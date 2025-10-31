import os
import shutil
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.conf import settings
from .models import Media
from .utils import VideoProcessor
import threading
from pathlib import Path

# Cuando se elimina un registro, borrar también el archivo físico
@receiver(post_delete, sender=Media)
def delete_media_file(sender, instance, **kwargs):
    if instance.file and os.path.isfile(instance.file.path):
        os.remove(instance.file.path)
        # Borrar también los archivos HLS si existen
        if instance.hls_path:
            hls_dir = os.path.join(settings.MEDIA_ROOT, instance.hls_path)
            if os.path.exists(hls_dir):
                for root, dirs, files in os.walk(hls_dir, topdown=False):
                    for name in files:
                        os.remove(os.path.join(root, name))
                    for name in dirs:
                        os.rmdir(os.path.join(root, name))
                os.rmdir(hls_dir)

# Cuando se actualiza un archivo, borrar el anterior
@receiver(pre_save, sender=Media)
def replace_media_file(sender, instance, **kwargs):
    if not instance.pk:
        return  # si es un nuevo archivo, no hacemos nada

    try:
        old_instance = Media.objects.get(pk=instance.pk)
        old_file = old_instance.file
    except Media.DoesNotExist:
        return

    new_file = instance.file
    if old_file and old_file != new_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)
        # Borrar también los archivos HLS si existen
        if old_instance.hls_path:
            hls_dir = os.path.join(settings.MEDIA_ROOT, old_instance.hls_path)
            if os.path.exists(hls_dir):
                for root, dirs, files in os.walk(hls_dir, topdown=False):
                    for name in files:
                        os.remove(os.path.join(root, name))
                    for name in dirs:
                        os.rmdir(os.path.join(root, name))
                os.rmdir(hls_dir)

def process_video(media_instance):
    """Procesa un video en segundo plano"""
    try:
        previous_hls_path = media_instance.hls_path
        ffmpeg_bin_dir = os.getenv('FFMPEG_BIN_DIR')
        if ffmpeg_bin_dir:
            os.environ['PATH'] = f"{ffmpeg_bin_dir}{os.pathsep}" + os.environ.get('PATH', '')

        processor = VideoProcessor(media_instance.file.path, media_id=media_instance.pk)
        success, metadata = processor.transcode_to_hls()

        if success:
            new_hls_path = metadata.get('relative_output_dir')
            if previous_hls_path and new_hls_path and previous_hls_path != new_hls_path:
                old_dir = Path(settings.MEDIA_ROOT) / previous_hls_path
                if old_dir.exists() and old_dir.is_dir():
                    shutil.rmtree(old_dir, ignore_errors=True)

            Media.objects.filter(pk=media_instance.pk).update(
                is_stream_ready=True,
                stream_status='ready',
                hls_path=new_hls_path,
                available_qualities=metadata.get('qualities', []),
                duration=metadata.get('duration') or 0.0,
                width=metadata.get('width'),
                height=metadata.get('height'),
                error_message=''
            )
        else:
            Media.objects.filter(pk=media_instance.pk).update(
                stream_status='failed',
                is_stream_ready=False,
                error_message=metadata.get('error', 'Error en la transcodificación'),
                available_qualities=[]
            )
    except Exception as e:
        Media.objects.filter(pk=media_instance.pk).update(
            stream_status='failed',
            is_stream_ready=False,
            error_message=str(e),
            available_qualities=[]
        )

# Cuando se guarda un nuevo video, iniciar el procesamiento
@receiver(post_save, sender=Media)
def handle_video_upload(sender, instance, created, **kwargs):
    if created and instance.media_type == 'video':
        # Iniciar procesamiento en segundo plano
        instance.stream_status = 'processing'
        instance.save(update_fields=['stream_status'])
        thread = threading.Thread(target=process_video, args=(instance,))
        thread.start()