from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserRegistrationSerializer, UserLoginSerializer, UserSerializer
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
import requests
import json


def register_view(request):
    if request.method == 'POST':
        try:
            response = requests.post(
                f'{get_base_url(request)}/api/auth/register/',
                json={
                    'username': request.POST['username'],
                    'email': request.POST['email'],
                    'password': request.POST['password'],
                    'location': request.POST.get('location', '')
                }
            )

            if response.status_code == 201:
                messages.success(
                    request, 'Registration successful! Please login.')
                return redirect('login')
            else:
                errors = response.json()
                for field, error_list in errors.items():
                    if isinstance(error_list, list):
                        messages.error(
                            request, f"{field}: {', '.join(error_list)}")
                    else:
                        messages.error(request, f"{field}: {error_list}")

        except Exception as e:
            messages.error(request, f'Registration failed: {str(e)}')

    return render(request, 'entities/register.html')


def login_view(request):
    if request.method == 'POST':
        try:
            response = requests.post(
                f'{get_base_url(request)}/api/auth/login/',
                json={
                    'username': request.POST['username'],
                    'password': request.POST['password']
                }
            )

            if response.status_code == 200:
                data = response.json()
                # Store tokens and user data in session
                request.session['access_token'] = data['access']
                request.session['refresh_token'] = data['refresh']
                request.session['user'] = data['user']
                request.session.modified = True

                messages.success(
                    request, f"Welcome back, {data['user']['username']}!")
                return redirect('dashboard')
            else:
                error_data = response.json()
                messages.error(request, error_data.get(
                    'detail', 'Invalid credentials'))

        except Exception as e:
            messages.error(request, f'Login failed: {str(e)}')

    return render(request, 'entities/login.html')


def logout_view(request):
    if 'access_token' in request.session:
        try:
            # Call logout API
            requests.post(
                f'{get_base_url(request)}/api/auth/logout/',
                headers={
                    'Authorization': f"Bearer {request.session['access_token']}"}
            )
        except:
            pass  # Even if API call fails, clear session

    # Clear session
    request.session.flush()
    messages.success(request, 'Logged out successfully')
    return redirect('landing_page')


def get_base_url(request):
    """Get the base URL for API calls"""
    if request.is_secure():
        return f'https://{request.get_host()}'
    else:
        return f'http://{request.get_host()}'


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()

        # Generate JWT token for the new user
        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']

        # Generate JWT token for the authenticated user
        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_user(request):
    # With JWT, logout is typically handled on the client side by deleting the token.
    # However, you can implement token blacklisting if needed.
    return Response({'message': 'Successfully logged out.'})
