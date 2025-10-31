from django.core.management.base import BaseCommand
from django.conf import settings
from videos.models import Media
from videos.utils import VideoProcessor
import time
import shutil
from pathlib import Path

class Command(BaseCommand):
    help = 'Procesa videos pendientes generando versiones HLS multi-calidad'

    def handle(self, *args, **options):
        # Procesar videos pendientes
        pending_videos = Media.objects.filter(
            media_type='video',
            stream_status='pending'
        )

        for video in pending_videos:
            self.stdout.write(f"Procesando video: {video.title}")
            
            try:
                # Marcar como en proceso
                video.stream_status = 'processing'
                video.save(update_fields=['stream_status'])
                
                # Iniciar procesamiento
                processor = VideoProcessor(video.file.path, media_id=video.pk)
                previous_hls_path = video.hls_path

                # Transcodificar a HLS
                success, metadata = processor.transcode_to_hls()

                if success:
                    # Actualizar modelo con información del stream
                    video.is_stream_ready = True
                    video.stream_status = 'ready'
                    video.hls_path = metadata.get('relative_output_dir')
                    video.available_qualities = metadata.get('qualities', [])
                    video.duration = metadata.get('duration') or 0.0
                    video.width = metadata.get('width')
                    video.height = metadata.get('height')
                    
                    # Crear thumbnail
                    processor.create_thumbnail()
                    
                    video.save()

                    # Limpiar carpeta HLS anterior si cambió
                    new_hls_path = metadata.get('relative_output_dir')
                    if previous_hls_path and new_hls_path and previous_hls_path != new_hls_path:
                        old_dir = Path(settings.MEDIA_ROOT) / previous_hls_path
                        shutil.rmtree(old_dir, ignore_errors=True)
                    self.stdout.write(self.style.SUCCESS(f"✓ Video {video.title} procesado exitosamente"))
                else:
                    video.stream_status = 'failed'
                    video.error_message = metadata.get('error', 'Error en la transcodificación')
                    video.available_qualities = []
                    video.is_stream_ready = False
                    video.save()
                    self.stdout.write(self.style.ERROR(f"✗ Error procesando {video.title}: {video.error_message}"))
            
            except Exception as e:
                video.stream_status = 'failed'
                video.error_message = str(e)
                video.is_stream_ready = False
                video.save()
                self.stdout.write(self.style.ERROR(f"✗ Error inesperado en {video.title}: {e}"))
            
            # Pequeña pausa entre videos para no saturar CPU
            time.sleep(1)