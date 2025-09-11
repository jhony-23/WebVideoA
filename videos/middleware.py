import re
import os
from django.conf import settings
from django.http import StreamingHttpResponse, HttpResponse
from django.urls import re_path
from wsgiref.util import FileWrapper

class RangeFileWrapper(object):
    """
    Wrapper para servir archivos en chunks con soporte para Range requests.
    """
    def __init__(self, filelike, blksize=8192, offset=0, length=None):
        self.filelike = filelike
        self.filelike.seek(offset, os.SEEK_SET)
        self.remaining = length
        self.blksize = blksize

    def __iter__(self):
        return self

    def __next__(self):
        if self.remaining is None:
            data = self.filelike.read(self.blksize)
            if data:
                return data
            raise StopIteration()
        else:
            if self.remaining <= 0:
                raise StopIteration()
            data = self.filelike.read(min(self.remaining, self.blksize))
            if not data:
                raise StopIteration()
            self.remaining -= len(data)
            return data

class StreamingMediaMiddleware:
    """
    Middleware para servir archivos multimedia con soporte para streaming y Range requests.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # Compilar expresión regular para identificar URLs de media
        media_url = settings.MEDIA_URL.lstrip('/').rstrip('/')
        regex = r'^/{}/(.*?)$'.format(media_url)
        self.media_re = re.compile(regex)
        
    def __call__(self, request):
        media_match = self.media_re.match(request.path)
        
        # Si no es una URL de media, continuar con el flujo normal
        if not media_match:
            return self.get_response(request)
            
        media_path = os.path.join(settings.MEDIA_ROOT, media_match.group(1))
        
        # Verificar si el archivo existe
        if not os.path.exists(media_path):
            return self.get_response(request)
            
        # Detectar si es un archivo de video
        file_ext = os.path.splitext(media_path)[1].lower()
        is_video = file_ext in ['.mp4', '.webm', '.ogg', '.mov', '.avi']
        
        # Si no es video o no hay Range header, servir normalmente
        if not is_video or 'HTTP_RANGE' not in request.META:
            return self.get_response(request)
            
        # Manejar Range requests para video
        size = os.path.getsize(media_path)
        content_type = 'video/mp4' if file_ext == '.mp4' else 'application/octet-stream'
        
        # Parsear el header Range
        range_header = request.META['HTTP_RANGE']
        range_match = re.match(r'bytes=(\d+)-(\d*)', range_header)
        
        if not range_match:
            return HttpResponse(status=416)  # Range Not Satisfiable
            
        start = int(range_match.group(1))
        end = int(range_match.group(2)) if range_match.group(2) else size - 1
        
        if start >= size:
            return HttpResponse(status=416)  # Range Not Satisfiable
            
        length = end - start + 1
        
        response = StreamingHttpResponse(
            FileWrapper(open(media_path, 'rb'), 8192, offset=start, length=length),
            status=206,  # Partial Content
            content_type=content_type
        )
        
        response['Content-Length'] = str(length)
        response['Content-Range'] = f'bytes {start}-{end}/{size}'
        response['Accept-Ranges'] = 'bytes'
        
        return response


class CacheControlMiddleware:
    """
    Middleware para añadir encabezados de caché a archivos multimedia
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Extensiones de archivos de media
        self.media_extensions = ['.mp4', '.webm', '.ogg', '.mp3', '.jpg', '.jpeg', '.png', '.gif']
        
    def __call__(self, request):
        response = self.get_response(request)
        
        # Verificar si es un archivo multimedia basado en la extensión
        path = request.path.lower()
        is_media = any(path.endswith(ext) for ext in self.media_extensions)
        
        if is_media:
            # Agregar encabezados de caché para archivos multimedia
            # Cache por 1 semana = 604800 segundos
            response['Cache-Control'] = 'public, max-age=604800, immutable'
            response['Expires'] = 'Sun, 1 Jan 2030 00:00:00 GMT'
            
        return response
