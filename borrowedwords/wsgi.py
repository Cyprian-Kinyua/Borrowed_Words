"""
WSGI config for borrowedwords project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

from django.core.wsgi import get_wsgi_application
import os
import sys

path = '/home/yourusername/borrowedwords'
if path not in sys.path:
    sys.path.append(path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'borrowedwords.settings')

application = get_wsgi_application()
