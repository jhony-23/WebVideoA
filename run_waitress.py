from waitress import serve
from AdiclaVideo.wsgi import application
import multiprocessing

# Calcular el número óptimo de hilos (normalmente número de CPUs * 2)
threads = multiprocessing.cpu_count() * 2

# Configuración optimizada para streaming de video
serve(
    application, 
    host='0.0.0.0', 
    port=8000,
    threads=threads,           # Número de hilos trabajadores
    url_scheme='http',         # Esquema de URL
    channel_timeout=300,       # Tiempo de espera para conexiones (5 minutos)
    send_bytes=65536,          # Tamaño del buffer de envío (64KB)
    connection_limit=1000,     # Límite de conexiones simultáneas
    cleanup_interval=30,       # Intervalo de limpieza de conexiones inactivas
    max_request_header_size=32768,  # Tamaño máximo de cabecera (32KB)
    max_request_body_size=1073741824,  # Tamaño máximo del cuerpo (1GB para videos)
    outbuf_overflow=10485760,  # Buffer de desbordamiento (10MB)
    inbuf_overflow=10485760,   # Buffer de entrada (10MB)
)