import os
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from .models import Media

# Cuando se elimina un registro, borrar también el archivo físico
@receiver(post_delete, sender=Media)
def delete_video_file(sender, instance, **kwargs):
    if instance.videofile and os.path.isfile(instance.videofile.path):
        os.remove(instance.videofile.path)

# Cuando se actualiza un video, borrar el archivo anterior
@receiver(pre_save, sender=Media)
def replace_video_file(sender, instance, **kwargs):
    if not instance.pk:
        return  # si es un video nuevo, no hace nada

    try:
        old_file = Media.objects.get(pk=instance.pk).videofile
    except Media.DoesNotExist:
        return

    new_file = instance.videofile
    if old_file and old_file != new_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)
