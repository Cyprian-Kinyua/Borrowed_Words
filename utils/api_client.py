import requests
from django.conf import settings


class APIClient:
    def __init__(self, session):
        self.session = session
        self.base_url = 'http://localhost:8000/api'
        if not settings.DEBUG:
            self.base_url = f'https://{settings.ALLOWED_HOSTS[0]}/api'

    def get_headers(self):
        headers = {'Content-Type': 'application/json'}
        if 'access_token' in self.session:
            headers['Authorization'] = f"Bearer {self.session['access_token']}"
        return headers

    def get(self, endpoint):
        response = requests.get(
            f"{self.base_url}{endpoint}", headers=self.get_headers())
        return self._handle_response(response)

    def post(self, endpoint, data=None):
        response = requests.post(
            f"{self.base_url}{endpoint}", json=data, headers=self.get_headers())
        return self._handle_response(response)

    def put(self, endpoint, data=None):
        response = requests.put(
            f"{self.base_url}{endpoint}", json=data, headers=self.get_headers())
        return self._handle_response(response)

    def delete(self, endpoint):
        response = requests.delete(
            f"{self.base_url}{endpoint}", headers=self.get_headers())
        return self._handle_response(response)

    def _handle_response(self, response):
        if response.status_code in [200, 201]:
            return response.json()
        elif response.status_code == 204:
            return None
        else:
            raise Exception(
                f"API Error: {response.status_code} - {response.text}")
