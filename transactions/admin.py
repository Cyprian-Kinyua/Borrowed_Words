from django.contrib import admin
from .models import BorrowTransaction


@admin.register(BorrowTransaction)
class BorrowTransactionAdmin(admin.ModelAdmin):
    list_display = ['book', 'borrower', 'lender',
                    'status', 'request_date', 'due_date']
    list_filter = ['status', 'request_date']
    search_fields = ['book__title', 'borrower__username', 'lender__username']
    readonly_fields = ['request_date', 'accept_date', 'return_date']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('book', 'borrower', 'lender')
