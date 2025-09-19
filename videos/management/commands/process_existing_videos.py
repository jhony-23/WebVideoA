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
                # Crear instancia del procesador
                processor = VideoProcessor(video)
                # Procesar el video
                processor.process()
                self.stdout.write(self.style.SUCCESS(
                    f'✓ Video {video.file.name} procesado exitosamente'
                ))
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f'✗ Error procesando {video.file.name}: {str(e)}'
                ))

        self.stdout.write(self.style.SUCCESS('¡Procesamiento completado!'))
