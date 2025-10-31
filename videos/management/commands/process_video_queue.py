import time
import shutil
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from videos.models import Media
from videos.utils import VideoProcessor

class Command(BaseCommand):
    help = 'Procesa videos en cola de manera continua'

    def handle(self, *args, **kwargs):
        self.stdout.write('Iniciando procesador de cola de videos...')
        
        while True:
            # Buscar videos pendientes
            pending_videos = Media.objects.filter(
                media_type='video',
                is_stream_ready=False,
                stream_status='pending'
            ).order_by('uploaded_at')[:1]  # Procesar uno a la vez
            
            if pending_videos:
                video = pending_videos[0]
                self.stdout.write(f'Procesando video: {video.file.name}')
                
                try:
                    # Marcar como en procesamiento
                    Media.objects.filter(pk=video.pk).update(
                        stream_status='processing',
                        error_message=''
                    )

                    processor = VideoProcessor(video.file.path, media_id=video.pk)
                    previous_hls_path = video.hls_path
                    success, metadata = processor.transcode_to_hls()

                    if success:
                        Media.objects.filter(pk=video.pk).update(
                            is_stream_ready=True,
                            stream_status='ready',
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
                        self.stdout.write(self.style.SUCCESS(
                            f'✓ Video {video.file.name} procesado exitosamente'
                        ))
                    else:
                        Media.objects.filter(pk=video.pk).update(
                            stream_status='failed',
                            is_stream_ready=False,
                            available_qualities=[],
                            error_message=metadata.get('error', 'Error en la transcodificación')
                        )

                except Exception as exc:
                    Media.objects.filter(pk=video.pk).update(
                        stream_status='failed',
                        is_stream_ready=False,
                        error_message=str(exc)
                    )
                    self.stdout.write(self.style.ERROR(f'Error: {str(exc)}'))
            
            # Esperar antes de la siguiente verificación
            time.sleep(10)  # 10 segundos entre verificaciones