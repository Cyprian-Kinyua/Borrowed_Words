from django.contrib import admin
from .models import Book


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'owner',
                    'is_available', 'daily_rental_price']
    list_filter = ['genre', 'condition', 'is_available']
    search_fields = ['title', 'author', 'owner__username']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('owner')
