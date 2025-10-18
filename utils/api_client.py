import requests
from django.conf import settings


class APIClient:
    def __init__(self, request):
        self.request = request
        self.base_url = get_base_url(request)

    def get_headers(self):
        headers = {'Content-Type': 'application/json'}
        if 'access_token' in self.request.session:
            headers['Authorization'] = f"Bearer {self.request.session['access_token']}"
        return headers

    def get(self, endpoint):
        response = requests.get(
            f"{self.base_url}/api{endpoint}", headers=self.get_headers())
        return self._handle_response(response)

    def post(self, endpoint, data=None):
        response = requests.post(
            f"{self.base_url}/api{endpoint}", json=data, headers=self.get_headers())
        return self._handle_response(response)

    def put(self, endpoint, data=None):
        response = requests.put(
            f"{self.base_url}/api{endpoint}", json=data, headers=self.get_headers())
        return self._handle_response(response)

    def delete(self, endpoint):
        response = requests.delete(
            f"{self.base_url}/api{endpoint}", headers=self.get_headers())
        return self._handle_response(response)

    def _handle_response(self, response):
        if response.status_code in [200, 201]:
            return response.json()
        elif response.status_code == 204:
            return None
        else:
            # Return the error response instead of raising exception
            try:
                return response.json()
            except:
                return {'error': f"HTTP {response.status_code}"}


def get_base_url(request):
    """Get the base URL for API calls"""
    if request.is_secure():
        return f'https://{request.get_host()}'
    else:
        return f'http://{request.get_host()}'
