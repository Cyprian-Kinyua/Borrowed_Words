# api/index.py
import os
from django.core.wsgi import get_wsgi_application

# Set the default Django settings module for your project
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "borrowedwords.settings")

# Get the WSGI application
app = get_wsgi_application()
