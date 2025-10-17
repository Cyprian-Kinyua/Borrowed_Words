from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import generics, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Book
from .serializers import BookSerializer
from .permissions import IsOwnerOrReadOnly


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
