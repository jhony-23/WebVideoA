import re
import os
from django.conf import settings
from django.http import StreamingHttpResponse, HttpResponse, FileResponse
from django.urls import re_path
from wsgiref.util import FileWrapper as WSGIFileWrapper

# Usar nuestro wrapper personalizado para mejor rendimiento
class RangeFileWrapper(object):
    """
    Wrapper para servir archivos en chunks con soporte para Range requests.
    """
    def __init__(self, filelike, blksize=8388608, offset=0, length=None):  # 8MB por chunk para streaming eficiente
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
    """Middleware para servir videos MP4 con soporte de Range.

    Se elimina intervención sobre HLS (.m3u8 / .ts) para que WhiteNoise/Django
    los sirva directamente (reduce overhead y evita manipular cabeceras que
    algunos players cachean de forma inesperada). Solo manejamos Range en
    archivos grandes tipo MP4/WebM/Mov.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # Compilar expresión regular para identificar URLs de media
        media_url = settings.MEDIA_URL.lstrip('/').rstrip('/')
        regex = r'^/{}/(.*?)$'.format(media_url)
        self.media_re = re.compile(regex)
        
        # Mapeo de extensiones a content types
        self.content_types = {
            '.mp4': 'video/mp4',
            '.webm': 'video/webm',
            '.ogg': 'video/ogg',
            '.mov': 'video/quicktime',
            '.m3u8': 'application/vnd.apple.mpegurl',
            '.ts': 'video/mp2t',
            '.jpg': 'image/jpeg',
            '.png': 'image/png',
        }
        
    def __call__(self, request):
        media_match = self.media_re.match(request.path)
        
        # Si no es una URL de media, continuar con el flujo normal
        if not media_match:
            return self.get_response(request)
            
        media_path = os.path.join(settings.MEDIA_ROOT, media_match.group(1))
        
        # Verificar si el archivo existe
        if not os.path.exists(media_path):
            return self.get_response(request)
            
        # Detectar tipo de archivo
        file_ext = os.path.splitext(media_path)[1].lower()
        is_video = file_ext in ['.mp4', '.webm', '.ogg', '.mov']
        is_hls = file_ext in ['.m3u8', '.ts']
        
        # Content-Type específico para el tipo de archivo
        content_type = self.content_types.get(file_ext, 'application/octet-stream')
        
        # HLS: no intervenir (lo sirve WhiteNoise / default). Evitar overhead.
        if is_hls:
            return self.get_response(request)
            
        # Si no es video o no hay Range header, servir normalmente
        if not is_video:
            return self.get_response(request)

        # Sin Range: devolver respuesta completa (fallback). Navegadores suelen iniciar con Range.
        if 'HTTP_RANGE' not in request.META:
            resp = FileResponse(open(media_path, 'rb'), content_type=content_type)
            resp['Accept-Ranges'] = 'bytes'
            resp['Cache-Control'] = 'public, max-age=604800, immutable'
            return resp
            
        # Manejar Range requests para video
        size = os.path.getsize(media_path)
        content_type = 'video/mp4' if file_ext == '.mp4' else 'application/octet-stream'
        
        # Detectar dispositivos de baja potencia como Smart TVs
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        is_tv = 'lg' in user_agent or 'webos' in user_agent or 'smart-tv' in user_agent or 'tv' in user_agent
        
        # Chunk adaptativo moderado: menos agresivo (reduce latencia inicial)
        if is_tv:
            chunk_size = 5 * 1024 * 1024   # 5MB
            buffer_size = 256 * 1024       # 256KB
        else:
            chunk_size = 8 * 1024 * 1024   # 8MB
            buffer_size = 512 * 1024       # 512KB
        
        # Parsear el header Range
        range_header = request.META['HTTP_RANGE']
        range_match = re.match(r'bytes=(\d+)-(\d*)', range_header)
        
        if not range_match:
            return HttpResponse(status=416)  # Range Not Satisfiable
            
        start = int(range_match.group(1))
        end = int(range_match.group(2)) if range_match.group(2) else size - 1
        
        # Límite de tamaño de chunk para mejorar el rendimiento
        # Garantiza que no enviamos chunks demasiado grandes
        if end - start > chunk_size:
            end = start + chunk_size
        
        if start >= size:
            return HttpResponse(status=416)  # Range Not Satisfiable
            
        length = end - start + 1
        
        # Abrir archivo con buffer optimizado para videos grandes
        try:
            # Abrir con buffer optimizado
            buffer_value = 512 * 1024 if is_tv else 1024 * 1024
            file_obj = open(media_path, 'rb', buffering=buffer_value)
            response = StreamingHttpResponse(
                RangeFileWrapper(file_obj, buffer_size, offset=start, length=length),
                status=206,  # Partial Content
                content_type=content_type
            )
        except Exception as e:
            # En caso de error, intentar con método estándar
            file_obj = open(media_path, 'rb')
            response = StreamingHttpResponse(
                RangeFileWrapper(file_obj, 131072, offset=start, length=length),
                status=206,
                content_type=content_type
            )
        
        response['Content-Length'] = str(length)
        response['Content-Range'] = f'bytes {start}-{end}/{size}'
        response['Accept-Ranges'] = 'bytes'
        response['X-Accel-Buffering'] = 'yes'  # Habilitar buffering en proxy
        
        # Cabeceras específicas según el dispositivo
        if is_tv:
            # Cabeceras optimizadas para Smart TVs
            response['Cache-Control'] = 'public, max-age=2592000'  # 30 días
            # Evitar cabeceras complejas que pueden no ser bien soportadas
            response['X-Content-Type-Options'] = 'nosniff'
            # No añadir cabeceras Link complejas para TVs
        else:
            # Cabeceras estándar para navegadores de escritorio
            response['Cache-Control'] = 'public, max-age=604800, immutable'
            response['X-Content-Type-Options'] = 'nosniff'
        
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
            # Cache por 2 semanas = 1209600 segundos (duplicado)
            response['Cache-Control'] = 'public, max-age=1209600, immutable'
            response['Expires'] = 'Sun, 1 Jan 2030 00:00:00 GMT'
            response['X-Content-Type-Options'] = 'nosniff'
            
            # Si es video, añadir encabezados de rendimiento
            if any(path.endswith(ext) for ext in ['.mp4', '.webm', '.ogg']):
                response['Accept-Ranges'] = 'bytes'
                # Pre-cargar el video desde el inicio, mejora la experiencia
                response.setdefault('Link', '<{}>; rel=preload; as=video'.format(request.path))
            
        return response
