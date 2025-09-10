"""
WSGI config for AdiclaVideo project.
It exposes the WSGI callable as a module-level variable named ``application``.
For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise  # Sirve archivos estáticos (CSS, JS, imágenes)
from django.conf import settings   # Para acceder a STATIC_ROOT

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AdiclaVideo.settings_production')

application = get_wsgi_application()

# Configuramos WhiteNoise para que sirva los archivos estáticos desde STATIC_ROOT
application = WhiteNoise(application, root=settings.STATIC_ROOT, max_age=31536000)

# Servir videos e imágenes subidas (media)
application.add_files(settings.MEDIA_ROOT, prefix='media/')