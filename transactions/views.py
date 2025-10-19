from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Q
from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from utils.api_client import APIClient
from utils.decorators import jwt_login_required
from .models import BorrowTransaction
from .serializers import BorrowTransactionSerializer, BorrowTransactionCreateSerializer
from .permissions import IsTransactionParticipant, IsLender, IsBorrower
from books.models import Book
from books.serializers import BookSerializer

# ===== API VIEWS (for DRF API endpoints) =====


class TransactionListView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return BorrowTransactionCreateSerializer
        return BorrowTransactionSerializer

    def get_queryset(self):
        user = self.request.user
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
def api_accept_request(request, transaction_id):
    """API endpoint for accepting requests"""
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

    transaction.status = 'ACCEPTED'
    transaction.save()

    transaction.book.is_available = False
    transaction.book.save()

    serializer = BorrowTransactionSerializer(transaction)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsLender])
def api_reject_request(request, transaction_id):
    """API endpoint for rejecting requests"""
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
def api_mark_returned(request, transaction_id):
    """API endpoint for marking books as returned"""
    try:
        transaction = BorrowTransaction.objects.get(id=transaction_id)
    except BorrowTransaction.DoesNotExist:
        return Response(
            {'error': 'Transaction not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    if transaction.status != 'ACCEPTED':
        return Response(
            {'error': 'Can only mark returned books that are currently borrowed'},
            status=status.HTTP_400_BAD_REQUEST
        )

    transaction.status = 'RETURNED'
    transaction.return_date = timezone.now()
    transaction.save()

    try:
        send_return_notification(transaction)
    except Exception as e:
        print(f"Email notification failed: {e}")

    serializer = BorrowTransactionSerializer(transaction)
    return Response({
        'message': 'Book marked as returned. Waiting for lender confirmation.',
        'transaction': serializer.data
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsLender])
def api_confirm_return(request, transaction_id):
    """API endpoint for confirming returns"""
    try:
        transaction = BorrowTransaction.objects.get(id=transaction_id)
    except BorrowTransaction.DoesNotExist:
        return Response(
            {'error': 'Transaction not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    if transaction.status != 'RETURNED':
        return Response(
            {'error': 'Can only confirm return for books marked as returned'},
            status=status.HTTP_400_BAD_REQUEST
        )

    transaction.status = 'COMPLETED'
    transaction.save()

    transaction.book.is_available = True
    transaction.book.save()

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
def api_cancel_request(request, transaction_id):
    """API endpoint for canceling requests"""
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

# ===== TEMPLATE VIEWS (for frontend HTML pages) =====


@jwt_login_required
def accept_request(request, transaction_id):
    """Template view for accepting requests"""
    try:
        api_client = APIClient(request)
        response = api_client.post(f'/transactions/{transaction_id}/accept/')
        print(f"DEBUG - Accept response: {response}")

        if isinstance(response, dict):
            if 'id' in response:
                messages.success(
                    request, '✅ Borrow request accepted! The book is now on loan.')
            elif 'detail' in response:
                messages.error(request, f'❌ {response["detail"]}')
            elif 'error' in response:
                messages.error(request, f'❌ {response["error"]}')
            else:
                messages.error(request, '❌ Failed to accept request')
        else:
            messages.error(request, '❌ Unexpected response from server')

    except Exception as e:
        print(f"DEBUG - Accept error: {e}")
        messages.error(request, '❌ Error accepting request')

    return redirect('transaction_list')


@jwt_login_required
def reject_request(request, transaction_id):
    """Template view for rejecting requests"""
    try:
        api_client = APIClient(request)
        response = api_client.post(f'/transactions/{transaction_id}/reject/')
        print(f"DEBUG - Reject response: {response}")

        if isinstance(response, dict):
            if 'id' in response:
                messages.success(request, '✅ Borrow request rejected.')
            elif 'detail' in response:
                messages.error(request, f'❌ {response["detail"]}')
            elif 'error' in response:
                messages.error(request, f'❌ {response["error"]}')
            else:
                messages.error(request, '❌ Failed to reject request')
        else:
            messages.error(request, '❌ Unexpected response from server')

    except Exception as e:
        print(f"DEBUG - Reject error: {e}")
        messages.error(request, '❌ Error rejecting request')

    return redirect('transaction_list')


@jwt_login_required
def mark_returned(request, transaction_id):
    """Template view for marking books returned"""
    try:
        api_client = APIClient(request)
        response = api_client.post(
            f'/transactions/{transaction_id}/mark-returned/')
        print(f"DEBUG - Mark returned response: {response}")

        if isinstance(response, dict):
            # if 'id' in response:
            messages.success(
                request, '✅ Book marked as returned! Waiting for owner confirmation.')
            # elif 'detail' in response:
            #     messages.error(request, f'❌ {response["detail"]}')
            # elif 'error' in response:
            #     messages.error(request, f'❌ {response["error"]}')
            # else:
            #     messages.error(request, '❌ Failed to mark as returned')
        else:
            messages.error(request, '❌ Unexpected response from server')

    except Exception as e:
        print(f"DEBUG - Mark returned error: {e}")
        messages.error(request, '❌ Error marking book as returned')

    return redirect('transaction_list')


@jwt_login_required
def confirm_return(request, transaction_id):
    """Template view for confirming returns"""
    try:
        api_client = APIClient(request)
        response = api_client.post(
            f'/transactions/{transaction_id}/confirm-return/')
        print(f"DEBUG - Confirm return response: {response}")

        if isinstance(response, dict):
            # if 'id' in response:
            messages.success(
                request, '✅ Return confirmed! Transaction completed.')
            # elif 'detail' in response:
            #     messages.error(request, f'❌ {response["detail"]}')
            # elif 'error' in response:
            #     messages.error(request, f'❌ {response["error"]}')
            # else:
            #     messages.error(request, '❌ Failed to confirm return')
        else:
            messages.error(request, '❌ Unexpected response from server')

    except Exception as e:
        print(f"DEBUG - Confirm return error: {e}")
        messages.error(request, '❌ Error confirming return')

    return redirect('transaction_list')


@jwt_login_required
def cancel_request(request, transaction_id):
    """Template view for canceling requests"""
    try:
        api_client = APIClient(request)
        response = api_client.post(f'/transactions/{transaction_id}/cancel/')
        print(f"DEBUG - Cancel response: {response}")

        if isinstance(response, dict):
            # if 'id' in response:
            messages.success(request, '✅ Borrow request cancelled.')
            # elif 'detail' in response:
            #     messages.error(request, f'❌ {response["detail"]}')
            # elif 'error' in response:
            #     messages.error(request, f'❌ {response["error"]}')
            # else:
            #     messages.error(request, '❌ Failed to cancel request')
        else:
            messages.error(request, '❌ Unexpected response from server')

    except Exception as e:
        print(f"DEBUG - Cancel error: {e}")
        messages.error(request, '❌ Error cancelling request')

    return redirect('transaction_list')

# ===== HELPER FUNCTIONS =====


def send_return_notification(transaction):
    """Send email notification to lender"""
    subject = f'Book Returned: {transaction.book.title}'
    message = f'''
    Hello {transaction.lender.username},
    
    The borrower {transaction.borrower.username} has marked the book 
    "{transaction.book.title}" as returned.
    
    Please confirm the return to complete the transaction.
    
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
    """Get transaction statistics"""
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
    """Get user dashboard data"""
    user = request.user

    recent_transactions = BorrowTransaction.objects.filter(
        Q(borrower=user) | Q(lender=user)
    ).select_related('book', 'borrower', 'lender')[:5]

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
