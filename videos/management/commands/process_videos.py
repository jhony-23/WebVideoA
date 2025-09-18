from django.core.management.base import BaseCommand
from videos.models import Media
from videos.utils import VideoProcessor
import os
import time
from django.conf import settings

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
                
                # Debugging
                self.stdout.write(f"Ruta del archivo: {video.file.path}")
                self.stdout.write(f"¿Existe el archivo? {os.path.exists(video.file.path)}")
                self.stdout.write(f"Contenido de media/: {os.listdir(settings.MEDIA_ROOT)}")
                
                # Construir ruta absoluta
                file_path = os.path.join(settings.MEDIA_ROOT, str(video.file))
                self.stdout.write(f"Ruta construida: {file_path}")
                self.stdout.write(f"¿Existe la ruta construida? {os.path.exists(file_path)}")
                
                # Iniciar procesamiento
                processor = VideoProcessor(file_path)
                
                # Transcodificar a HLS
                success, result = processor.transcode_to_hls()
                
                if success:
                    # Actualizar modelo con información del stream
                    video.is_stream_ready = True
                    video.stream_status = 'ready'
                    video.hls_path = os.path.relpath(result, settings.MEDIA_ROOT)
                    video.available_qualities = list(processor.QUALITY_PROFILES.keys())
                    
                    # Crear thumbnail
                    processor.create_thumbnail()
                    
                    video.save()
                    self.stdout.write(self.style.SUCCESS(f"✓ Video {video.title} procesado exitosamente"))
                else:
                    video.stream_status = 'failed'
                    video.error_message = str(result)
                    video.save()
                    self.stdout.write(self.style.ERROR(f"✗ Error procesando {video.title}: {result}"))
            
            except Exception as e:
                video.stream_status = 'failed'
                video.error_message = str(e)
                video.save()
                self.stdout.write(self.style.ERROR(f"✗ Error inesperado en {video.title}: {e}"))
            
            # Pequeña pausa entre videos para no saturar CPU
            time.sleep(1)