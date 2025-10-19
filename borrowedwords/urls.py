from django.urls import path, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView

# Import all your template views
from books.views import (
    home_view, book_list_view, book_detail_view,
    dashboard_view, my_books_view, add_book_view,
    transaction_list_view, edit_book_view, borrow_book_view
)
from transactions.views import (
    accept_request, reject_request, mark_returned, confirm_return, cancel_request
)
from entities.views import register_view, login_view, logout_view

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Template views (frontend)
    path('', home_view, name='landing_page'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('books/', book_list_view, name='book_list'),
    path('books/<int:book_id>/', book_detail_view, name='book_detail'),
    path('my-books/', my_books_view, name='my_books'),
    path('books/add/', add_book_view, name='add_book'),
    path('books/edit/<int:book_id>/', edit_book_view, name='edit_book'),
    path('books/<int:book_id>/borrow/', borrow_book_view, name='borrow_book'),
    path('transactions/', transaction_list_view, name='transaction_list'),

    # Transaction template views (frontend)
    path('transactions/', transaction_list_view, name='transaction_list'),
    path('transactions/<int:transaction_id>/accept/',
         accept_request, name='accept_request'),
    path('transactions/<int:transaction_id>/reject/',
         reject_request, name='reject_request'),
    path('transactions/<int:transaction_id>/mark-returned/',
         mark_returned, name='mark_returned'),
    path('transactions/<int:transaction_id>/confirm-return/',
         confirm_return, name='confirm_return'),
    path('transactions/<int:transaction_id>/cancel/',
         cancel_request, name='cancel_request'),

    # API URLs (backend - for AJAX calls)
    path('api/auth/', include('entities.urls')),
    path('api/books/', include('books.urls')),
    path('api/transactions/', include('transactions.urls')),
    path('api/auth/token/refresh/',
         TokenRefreshView.as_view(), name='token_refresh'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
