"""WSGI config for zero project."""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "zero.settings")

application = get_wsgi_application()
