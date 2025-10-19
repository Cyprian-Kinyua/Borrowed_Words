# books/urls.py - This should be for API endpoints only
from django.urls import path
from . import views

urlpatterns = [
    path('', views.BookListView.as_view(), name='api-book-list'),
    path('<int:pk>/', views.BookDetailView.as_view(), name='api-book-detail'),
    path('my-books/', views.MyBooksListView.as_view(), name='api-my-books'),
]
