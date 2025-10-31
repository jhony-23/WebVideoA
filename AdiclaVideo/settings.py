from pathlib import Path
import os
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Environment configuration (uses django-environ + python-dotenv)
ENV_FILE = BASE_DIR / '.env'
env = environ.Env(
    DJANGO_DEBUG=(bool, True),
)
if ENV_FILE.exists():
    environ.Env.read_env(str(ENV_FILE))

# Quick-start development settings - unsuitable for production
SECRET_KEY = env('DJANGO_SECRET_KEY', default='django-insecure-0)h94amrf7vl3v70v#^e9o__hpkowcp0z%fn@v(3g09dtez^eh')
DEBUG = env.bool('DJANGO_DEBUG', default=True)

# Permitir estos hosts (IP del servidor y localhost para pruebas locales)
ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=['127.0.0.1', 'localhost', '192.168.0.149'])

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
        'DIRS': [BASE_DIR / 'videos' / 'templates'],  # Carpeta templates de la app
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
        'ENGINE': env('DJANGO_DB_ENGINE', default='mssql'),
        'NAME': env('DJANGO_DB_NAME', default='PlataformaVideosA'),
        'HOST': env('DJANGO_DB_HOST', default='192.168.56.1'),
        'PORT': env('DJANGO_DB_PORT', default='1433'),
        'USER': env('DJANGO_DB_USER', default='vm_user'),
        'PASSWORD': env('DJANGO_DB_PASSWORD', default='Adicla221231'),
        'OPTIONS': {
            'driver': env('DJANGO_DB_DRIVER', default='ODBC Driver 17 for SQL Server'),
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
STATIC_URL = env('DJANGO_STATIC_URL', default='/static/')

# Para producción (collectstatic los copia aquí)
STATIC_ROOT = os.path.abspath(env('DJANGO_STATIC_ROOT', default=str(BASE_DIR / 'staticfiles')))

# Para desarrollo: indica dónde buscar los archivos estáticos originales
STATICFILES_DIRS = [
    str(BASE_DIR / 'videos' / 'static'),
]

# Carpeta donde se guardarán los videos subidos
MEDIA_URL = env('DJANGO_MEDIA_URL', default='/media/')
MEDIA_ROOT = os.path.abspath(env('DJANGO_MEDIA_ROOT', default=str(BASE_DIR / 'media')))
os.makedirs(MEDIA_ROOT, exist_ok=True)
os.makedirs(os.path.join(MEDIA_ROOT, 'uploads'), exist_ok=True)
os.makedirs(os.path.join(MEDIA_ROOT, 'hls'), exist_ok=True)

STATICFILES_STORAGE = env('DJANGO_STATICFILES_STORAGE', default='whitenoise.storage.CompressedManifestStaticFilesStorage')

# Configuración FFmpeg accesible en código
FFMPEG_BIN_DIR = env('FFMPEG_BIN_DIR', default='')
FFMPEG_BIN = env('FFMPEG_BIN', default='ffmpeg')
FFPROBE_BIN = env('FFPROBE_BIN', default='ffprobe')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Logging centralizado para diagnóstico de streaming y transcodificación
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)

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
            'filename': str(LOG_DIR / 'streaming.log'),
            'formatter': 'verbose',
            'encoding': 'utf-8'
        },
        'ffmpeg_file': {
            'class': 'logging.FileHandler',
            'filename': str(LOG_DIR / 'ffmpeg.log'),
            'formatter': 'verbose',
            'encoding': 'utf-8'
        }
    },
    'loggers': {
        'videos.streaming': {
            'handlers': ['console', 'stream_file'],
            'level': env('STREAMING_LOG_LEVEL', default='INFO'),
            'propagate': False
        },
        'videos.ffmpeg': {
            'handlers': ['console', 'ffmpeg_file'],
            'level': env('FFMPEG_LOG_LEVEL', default='INFO'),
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
SESSION_COOKIE_AGE = env.int('SESSION_COOKIE_AGE', default=28800)  # 8 horas en segundos

# Configuración para sesiones múltiples independientes
SESSION_COOKIE_NAME = env('SESSION_COOKIE_NAME', default='sessionid')
SESSION_COOKIE_PATH = '/'
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Permitir múltiples sesiones por usuario en diferentes pestañas
# Usar diferentes nombres de cookie para diferentes sistemas
TAREAS_SESSION_COOKIE_NAME = env('TAREAS_SESSION_COOKIE_NAME', default='tareas_sessionid')
UPLOAD_SESSION_COOKIE_NAME = env('UPLOAD_SESSION_COOKIE_NAME', default='upload_sessionid')
