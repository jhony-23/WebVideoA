import time
import os
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
                file__endswith='.mp4',
                is_stream_ready=False,
                stream_status='pending'
            ).order_by('uploaded_at')[:1]  # Procesar uno a la vez
            
            if pending_videos:
                video = pending_videos[0]
                self.stdout.write(f'Procesando video: {video.file.name}')
                
                try:
                    # Marcar como en procesamiento
                    video.stream_status = 'processing'
                    video.save()
                    
                    # Procesar el video
                    input_path = os.path.join(settings.MEDIA_ROOT, str(video.file))
                    processor = VideoProcessor(input_path)
                    result = processor.transcode_to_hls()
                    
                    if result:
                        # Actualizar metadatos
                        video_info = processor._get_video_info()
                        duration = float(video_info['streams'][0].get('duration', 0))
                        
                        # Determinar calidades generadas
                        available_qualities = []
                        for quality in ['720p', '1080p', '480p']:
                            if os.path.exists(os.path.join(processor.output_dir, f'{quality}.m3u8')):
                                available_qualities.append(quality)
                        
                        # Actualizar el video
                        video.is_stream_ready = True
                        video.stream_status = 'completed'
                        video.hls_path = f'hls/{video.file.name.replace(".mp4", "")}/master.m3u8'
                        video.available_qualities = available_qualities
                        video.duration = duration
                        video.save()
                        
                        self.stdout.write(self.style.SUCCESS(
                            f'✓ Video {video.file.name} procesado exitosamente'
                        ))
                    else:
                        video.stream_status = 'error'
                        video.error_message = 'Error en la transcodificación'
                        video.save()
                        
                except Exception as e:
                    video.stream_status = 'error'
                    video.error_message = str(e)
                    video.save()
                    self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
            
            # Esperar antes de la siguiente verificación
            time.sleep(10)  # 10 segundos entre verificaciones