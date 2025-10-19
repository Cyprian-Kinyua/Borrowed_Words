from django.contrib import messages
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
from utils.api_client import APIClient
from utils.decorators import jwt_login_required


def home_view(request):
    """Homepage view"""
    api_client = APIClient(request)
    recent_books = []

    try:
        # Get recent books for the homepage
        books_data = api_client.get('/books/?ordering=-created_at&limit=8')
        print(f"DEBUG - Home API Response: {books_data}")

        # Ensure we have a list and filter out any invalid books
        if isinstance(books_data, list):
            recent_books = [book for book in books_data if book.get('id')]
        elif isinstance(books_data, dict) and 'detail' in books_data:
            # API returned an error, likely authentication required
            print(
                f"DEBUG - API Error (will use empty books): {books_data['detail']}")
            recent_books = []
        else:
            recent_books = []

    except Exception as e:
        print(f"Error loading books: {e}")  # For debugging
        recent_books = []

    context = {
        'recent_books': recent_books,
        'user': request.session.get('user')
    }
    return render(request, 'home.html', context)


@jwt_login_required
def dashboard_view(request):
    """User dashboard"""
    api_client = APIClient(request)

    try:
        dashboard_data = api_client.get('/dashboard/')
    except Exception as e:
        dashboard_data = {}
        messages.error(request, 'Error loading dashboard')

    context = {
        'dashboard_data': dashboard_data,
        'user': request.session.get('user', {})
    }
    return render(request, 'dashboard.html', context)


@jwt_login_required
def my_books_view(request):
    """User's own books"""
    api_client = APIClient(request)

    try:
        my_books = api_client.get('/books/my-books/')
        print(f"DEBUG - My Books API Response: {my_books}")  # Debug line

        if isinstance(my_books, dict) and 'error' in my_books:
            print(f"DEBUG - API Error: {my_books['error']}")
            my_books = []
            messages.error(request, 'Error loading your books')
        elif not isinstance(my_books, list):
            print(f"DEBUG - Unexpected response type: {type(my_books)}")
            my_books = []
    except Exception as e:
        print(f"DEBUG - Exception: {e}")
        my_books = []
        messages.error(request, 'Error loading your books')

    # Filter out books without IDs
    valid_books = [book for book in my_books if book and book.get('id')]
    print(f"DEBUG - Valid books: {valid_books}")  # Debug line

    context = {
        'books': valid_books,
        'user': request.session.get('user', {})
    }
    return render(request, 'books/my_books.html', context)


@jwt_login_required
def add_book_view(request):
    """Add a new book"""
    if request.method == 'POST':
        api_client = APIClient(request)

        try:
            book_data = {
                'title': request.POST['title'],
                'author': request.POST['author'],
                'genre': request.POST['genre'],
                'condition': request.POST['condition'],
                'daily_rental_price': request.POST['daily_rental_price'],
                'description': request.POST.get('description', ''),
                'isbn': request.POST.get('isbn', ''),
            }

            print(f"DEBUG - Sending book data: {book_data}")

            response = api_client.post('/books/', book_data)
            print(f"DEBUG - API Response: {response}")

            if isinstance(response, dict) and 'error' in response:
                error_msg = response['error']
                messages.error(request, f'Error adding book: {error_msg}')
                print(f"DEBUG - API Error: {error_msg}")
            else:
                messages.success(request, 'Book added successfully!')
                return redirect('my_books')

        except Exception as e:
            error_msg = f'Error adding book: {str(e)}'
            messages.error(request, error_msg)
            print(f"DEBUG - Exception: {error_msg}")

    context = {
        'genres': ['FICTION', 'SCI_FI', 'MYSTERY', 'ROMANCE', 'FANTASY', 'HISTORICAL', 'BIOGRAPHY', 'OTHER'],
        'conditions': ['NEW', 'LIKE_NEW', 'GOOD', 'FAIR', 'POOR']
    }
    return render(request, 'books/add_book.html', context)


