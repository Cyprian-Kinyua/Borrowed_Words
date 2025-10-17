from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('books/books/', views.BookListView.as_view(), name='book-list'),
    path('books/books/<int:pk>/', views.BookDetailView.as_view(), name='book-detail'),
    path('books/books/my-books/', views.MyBooksListView.as_view(), name='my-books'),
]
