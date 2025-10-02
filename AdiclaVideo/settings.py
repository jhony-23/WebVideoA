from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
SECRET_KEY = 'django-insecure-0)h94amrf7vl3v70v#^e9o__hpkowcp0z%fn@v(3g09dtez^eh'
DEBUG = True

# Permitir estos hosts (IP del servidor y localhost para pruebas locales)
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '192.168.0.149']

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
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'videos.middleware.StreamingMediaMiddleware',  # Nuestro middleware de streaming
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



DATABASES = {
    'default': {
        'ENGINE': 'mssql',
        'NAME': 'PlataformaVideosA',
        'HOST': '192.168.56.1', 
        'PORT': '1433', 
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

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Logging centralizado para diagnóstico de streaming y transcodificación
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {name} :: {message}',
            'style': '{'
        },
        'simple': {
            'format': '{levelname}: {message}',
            'style': '{'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'stream_file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'streaming.log'),
            'formatter': 'verbose',
            'encoding': 'utf-8'
        },
        'ffmpeg_file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'ffmpeg.log'),
            'formatter': 'verbose',
            'encoding': 'utf-8'
        }
    },
    'loggers': {
        'videos.streaming': {
            'handlers': ['console', 'stream_file'],
            'level': 'INFO',
            'propagate': False
        },
        'videos.ffmpeg': {
            'handlers': ['console', 'ffmpeg_file'],
            'level': 'INFO',
            'propagate': False
        },
        'django': {
            'handlers': ['console'],
            'level': 'WARNING'
        }
    }
}

# Configuración de autenticación
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/upload/'
SESSION_COOKIE_AGE = 28800  # 8 horas en segundos
