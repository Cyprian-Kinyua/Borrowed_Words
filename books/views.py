from pyexpat.errors import messages
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import generics, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Book
from .serializers import BookSerializer
from .permissions import IsOwnerOrReadOnly
import django_filters
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from utils.api_client import APIClient


def home_view(request):
    # Homepage view
    api_client = APIClient(request.session)

    try:
        books = api_client.get('/books/books/?ordering=-created_at&limit=8')
    except:
        books = []

    context = {
        'recent_books': books,
        'user': request.session.get('user')
    }
    return render(request, 'home.html', context)


@login_required
def book_list_view(request):
    # Browse all books
    api_client = APIClient(request.session)

    # Get query parameters for filtering
    search = request.GET.get('search', '')
    genre = request.GET.get('genre', '')

    endpoint = '/books/books/'
    params = []
    if search:
        params.append(f'search={search}')
    if genre:
        params.append(f'genre={genre}')

    if params:
        endpoint += '?' + '&'.join(params)

    try:
        books = api_client.get(endpoint)
    except Exception as e:
        books = []
        messages.error(request, 'Error loading books')

    context = {
        'books': books,
        'search_query': search,
        'selected_genre': genre
    }
    return render(request, 'books/books/book_list.html', context)


@login_required
def book_detail_view(request, book_id):
    # Book detail page
    api_client = APIClient(request.session)

    try:
        book = api_client.get(f'/books/books/{book_id}/')

        # Check if user can borrow this book
        can_borrow = (
            request.session.get('user', {}).get('id') != book['owner']['id'] and
            book['is_available']
        )

    except Exception as e:
        messages.error(request, 'Book not found')
        return redirect('book_list')

    context = {
        'book': book,
        'can_borrow': can_borrow
    }
    return render(request, 'books/books/book_detail.html', context)


class BookFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(
        field_name="daily_rental_price", lookup_expr='gte')
    max_price = django_filters.NumberFilter(
        field_name="daily_rental_price", lookup_expr='lte')
    author = django_filters.CharFilter(
        field_name="author", lookup_expr='icontains')

    class Meta:
        model = Book
        fields = ['genre', 'condition', 'is_available']


class BookListView(generics.ListCreateAPIView):
    serializer_class = BookSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'author', 'description']
    filterset_fields = ['genre', 'condition', 'is_available']
    ordering_fields = ['created_at', 'daily_rental_price', 'title']
    ordering = ['-created_at']  # Default ordering: newest first

    def get_queryset(self):
        queryset = Book.objects.all()

        # Location-based filtering (simple implementation)
        user_location = self.request.query_params.get('location', None)
        if user_location:
            queryset = queryset.filter(location__icontains=user_location)

        # Only show available books to non-owners
        if not self.request.user.is_authenticated:
            return queryset.filter(is_available=True)

        # Show all books to authenticated users, but we'll handle availability in frontend
        return queryset

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class BookDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]


class MyBooksListView(generics.ListAPIView):
    serializer_class = BookSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Book.objects.filter(owner=self.request.user)


@api_view(['GET'])
@permission_classes([AllowAny])
def home(request):
    return Response({
        'message': 'Welcome to BorrowedWords API!',
        'endpoints': {
            'auth': '/api/auth/',
            'register': '/api/auth/register/',
            'login': '/api/auth/login/'
        }
    })
