from django.core.management.base import BaseCommand
from videos.models import Media
from videos.utils import VideoProcessor

class Command(BaseCommand):
    help = 'Procesa todos los videos existentes que no han sido convertidos a HLS'

    def handle(self, *args, **kwargs):
        # Obtener todos los videos que no están listos para HLS
        videos = Media.objects.filter(
            file__endswith='.mp4',  # Solo videos
            is_stream_ready=False  # No procesados
        )
        
        total = videos.count()
        self.stdout.write(f'Encontrados {total} videos para procesar')
        
        for i, video in enumerate(videos, 1):
            self.stdout.write(f'Procesando video {i} de {total}: {video.file.name}')
            try:
                # Crear instancia del procesador con la ruta del archivo
                processor = VideoProcessor(video.file.path)
                # Procesar el video y actualizar el objeto Media
                result = processor.transcode_video()
                if result:
                    video.is_stream_ready = True
                    video.stream_status = 'completed'
                    video.hls_path = f'hls/{video.file.name.replace(".mp4", "")}/master.m3u8'
                    video.available_qualities = ['720p', '1080p']
                    video.duration = processor.get_video_duration()
                    video.save()
                    self.stdout.write(self.style.SUCCESS(
                        f'✓ Video {video.file.name} procesado exitosamente'
                    ))
                else:
                    self.stdout.write(self.style.ERROR(
                        f'✗ Error procesando {video.file.name}: No se pudo procesar el video'
                    ))
            except Exception as e:
                video.stream_status = 'error'
                video.error_message = str(e)
                video.save()
                self.stdout.write(self.style.ERROR(
                    f'✗ Error procesando {video.file.name}: {str(e)}'
                ))

        self.stdout.write(self.style.SUCCESS('¡Procesamiento completado!'))
