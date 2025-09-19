from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
os.environ["PATH"] += os.pathsep + r"C:\ffmpeg\bin"
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
SECRET_KEY = 'django-insecure-0)h94amrf7vl3v70v#^e9o__hpkowcp0z%fn@v(3g09dtez^eh'
DEBUG = False

# Permitir estos hosts (IP del servidor y localhost para pruebas locales)
ALLOWED_HOSTS = ['192.99.121.227', '172.32.32.30', '127.0.0.1', 'localhost']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'widget_tweaks',
    'videos.apps.VideosConfig',  # Nuestra app

]

MIDDLEWARE = [
    # Security primero (recomendación oficial) y luego WhiteNoise
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'videos.middleware.StreamingMediaMiddleware',  # Middleware de streaming
    'videos.middleware.CacheControlMiddleware',    # Middleware de caché
]

ROOT_URLCONF = 'AdiclaVideo.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'videos', 'templates')],  # Carpeta templates de la app
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'AdiclaVideo.wsgi.application'

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DATABASES = {
    'default': {
        'ENGINE': 'mssql',
        'NAME': 'PlataformaVideosA',
        'HOST': '172.32.32.30',
        'PORT': '49789',
        'USER': 'vm_user',
        'PASSWORD': 'Adicla221231',
        'OPTIONS': {
            'driver': 'ODBC Driver 17 for SQL Server',
        },
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/Guatemala'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'

# Para producción (collectstatic los copia aquí)
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Para desarrollo: indica dónde buscar los archivos estáticos originales
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'videos', 'static'),
]

# Carpeta donde se guardarán los videos subidos
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
