from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny


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
