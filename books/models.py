from django.db import models
from django.conf import settings


class Book(models.Model):
    # Genre choices
    GENRE_CHOICES = [
        ('FICTION', 'Fiction'),
        ('SCI_FI', 'Science Fiction'),
        ('MYSTERY', 'Mystery'),
        ('THRILLER', 'Thriller'),
        ('ROMANCE', 'Romance'),
        ('FANTASY', 'Fantasy'),
        ('HORROR', 'Horror'),
        ('HISTORICAL', 'Historical Fiction'),
        ('BIOGRAPHY', 'Biography'),
        ('SELF_HELP', 'Self Help'),
        ('BUSINESS', 'Business'),
        ('SCIENCE', 'Science'),
        ('TECHNOLOGY', 'Technology'),
        ('ART', 'Art'),
        ('COOKING', 'Cooking'),
        ('TRAVEL', 'Travel'),
        ('OTHER', 'Other'),
    ]

    # Condition choices
    CONDITION_CHOICES = [
        ('NEW', 'New'),
        ('LIKE_NEW', 'Like New'),
        ('GOOD', 'Good'),
        ('FAIR', 'Fair'),
        ('POOR', 'Poor'),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='books'
    )
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    isbn = models.CharField(max_length=13, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    genre = models.CharField(
        max_length=20, choices=GENRE_CHOICES, default='FICTION')
    condition = models.CharField(
        max_length=10, choices=CONDITION_CHOICES, default='GOOD')
    daily_rental_price = models.DecimalField(
        max_digits=6, decimal_places=2, default=0.50)
    cover_image = models.ImageField(
        upload_to='book_covers/',
        blank=True,
        null=True,
        default='book_covers/default_cover.jpg'
    )
    is_available = models.BooleanField(default=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} by {self.author}"

    def save(self, *args, **kwargs):
        # Auto-populate location from owner if not set
        if not self.location and self.owner.location:
            self.location = self.owner.location
        super().save(*args, **kwargs)

    @property
    def has_pending_requests(self):
        """Check if this book has any pending borrow requests"""
        return self.transactions.filter(status='PENDING').exists()

    def get_pending_requests_count(self):
        """Get count of pending borrow requests"""
        return self.transactions.filter(status='PENDING').count()
