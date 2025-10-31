from django.core.management.base import BaseCommand
from django.conf import settings
from videos.models import Media
from videos.utils import VideoProcessor
from pathlib import Path
import shutil

class Command(BaseCommand):
    help = 'Procesa todos los videos existentes que no han sido convertidos a HLS'

    def handle(self, *args, **kwargs):
        self.stdout.write(f'MEDIA_ROOT configurado en: {settings.MEDIA_ROOT}')
        
        # Obtener todos los videos que no están listos para HLS
        videos = Media.objects.filter(
            media_type='video',  # Solo videos
            is_stream_ready=False  # No procesados
        )
        
        total = videos.count()
        self.stdout.write(f'Encontrados {total} videos para procesar')
        
        # Mostrar información de cada video en la base de datos
        self.stdout.write('\nVideos en la base de datos:')
        for v in videos:
            self.stdout.write(f'- {v.file.name} (Campo file completo: {v.file})')
        
        for i, video in enumerate(videos, 1):
            self.stdout.write(f'Procesando video {i} de {total}: {video.file.name}')
            try:
                # Construir la ruta completa al archivo
                input_path = Path(video.file.path)
                
                # Verificar que el archivo existe
                if not input_path.exists():
                    raise FileNotFoundError(f"El archivo no existe en: {input_path}")
                
                self.stdout.write(f'Ruta del archivo: {input_path}')
                
                # Crear instancia del procesador con la ruta del archivo
                processor = VideoProcessor(input_path, media_id=video.pk)
                previous_hls_path = video.hls_path
                # Procesar el video y actualizar el objeto Media
                success, metadata = processor.transcode_to_hls()
                if success:
                    # Actualizar el objeto Media
                    video.is_stream_ready = True
                    video.stream_status = 'ready'
                    video.hls_path = metadata.get('relative_output_dir')
                    video.available_qualities = metadata.get('qualities', [])
                    video.duration = metadata.get('duration') or 0.0
                    video.width = metadata.get('width')
                    video.height = metadata.get('height')
                    video.error_message = ''
                    video.save()
                    new_hls_path = metadata.get('relative_output_dir')
                    if previous_hls_path and new_hls_path and previous_hls_path != new_hls_path:
                        old_dir = Path(settings.MEDIA_ROOT) / previous_hls_path
                        shutil.rmtree(old_dir, ignore_errors=True)
                    self.stdout.write(self.style.SUCCESS(
                        f'✓ Video {video.file.name} procesado exitosamente'
                    ))
                else:
                    video.stream_status = 'failed'
                    video.is_stream_ready = False
                    video.available_qualities = []
                    video.error_message = metadata.get('error', 'No se pudo procesar el video')
                    video.save(update_fields=['stream_status', 'is_stream_ready', 'available_qualities', 'error_message'])
                    self.stdout.write(self.style.ERROR(
                        f'✗ Error procesando {video.file.name}: {video.error_message}'
                    ))
            except Exception as e:
                video.stream_status = 'error'
                video.error_message = str(e)
                video.save()
                self.stdout.write(self.style.ERROR(
                    f'✗ Error procesando {video.file.name}: {str(e)}'
                ))

        self.stdout.write(self.style.SUCCESS('¡Procesamiento completado!'))
