from waitress import serve
from AdiclaVideo.wsgi import application
import multiprocessing
import os

# Calcular el número óptimo de hilos (aumentamos a 4x CPUs para mejor rendimiento)
threads = multiprocessing.cpu_count() * 4

# Configuración super optimizada para streaming de video
serve(
    application, 
    host='0.0.0.0', 
    port=8000,
    threads=threads,           # Número de hilos trabajadores (aumentado)
    url_scheme='http',         # Esquema de URL
    channel_timeout=600,       # Tiempo de espera para conexiones (10 minutos)
    send_bytes=262144,         # Tamaño del buffer de envío (256KB - cuadruplicado)
    connection_limit=2000,     # Límite de conexiones simultáneas (duplicado)
    cleanup_interval=60,       # Intervalo de limpieza de conexiones inactivas
    max_request_header_size=65536,  # Tamaño máximo de cabecera (64KB)
    max_request_body_size=2147483648,  # Tamaño máximo del cuerpo (2GB para videos)
    outbuf_overflow=31457280,  # Buffer de desbordamiento (30MB - triplicado)
    inbuf_overflow=31457280,   # Buffer de entrada (30MB - triplicado)
    clear_untrusted_proxy_headers=False,  # Mantener cabeceras de proxy
    asyncore_use_poll=True,    # Usar poll() en lugar de select() para mejor rendimiento
)