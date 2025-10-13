"""
Middleware para manejar sesiones independientes por sistema
"""
from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware
from django.utils.cache import patch_vary_headers


class MultipleSessionMiddleware(SessionMiddleware):
    """
    Middleware que permite sesiones independientes para diferentes sistemas
    """
    
    def process_request(self, request):
        # Determinar qué tipo de sesión usar basado en la URL
        session_key = self.get_session_key_for_path(request.path)
        
        # Establecer el nombre de cookie dinámicamente
        self.cookie_name = session_key
        
        # Llamar al método padre
        super().process_request(request)
    
    def process_response(self, request, response):
        """
        Procesar respuesta con el nombre de cookie correcto
        """
        # Asegurar que usamos el nombre de cookie correcto
        if hasattr(request, 'session'):
            session_key = self.get_session_key_for_path(request.path)
            self.cookie_name = session_key
        
        return super().process_response(request, response)
    
    def get_session_key_for_path(self, path):
        """
        Determinar qué nombre de cookie usar según la ruta
        """
        if path.startswith('/tareas/'):
            return getattr(settings, 'TAREAS_SESSION_COOKIE_NAME', 'tareas_sessionid')
        elif path.startswith('/upload/') or path.startswith('/login/') or path.startswith('/logout/'):
            return getattr(settings, 'UPLOAD_SESSION_COOKIE_NAME', 'upload_sessionid')
        else:
            # Usar cookie por defecto para otras rutas
            return getattr(settings, 'SESSION_COOKIE_NAME', 'sessionid')