@jwt_login_required
def edit_book_view(request, book_id):
    """Edit an existing book"""
    api_client = APIClient(request)

    if request.method == 'POST':
        try:
            book_data = {
                'title': request.POST['title'],
                'author': request.POST['author'],
                'genre': request.POST['genre'],
                'condition': request.POST['condition'],
                'daily_rental_price': request.POST['daily_rental_price'],
                'description': request.POST.get('description', ''),
                'is_available': 'is_available' in request.POST,
            }

            print(f"DEBUG - Editing book {book_id} with data: {book_data}")

            response = api_client.put(f'/books/{book_id}/', book_data)

            if isinstance(response, dict) and 'error' in response:
                messages.error(
                    request, f'Error updating book: {response["error"]}')
            else:
                messages.success(request, 'Book updated successfully!')

        except Exception as e:
            messages.error(request, f'Error updating book: {str(e)}')

    return redirect('my_books')


@jwt_login_required
def transaction_list_view(request):
    """User's transactions with detailed debugging"""
    api_client = APIClient(request)

    # Debug session and user info
    user_data = request.session.get('user', {})
    print(f"DEBUG - Current User: {user_data}")
    print(f"DEBUG - User ID: {user_data.get('id')}")
    print(f"DEBUG - Username: {user_data.get('username')}")

    transaction_type = request.GET.get('type', '')
    endpoint = '/transactions/'
    if transaction_type:
        endpoint += f'?type={transaction_type}'

    try:
        transactions_data = api_client.get(endpoint)
        print(f"DEBUG - Raw Transactions API Response: {transactions_data}")
        print(f"DEBUG - Transactions Response Type: {type(transactions_data)}")

        # Handle different response types
        if isinstance(transactions_data, dict):
            if 'detail' in transactions_data:
                print(f"DEBUG - API Error: {transactions_data['detail']}")
                messages.error(
                    request, f'Error loading transactions: {transactions_data["detail"]}')
                transactions = []
            elif 'error' in transactions_data:
                print(
                    f"DEBUG - API General Error: {transactions_data['error']}")
                messages.error(request, f'Error: {transactions_data["error"]}')
                transactions = []
            else:
                print(f"DEBUG - Unexpected dictionary structure")
                transactions = []
        elif isinstance(transactions_data, list):
            transactions = transactions_data
            print(f"DEBUG - Found {len(transactions)} transactions")

            # Debug each transaction
            for i, transaction in enumerate(transactions):
                print(f"DEBUG - Transaction {i}:")
                print(f"  ID: {transaction.get('id')}")
                print(f"  Status: {transaction.get('status')}")
                print(f"  Book: {transaction.get('book', {}).get('title')}")
                print(
                    f"  Borrower: {transaction.get('borrower', {}).get('username')}")
                print(
                    f"  Lender: {transaction.get('lender', {}).get('username')}")
                print(f"  Request Date: {transaction.get('request_date')}")
        else:
            print(f"DEBUG - Unexpected response type")
            transactions = []
            messages.error(request, 'Unexpected response from server')

    except Exception as e:
        print(f"DEBUG - Transactions Exception: {str(e)}")
        import traceback
        print(f"DEBUG - Transactions Traceback: {traceback.format_exc()}")
        transactions = []
        messages.error(request, 'Error loading transactions')

    context = {
        'transactions': transactions if isinstance(transactions, list) else [],
        'transaction_type': transaction_type
    }
    return render(request, 'transactions/transaction_list.html', context)


@jwt_login_required
def book_list_view(request):
    api_client = APIClient(request)

    # Get query parameters for filtering
    search = request.GET.get('search', '')
    genre = request.GET.get('genre', '')

    endpoint = '/books/'
    params = []
    if search:
        params.append(f'search={search}')
    if genre:
        params.append(f'genre={genre}')

    if params:
        endpoint += '?' + '&'.join(params)

    print(f"DEBUG - Final API Endpoint: {endpoint}")

    try:
        books_data = api_client.get(endpoint)
        print(f"DEBUG - Raw API Response: {books_data}")

        # Check if we got an authentication error even after refresh
        if isinstance(books_data, dict) and 'detail' in books_data:
            if 'token_not_valid' in books_data.get('code', ''):
                messages.error(
                    request, 'Your session has expired. Please log in again.')
                return redirect('login')
            elif 'error' in books_data:
                messages.error(
                    request, f'Error loading books: {books_data["error"]}')
                books_data = []

        if isinstance(books_data, list):
            valid_books = [
                book for book in books_data if book and book.get('id')]
            print(f"DEBUG - Valid books count: {len(valid_books)}")
        else:
            valid_books = []
            messages.error(request, 'Error loading books')

    except Exception as e:
        print(f"DEBUG - Exception: {e}")
        valid_books = []
        messages.error(request, 'Error loading books')

    context = {
        'books': valid_books,
        'search_query': search,
        'selected_genre': genre
    }
    return render(request, 'books/book_list.html', context)


