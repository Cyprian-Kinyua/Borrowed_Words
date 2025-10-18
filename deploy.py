#!/usr/bin/env python
import os
import sys
import django
from django.core.management import execute_from_command_line


def deploy():
    # Deployment commands
    print("Starting deployment...")

    # Collect static files
    print("Collecting static files...")
    execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])

    # Run migrations
    print("Running migrations...")
    execute_from_command_line(['manage.py', 'migrate'])

    print("Deployment completed!")


if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'borrowedwords.settings')
    django.setup()
    deploy()
