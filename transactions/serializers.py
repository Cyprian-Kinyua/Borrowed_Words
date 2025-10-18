from rest_framework import serializers
from .models import BorrowTransaction
from books.serializers import BookSerializer
from entities.serializers import UserSerializer


class BorrowTransactionSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)
    borrower = UserSerializer(read_only=True)
    lender = UserSerializer(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    days_borrowed = serializers.SerializerMethodField()
    estimated_fee = serializers.SerializerMethodField()

    class Meta:
        model = BorrowTransaction
        fields = [
            'id', 'book', 'borrower', 'lender', 'status', 'request_date',
            'accept_date', 'due_date', 'return_date', 'final_rental_fee',
            'is_overdue', 'days_borrowed', 'estimated_fee'
        ]
        read_only_fields = [
            'id', 'book', 'borrower', 'lender', 'request_date', 'accept_date',
            'due_date', 'return_date', 'final_rental_fee', 'is_overdue',
            'days_borrowed', 'estimated_fee'
        ]

    def get_days_borrowed(self, obj):
        """Calculate days borrowed or currently borrowing"""
        if obj.accept_date:
            end_date = obj.return_date or timezone.now()
            days = (end_date - obj.accept_date).days
            return max(1, days)  # Minimum 1 day
        return 0

    def get_estimated_fee(self, obj):
        """Calculate estimated or final rental fee"""
        if obj.final_rental_fee:
            return obj.final_rental_fee
        elif obj.accept_date:
            days = self.get_days_borrowed(obj)
            return days * obj.book.daily_rental_price
        return 0


class BorrowTransactionCreateSerializer(serializers.ModelSerializer):
    book_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = BorrowTransaction
        fields = ['book_id']

    def validate_book_id(self, value):
        """Validate that the book exists and is available"""
        from books.models import Book

        try:
            book = Book.objects.get(id=value)
        except Book.DoesNotExist:
            raise serializers.ValidationError("Book does not exist.")

        # Check if book is available
        if not book.is_available:
            raise serializers.ValidationError(
                "This book is not available for borrowing.")

        # Check if user is trying to borrow their own book
        if self.context['request'].user == book.owner:
            raise serializers.ValidationError(
                "You cannot borrow your own book.")

        return value

    def create(self, validated_data):
        from books.models import Book

        book_id = validated_data.pop('book_id')
        book = Book.objects.get(id=book_id)

        # Create the transaction
        transaction = BorrowTransaction.objects.create(
            book=book,
            borrower=self.context['request'].user,
            lender=book.owner,
            status='PENDING'
        )

        return transaction
