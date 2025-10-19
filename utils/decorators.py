from django.shortcuts import redirect
from django.contrib import messages


def jwt_login_required(view_func):
    """Custom login required decorator that checks for JWT token in session"""
    def wrapper(request, *args, **kwargs):
        if 'access_token' in request.session and 'user' in request.session:
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, 'Please log in to access this page.')
            return redirect('login')
    return wrapper
