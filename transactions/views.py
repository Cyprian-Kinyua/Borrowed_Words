from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Q
from .models import BorrowTransaction
from .serializers import BorrowTransactionSerializer, BorrowTransactionCreateSerializer
from .permissions import IsTransactionParticipant, IsLender, IsBorrower
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from books.models import Book
from books.serializers import BookSerializer


class TransactionListView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return BorrowTransactionCreateSerializer
        return BorrowTransactionSerializer

    def get_queryset(self):
        user = self.request.user

        # Filter by transaction type if provided
        transaction_type = self.request.query_params.get('type', None)

        queryset = BorrowTransaction.objects.filter(
            Q(borrower=user) | Q(lender=user)
        ).select_related('book', 'borrower', 'lender')

        if transaction_type == 'outgoing':
            queryset = queryset.filter(borrower=user)
        elif transaction_type == 'incoming':
            queryset = queryset.filter(lender=user)

        return queryset


class TransactionDetailView(generics.RetrieveAPIView):
    queryset = BorrowTransaction.objects.all()
    serializer_class = BorrowTransactionSerializer
    permission_classes = [
        permissions.IsAuthenticated, IsTransactionParticipant]


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsLender])
def accept_request(request, transaction_id):
    try:
        transaction = BorrowTransaction.objects.get(id=transaction_id)
    except BorrowTransaction.DoesNotExist:
        return Response(
            {'error': 'Transaction not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Check if transaction is in pending state
    if transaction.status != 'PENDING':
        return Response(
            {'error': 'This request has already been processed'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Update transaction status
    transaction.status = 'ACCEPTED'
    transaction.save()

    # Mark book as unavailable
    transaction.book.is_available = False
    transaction.book.save()

    serializer = BorrowTransactionSerializer(transaction)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsLender])
def reject_request(request, transaction_id):
    try:
        transaction = BorrowTransaction.objects.get(id=transaction_id)
    except BorrowTransaction.DoesNotExist:
        return Response(
            {'error': 'Transaction not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    if transaction.status != 'PENDING':
        return Response(
            {'error': 'This request has already been processed'},
            status=status.HTTP_400_BAD_REQUEST
        )

    transaction.status = 'REJECTED'
    transaction.save()

    serializer = BorrowTransactionSerializer(transaction)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsBorrower])
def mark_returned(request, transaction_id):
    """
    Borrower marks the book as returned
    """
    try:
        transaction = BorrowTransaction.objects.get(id=transaction_id)
    except BorrowTransaction.DoesNotExist:
        return Response(
            {'error': 'Transaction not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Check if transaction is in borrowed state
    if transaction.status != 'ACCEPTED':
        return Response(
            {'error': 'Can only mark returned books that are currently borrowed'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Update transaction status and return date
    transaction.status = 'RETURNED'
    transaction.return_date = timezone.now()
    transaction.save()

    # Send notification to lender (stretch goal)
    try:
        send_return_notification(transaction)
    except Exception as e:
        # Don't fail if email doesn't send
        print(f"Email notification failed: {e}")

    serializer = BorrowTransactionSerializer(transaction)
    return Response({
        'message': 'Book marked as returned. Waiting for lender confirmation.',
        'transaction': serializer.data
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsLender])
def confirm_return(request, transaction_id):
    """
    Lender confirms the return and completes the transaction
    """
    try:
        transaction = BorrowTransaction.objects.get(id=transaction_id)
    except BorrowTransaction.DoesNotExist:
        return Response(
            {'error': 'Transaction not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Check if transaction is in returned state
    if transaction.status != 'RETURNED':
        return Response(
            {'error': 'Can only confirm return for books marked as returned'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Update transaction status to completed
    transaction.status = 'COMPLETED'
    transaction.save()

    # Mark book as available again
    transaction.book.is_available = True
    transaction.book.save()

    # Calculate and save final rental fee
    transaction.final_rental_fee = transaction.calculate_rental_fee()
    transaction.save()

    serializer = BorrowTransactionSerializer(transaction)
    return Response({
        'message': 'Return confirmed. Book is now available for borrowing again.',
        'transaction': serializer.data,
        'rental_fee': transaction.final_rental_fee
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsBorrower])
def cancel_request(request, transaction_id):
    """
    Borrower cancels their own pending request
    """
    try:
        transaction = BorrowTransaction.objects.get(id=transaction_id)
    except BorrowTransaction.DoesNotExist:
        return Response(
            {'error': 'Transaction not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    if transaction.status != 'PENDING':
        return Response(
            {'error': 'Can only cancel pending requests'},
            status=status.HTTP_400_BAD_REQUEST
        )

    transaction.status = 'CANCELLED'
    transaction.save()

    serializer = BorrowTransactionSerializer(transaction)
    return Response({
        'message': 'Borrow request cancelled.',
        'transaction': serializer.data
    })


def send_return_notification(transaction):
    """
    Send email notification to lender when book is returned
    """
    subject = f'Book Returned: {transaction.book.title}'
    message = f'''
    Hello {transaction.lender.username},
    
    The borrower {transaction.borrower.username} has marked the book 
    "{transaction.book.title}" as returned.
    
    Please confirm the return to complete the transaction and make the 
    book available for borrowing again.
    
    Thank you for using BorrowedWords!
    '''

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [transaction.lender.email],
        fail_silently=True,
    )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def transaction_stats(request):
    """
    Get statistics for the current user's transactions
    """
    user = request.user

    stats = {
        'total_borrowed': BorrowTransaction.objects.filter(borrower=user, status='COMPLETED').count(),
        'total_lent': BorrowTransaction.objects.filter(lender=user, status='COMPLETED').count(),
        'pending_requests': BorrowTransaction.objects.filter(lender=user, status='PENDING').count(),
        'active_borrowings': BorrowTransaction.objects.filter(borrower=user, status='ACCEPTED').count(),
        'overdue_books': BorrowTransaction.objects.filter(
            borrower=user,
            status='ACCEPTED',
            due_date__lt=timezone.now().date()
        ).count(),
    }

    return Response(stats)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_dashboard(request):
    """
    Get dashboard data for the current user
    """
    user = request.user

    # Recent transactions
    recent_transactions = BorrowTransaction.objects.filter(
        Q(borrower=user) | Q(lender=user)
    ).select_related('book', 'borrower', 'lender')[:5]

    # User's books with pending requests
    books_with_requests = Book.objects.filter(
        owner=user,
        transactions__status='PENDING'
    ).distinct()

    dashboard_data = {
        'recent_transactions': BorrowTransactionSerializer(recent_transactions, many=True).data,
        'books_with_pending_requests': BookSerializer(books_with_requests, many=True).data,
        'stats': {
            'books_listed': Book.objects.filter(owner=user).count(),
            'active_borrowings': BorrowTransaction.objects.filter(borrower=user, status='ACCEPTED').count(),
            'pending_decisions': BorrowTransaction.objects.filter(lender=user, status='PENDING').count(),
        }
    }

    return Response(dashboard_data)
