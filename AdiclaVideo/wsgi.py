"""
WSGI config for AdiclaVideo project.
It exposes the WSGI callable as a module-level variable named ``application``.
For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise  # <-- Esto sirve archivos estáticos (CSS, JS, imágenes)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AdiclaVideo.settings')

application = get_wsgi_application()
# Aquí configuramos WhiteNoise para que sirva los archivos estáticos desde STATIC_ROOT
application = WhiteNoise(application, root=os.path.join(os.path.dirname(__file__), 'staticfiles'), max_age=31536000)
