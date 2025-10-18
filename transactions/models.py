from django.db import models
from django.conf import settings
from django.forms import ValidationError
from django.utils import timezone


class BorrowTransaction(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('BORROWED', 'Borrowed'),
        ('RETURNED', 'Returned'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    book = models.ForeignKey(
        'books.Book',
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    borrower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='borrowed_transactions'
    )
    lender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lent_transactions'
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    request_date = models.DateTimeField(auto_now_add=True)
    accept_date = models.DateTimeField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    return_date = models.DateTimeField(null=True, blank=True)
    final_rental_fee = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['-request_date']  # Newest transactions first

    def __str__(self):
        return f"{self.borrower.username} -> {self.book.title} ({self.status})"

    def calculate_rental_fee(self):
        """Calculate rental fee based on days borrowed"""
        if self.accept_date and self.return_date:
            # Calculate days between accept and return
            days_borrowed = (self.return_date - self.accept_date).days
            days_borrowed = max(1, days_borrowed)  # Minimum 1 day
            return days_borrowed * self.book.daily_rental_price
        return None

    @property
    def is_overdue(self):
        # Check if the book is overdue
        if self.due_date and self.status in ['ACCEPTED', 'BORROWED']:
            return timezone.now().date() > self.due_date
        return False

    def clean(self):
        # Additional validation for dates consistency
        if self.due_date and self.accept_date:
            if self.due_date <= self.accept_date.date():
                raise ValidationError('Due date must be after acceptance date')

        if self.return_date and self.accept_date:
            if self.return_date < self.accept_date:
                raise ValidationError(
                    'Return date cannot be before acceptance date')

    def save(self, *args, **kwargs):
        # Auto-calculate final rental fee when book is returned
        if self.status == 'RETURNED' and self.return_date:
            self.final_rental_fee = self.calculate_rental_fee()

        # Set due date to 14 days from acceptance if not set
        if self.status == 'ACCEPTED' and not self.due_date:
            self.due_date = timezone.now().date() + timezone.timedelta(days=14)

        self.clean()
        super().save(*args, **kwargs)
