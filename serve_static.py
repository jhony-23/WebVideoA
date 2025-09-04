import os
from wsgiref.simple_server import make_server
from django.core.wsgi import get_wsgi_application
from waitress import serve
from whitenoise import WhiteNoise

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "AdiclaVideo.settings")
application = get_wsgi_application()
application = WhiteNoise(application, root=os.path.join(os.path.dirname(__file__), 'static'))
application.add_files(os.path.join(os.path.dirname(__file__), 'media'), prefix='media/')

serve(application, host='0.0.0.0', port=8000)
