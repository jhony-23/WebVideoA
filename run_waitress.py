from waitress import serve
from AdiclaVideo.wsgi import application
import multiprocessing
import os

# Calcular el número óptimo de hilos (aumentamos a 4x CPUs para mejor rendimiento)
threads = multiprocessing.cpu_count() * 4

# Configuración ultra-optimizada para streaming de videos muy grandes
serve(
    application, 
    host='0.0.0.0', 
    port=8000,
    threads=threads,           # Número de hilos trabajadores (aumentado)
    url_scheme='http',         # Esquema de URL
    channel_timeout=1200,      # Tiempo de espera para conexiones (20 minutos para videos largos)
    send_bytes=1048576,        # Tamaño del buffer de envío (1MB - óptimo para videos grandes)
    connection_limit=2000,     # Límite de conexiones simultáneas
    cleanup_interval=60,       # Intervalo de limpieza de conexiones inactivas
    max_request_header_size=65536,  # Tamaño máximo de cabecera (64KB)
    max_request_body_size=4294967296,  # Tamaño máximo del cuerpo (4GB para videos grandes)
    outbuf_overflow=104857600,  # Buffer de desbordamiento (100MB - óptimo para videos de 80MB+)
    inbuf_overflow=104857600,   # Buffer de entrada (100MB - óptimo para videos de 80MB+)
    clear_untrusted_proxy_headers=False,  # Mantener cabeceras de proxy
    asyncore_use_poll=True,    # Usar poll() en lugar de select() para mejor rendimiento
)