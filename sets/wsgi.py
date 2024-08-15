"""
WSGI config for sets project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from django.conf import settings
import site

site.addsitedir("../.venv/lib/python3.10/site-packages")

import sets.monitor as monitor

monitor.start(interval=1.0)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sets.settings')

if settings.DEBUG:
    import debugpy
    debugpy.listen(("0.0.0.0", settings.ATTACH_DEBUG_PORT))

application = get_wsgi_application()