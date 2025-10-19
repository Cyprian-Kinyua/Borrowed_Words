import requests
from django.conf import settings
from django.contrib import messages


class APIClient:
    def __init__(self, request):
        self.request = request
        self.base_url = self.get_base_url()

    def get_base_url(self):
        """Get the base URL for API calls"""
        try:
            if hasattr(settings, 'ON_PYTHONANYWHERE') and settings.ON_PYTHONANYWHERE:
                return 'https://milagro.pythonanywhere.com'
            elif hasattr(self.request, 'is_secure') and hasattr(self.request, 'get_host'):
                if self.request.is_secure():
                    return f'https://{self.request.get_host()}'
                else:
                    return f'http://{self.request.get_host()}'
            else:
                return 'http://localhost:8000'
        except:
            return 'http://localhost:8000'

    def refresh_token(self):
        """Refresh the access token using refresh token"""
        try:
            refresh_token = self.request.session.get('refresh_token')
            if not refresh_token:
                print("DEBUG - No refresh token available")
                return False

            print("DEBUG - Attempting token refresh...")
            response = requests.post(
                f'{self.base_url}/api/auth/token/refresh/',
                json={'refresh': refresh_token}
            )

            if response.status_code == 200:
                data = response.json()
                self.request.session['access_token'] = data['access']
                self.request.session.modified = True
                print("DEBUG - Token refreshed successfully")
                return True
            else:
                print(
                    f"DEBUG - Token refresh failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"DEBUG - Token refresh error: {e}")
            return False

    def get_headers(self):
        """Get headers with proper authentication"""
        headers = {'Content-Type': 'application/json'}

        # Get token from session
        if hasattr(self.request, 'session') and self.request.session.get('user'):
            access_token = self.request.session.get('access_token')
            if access_token:
                headers['Authorization'] = f"Bearer {access_token}"
                print(f"DEBUG - Authorization header set with token")
            else:
                print("DEBUG - No access token in session")
        else:
            print("DEBUG - No User in session (public request))")

        return headers

    def handle_authentication_error(self, response):
        """Handle authentication errors and attempt token refresh"""
        if response.status_code == 401:
            print("DEBUG - Authentication error detected")
            if 'token_not_valid' in response.text or 'expired' in response.text.lower():
                print("DEBUG - Token appears to be expired, attempting refresh...")
                if self.refresh_token():
                    return True  # Token was refreshed
                else:
                    print("DEBUG - Token refresh failed, clearing session")
                    # Clear invalid session
                    if hasattr(self.request, 'session'):
                        self.request.session.flush()
            else:
                print("DEBUG - Other authentication error")
        return False

    def make_authenticated_request(self, method, endpoint, data=None, max_retries=1):
        """Make an authenticated request with automatic token refresh"""
        for attempt in range(max_retries + 1):
            try:
                headers = self.get_headers()
                full_url = f"{self.base_url}/api{endpoint}"

                print(f"DEBUG - Attempt {attempt + 1}: {method} {full_url}")

                if method.upper() == 'GET':
                    response = requests.get(full_url, headers=headers)
                elif method.upper() == 'POST':
                    response = requests.post(
                        full_url, json=data, headers=headers)
                elif method.upper() == 'PUT':
                    response = requests.put(
                        full_url, json=data, headers=headers)
                elif method.upper() == 'DELETE':
                    response = requests.delete(full_url, headers=headers)
                else:
                    return {'error': f'Unsupported method: {method}'}

                print(f"DEBUG - Response status: {response.status_code}")

                # If authentication error and we haven't retried yet, try refreshing token
                if response.status_code == 401 and attempt < max_retries:
                    if self.handle_authentication_error(response):
                        continue  # Retry with new token

                return self._handle_response(response)

            except Exception as e:
                print(f"DEBUG - Request exception: {e}")
                return {'error': str(e)}

        return {'error': 'Authentication failed after retry'}

    def get(self, endpoint):
        """Make GET request - works for both authenticated and public endpoints"""
        try:
            full_url = f"{self.base_url}/api{endpoint}"
            if settings.DEBUG:
                print(f"DEBUG - API GET: {full_url}")

            response = requests.get(full_url, headers=self.get_headers())

            if settings.DEBUG:
                print(f"DEBUG - Response status: {response.status_code}")

            return self._handle_response(response)
        except Exception as e:
            if settings.DEBUG:
                print(f"DEBUG - API GET Exception: {e}")
            return {'error': str(e)}

    def post(self, endpoint, data=None):
        return self.make_authenticated_request('POST', endpoint, data)

    def put(self, endpoint, data=None):
        return self.make_authenticated_request('PUT', endpoint, data)

    def delete(self, endpoint):
        return self.make_authenticated_request('DELETE', endpoint)

    def _handle_response(self, response):
        if response.status_code in [200, 201]:
            try:
                return response.json()
            except:
                return {'text': response.text}
        elif response.status_code == 204:
            return None
        else:
            try:
                error_data = response.json()
                return error_data
            except:
                return {
                    'error': f"HTTP {response.status_code}",
                    'detail': response.text[:200] if response.text else 'No error details'
                }


def get_base_url(request):
    """Get the base URL for API calls - standalone version"""
    try:
        if request.is_secure():
            return f'https://{request.get_host()}'
        else:
            return f'http://{request.get_host()}'
    except:
        return 'http://localhost:8000'
