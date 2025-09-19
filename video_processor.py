import os
import sys
import django
import time
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
            file__endswith='.mp4',
            stream_status='pending'
        ).order_by('uploaded_at').first()
        
        if pending:
            print(f"\nProcesando video: {pending.title}")
            try:
                # Marcar como procesando
                pending.stream_status = 'processing'
                pending.save()
                
                # Procesar el video
                input_path = os.path.join(settings.MEDIA_ROOT, str(pending.file))
                processor = VideoProcessor(input_path)
                
                if processor.transcode_to_hls():
                    # Actualizar metadatos
                    video_info = processor._get_video_info()
                    duration = float(video_info['streams'][0].get('duration', 0))
                    
                    # Verificar calidades generadas
                    qualities = []
                    for quality in ['720p', '1080p', '480p']:
                        if os.path.exists(os.path.join(processor.output_dir, f'{quality}.m3u8')):
                            qualities.append(quality)
                    
                    # Actualizar video
                    pending.stream_status = 'completed'
                    pending.is_stream_ready = True
                    pending.hls_path = f'hls/{pending.file.name.replace(".mp4", "")}/master.m3u8'
                    pending.available_qualities = qualities
                    pending.duration = duration
                    pending.save()
                    
                    print(f"✓ Video {pending.title} procesado exitosamente")
                else:
                    pending.stream_status = 'error'
                    pending.save()
                    print(f"✗ Error procesando {pending.title}")
                    
            except Exception as e:
                pending.stream_status = 'error'
                pending.error_message = str(e)
                pending.save()
                print(f"✗ Error: {str(e)}")
        
        # Esperar antes de la siguiente verificación
        time.sleep(5)

if __name__ == '__main__':
    process_video_queue()