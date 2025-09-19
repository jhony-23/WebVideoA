from waitress import serve
from AdiclaVideo.wsgi import application
import multiprocessing
import os

"""Script de arranque Waitress.

Ajustes enfocados a equilibrio CPU/RAM en Windows sin proxy inverso:
- Menos hilos (cpu * 2) para evitar excesivo contexto en transcodificaciones paralelas.
- Buffers moderados: suficientes para servir segmentos HLS (normalmente ~300-800KB) sin inflar RAM.
- Timeouts razonables (5 min) para requests prolongadas pero no ilimitadas.
- Permite override por variables de entorno para tuning futuro.
"""

CPU_COUNT = multiprocessing.cpu_count()
THREADS = int(os.getenv('WAITRESS_THREADS', CPU_COUNT * 2))
PORT = int(os.getenv('PORT', 8000))
CHANNEL_TIMEOUT = int(os.getenv('WAITRESS_CHANNEL_TIMEOUT', 300))  # 5 min

print(f"Iniciando Waitress en 0.0.0.0:{PORT} con {THREADS} hilos (CPUs={CPU_COUNT})")

serve(
    application,
    host='0.0.0.0',
    port=PORT,
    threads=THREADS,
    url_scheme='http',
    channel_timeout=CHANNEL_TIMEOUT,
    send_bytes=512 * 1024,          # 512KB por envío
    connection_limit=int(os.getenv('WAITRESS_CONN_LIMIT', 300)),
    cleanup_interval=30,
    max_request_header_size=32768,  # 32KB headers
    max_request_body_size=2 * 1024 * 1024 * 1024,  # 2GB uploads
    outbuf_overflow=32 * 1024 * 1024,  # 32MB salida
    inbuf_overflow=32 * 1024 * 1024,   # 32MB entrada
    clear_untrusted_proxy_headers=False,
    asyncore_use_poll=True,
    ident=None,
    expose_tracebacks=False,
)