import os
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.conf import settings
from .models import Media
from .utils import VideoProcessor
import threading

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
        # Asegurar que FFmpeg esté en el PATH
        import os
        os.environ["PATH"] = r"C:\Program Files\ffmpeg\bin;" + os.environ["PATH"]
        
        processor = VideoProcessor(media_instance.file.path)
        if processor.transcode_to_hls():
            # Actualizar el modelo con la información del HLS
            Media.objects.filter(pk=media_instance.pk).update(
                is_stream_ready=True,
                stream_status='ready',
                hls_path=os.path.relpath(processor.output_dir, settings.MEDIA_ROOT),
                available_qualities=list(processor.QUALITY_PROFILES.keys())
            )
        else:
            Media.objects.filter(pk=media_instance.pk).update(
                stream_status='failed',
                error_message='Error en la transcodificación'
            )
    except Exception as e:
        Media.objects.filter(pk=media_instance.pk).update(
            stream_status='failed',
            error_message=str(e)
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