from .settings import *  # noqa

# Ajustes específicos de producción
DEBUG = False
ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=['192.99.121.227', '172.32.32.30', '127.0.0.1', 'localhost'])

# Reordenar middleware para incluir WhiteNoise y CacheControl
base_middleware = [m for m in MIDDLEWARE if m not in {
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'videos.middleware.CacheControlMiddleware'
}]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    *base_middleware,
]
if 'videos.middleware.CacheControlMiddleware' not in MIDDLEWARE:
    MIDDLEWARE.append('videos.middleware.CacheControlMiddleware')

STATICFILES_STORAGE = env('DJANGO_STATICFILES_STORAGE', default='whitenoise.storage.CompressedManifestStaticFilesStorage')

# Forzar actualización de base de datos con valores de producción
DATABASES['default'] = {
    'ENGINE': env('DJANGO_DB_ENGINE', default='mssql'),
    'NAME': env('DJANGO_DB_NAME', default='PlataformaVideosA'),
    'HOST': env('DJANGO_DB_HOST', default='172.32.32.30'),
    'PORT': env('DJANGO_DB_PORT', default='49789'),
    'USER': env('DJANGO_DB_USER', default='vm_user'),
    'PASSWORD': env('DJANGO_DB_PASSWORD', default='Adicla221231'),
    'OPTIONS': {
        'driver': env('DJANGO_DB_DRIVER', default='ODBC Driver 17 for SQL Server'),
    },
}

# Ajustes de cookies/seguridad recomendados para producción (overridable via .env)
SESSION_COOKIE_SECURE = env.bool('SESSION_COOKIE_SECURE', default=True)
CSRF_COOKIE_SECURE = env.bool('CSRF_COOKIE_SECURE', default=True)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=False)
SECURE_HSTS_PRELOAD = env.bool('SECURE_HSTS_PRELOAD', default=False)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
