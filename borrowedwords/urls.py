"""
URL configuration for borrowedwords project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from books.views import home_view, book_list_view, book_detail_view, dashboard_view, my_books_view, add_book_view, transaction_list_view
from entities.views import register_view, login_view, logout_view
from rest_framework_simplejwt.views import TokenRefreshView
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),

    # Template views
    path('', home_view, name='home'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('books/', book_list_view, name='book_list'),
    path('books/<int:book_id>/', book_detail_view, name='book_detail'),
    path('books/my-books/', my_books_view, name='my_books'),
    path('books/add/', add_book_view, name='add_book'),
    path('transactions/', transaction_list_view, name='transaction_list'),

    # API endpoints
    path('api/auth/', include('entities.urls')),
    path('api/', include('books.urls')),
    path('api/', include('transactions.urls')),

    # JWT token refresh endpoint
    path('api/auth/token/refresh/',
         TokenRefreshView.as_view(), name='token_refresh'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