@jwt_login_required
def book_detail_view(request, book_id):
    """Book detail page with proper error handling"""
    api_client = APIClient(request)

    print(f"DEBUG - Book Detail - Book ID: {book_id}")

    try:
        book_data = api_client.get(f'/books/{book_id}/')
        print(f"DEBUG - Book Detail API Response: {book_data}")

        # Handle different response types
        if isinstance(book_data, dict):
            if 'detail' in book_data:
                # API returned an error
                error_msg = book_data['detail']
                print(f"DEBUG - Book Detail API Error: {error_msg}")
                messages.error(request, f'Book not found: {error_msg}')
                return redirect('book_list')
            elif 'id' in book_data:
                # Valid book data
                book = book_data
                print(f"DEBUG - Book data validated, ID: {book['id']}")
            else:
                # Unexpected dictionary structure
                print(f"DEBUG - Unexpected book data structure: {book_data}")
                messages.error(request, 'Unexpected book data format')
                return redirect('book_list')
        else:
            # Unexpected response type
            print(f"DEBUG - Unexpected book response type: {type(book_data)}")
            messages.error(request, 'Unable to load book details')
            return redirect('book_list')

        # Debug the book owner structure
        print(f"DEBUG - Book owner data: {book.get('owner')}")
        print(f"DEBUG - Book owner type: {type(book.get('owner'))}")

        # Check if user can borrow this book
        user_data = request.session.get('user', {})
        user_id = user_data.get('id')
        user_username = user_data.get('username')

        # Handle different owner data structures
        owner_data = book.get('owner', {})
        if isinstance(owner_data, dict):
            owner_id = owner_data.get('id')
            owner_username = owner_data.get('username')
        else:
            # Owner might be a string (username) or integer (ID)
            owner_id = owner_data
            owner_username = str(owner_data)

        book_available = book.get('is_available', False)

        print(f"DEBUG - User data from session: {user_data}")
        print(f"DEBUG - User ID: {user_id}")
        print(f"DEBUG - Owner ID: {owner_id}")
        print(f"DEBUG - Owner username: {owner_username}")
        print(f"DEBUG - Book available: {book_available}")

        is_own_book = (owner_username == user_username) or (
            owner_id == user_username)

        can_borrow = (
            user_id is not None and
            not is_own_book and
            book_available
        )

        print(f"DEBUG - Final can_borrow: {can_borrow}")

    except Exception as e:
        print(f"DEBUG - Book Detail Exception: {str(e)}")
        import traceback
        print(f"DEBUG - Book Detail Traceback: {traceback.format_exc()}")
        messages.error(request, 'Error loading book details')
        return redirect('book_list')

    context = {
        'book': book,
        'can_borrow': can_borrow,
        'owner_name': owner_username,
        'owner_id': owner_id
    }
    return render(request, 'books/book_detail.html', context)


@jwt_login_required
def borrow_book_view(request, book_id):
    """Handle book borrowing requests"""
    api_client = APIClient(request)

    print(f"DEBUG - Borrow attempt for book ID: {book_id}")

    try:
        # Create borrow request
        response = api_client.post('/transactions/', {'book_id': book_id})
        print(f"DEBUG - Borrow API Response: {response}")

        if isinstance(response, dict):
            messages.success(request, 'Borrow request sent successfully!')
        elif isinstance(response, dict) and 'error' in response:
            error_msg = response.get('error', 'Unknown error')
            messages.error(request, f'Failed to borrow book: {error_msg}')
        else:
            messages.error(request, 'Failed to send borrow request')

    except Exception as e:
        print(f"DEBUG - Borrow Exception: {e}")
        messages.error(request, 'Error sending borrow request')

    return redirect('book_detail', book_id=book_id)


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
