from waitress import serve
from AdiclaVideo.wsgi import application
import multiprocessing
import os

# Calcular el número óptimo de hilos (8x CPUs para streaming de video)
threads = multiprocessing.cpu_count() * 8

print(f"Iniciando servidor con {threads} hilos...")

# Configuración ultra-optimizada para streaming de videos
serve(
    application, 
    host='0.0.0.0', 
    port=8000,
    threads=threads,           # Más hilos para manejar más conexiones simultáneas
    url_scheme='http',        
    channel_timeout=300,       # 5 minutos de timeout (suficiente para chunks HLS)
    send_bytes=262144,        # Buffer de envío de 256KB (óptimo para segmentos HLS)
    connection_limit=1000,     # Límite de conexiones simultáneas
    cleanup_interval=30,       # Limpieza más frecuente
    max_request_header_size=32768,  # 32KB para headers
    max_request_body_size=1073741824,  # 1GB máximo para uploads
    outbuf_overflow=52428800,  # Buffer de 50MB (suficiente para segmentos HLS)
    inbuf_overflow=52428800,   # Buffer de entrada de 50MB
    clear_untrusted_proxy_headers=False,
    asyncore_use_poll=True     # Mejor rendimiento
)