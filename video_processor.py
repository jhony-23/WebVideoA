import os
import sys
import django
import time
import shutil
from pathlib import Path

# Configurar Django
sys.path.append(str(Path(__file__).parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AdiclaVideo.settings_production')
django.setup()

from django.conf import settings
from videos.models import Media
from videos.utils import VideoProcessor

def process_video_queue():
    print("Iniciando procesador de videos...")
    
    while True:
        # Buscar videos pendientes
        pending = Media.objects.filter(
            media_type='video',
            stream_status='pending'
        ).order_by('uploaded_at').first()
        
        if pending:
            print(f"\nProcesando video: {pending.title}")
            try:
                Media.objects.filter(pk=pending.pk).update(
                    stream_status='processing',
                    error_message='' 
                )

                processor = VideoProcessor(pending.file.path, media_id=pending.pk)
                previous_hls_path = pending.hls_path
                success, metadata = processor.transcode_to_hls()

                if success:
                    Media.objects.filter(pk=pending.pk).update(
                        stream_status='ready',
                        is_stream_ready=True,
                        hls_path=metadata.get('relative_output_dir'),
                        available_qualities=metadata.get('qualities', []),
                        duration=metadata.get('duration') or 0.0,
                        width=metadata.get('width'),
                        height=metadata.get('height'),
                        error_message=''
                    )
                    new_hls_path = metadata.get('relative_output_dir')
                    if previous_hls_path and new_hls_path and previous_hls_path != new_hls_path:
                        old_dir = Path(settings.MEDIA_ROOT) / previous_hls_path
                        shutil.rmtree(old_dir, ignore_errors=True)
                    print(f"✓ Video {pending.title} procesado exitosamente")
                else:
                    Media.objects.filter(pk=pending.pk).update(
                        stream_status='failed',
                        is_stream_ready=False,
                        available_qualities=[],
                        error_message=metadata.get('error', 'Error en la transcodificación')
                    )
                    print(f"✗ Error procesando {pending.title}")

            except Exception as exc:
                Media.objects.filter(pk=pending.pk).update(
                    stream_status='failed',
                    is_stream_ready=False,
                    error_message=str(exc)
                )
                print(f"✗ Error: {str(exc)}")
        
        # Esperar antes de la siguiente verificación
        time.sleep(5)

if __name__ == '__main__':
    process_video_queue()