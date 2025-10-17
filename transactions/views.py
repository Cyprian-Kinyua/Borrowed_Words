from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Q
from .models import BorrowTransaction
from .serializers import BorrowTransactionSerializer, BorrowTransactionCreateSerializer
from .permissions import IsTransactionParticipant, IsLender, IsBorrower


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
