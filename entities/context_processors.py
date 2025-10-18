def auth_context(request):
    """Add authentication context to all templates"""
    return {
        'user': request.session.get('user', None)
    }
