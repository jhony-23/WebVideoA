"""
import os
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from .models import Media

# Cuando se elimina un registro, borrar también el archivo físico
@receiver(post_delete, sender=Media)
def delete_media_file(sender, instance, **kwargs):
    if instance.file and os.path.isfile(instance.file.path):
        os.remove(instance.file.path)

# Cuando se actualiza un archivo, borrar el anterior
@receiver(pre_save, sender=Media)
def replace_media_file(sender, instance, **kwargs):
    if not instance.pk:
        return  # si es un nuevo archivo, no hacemos nada

    try:
        old_file = Media.objects.get(pk=instance.pk).file
    except Media.DoesNotExist:
        return

    new_file = instance.file
    if old_file and old_file != new_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)
            
"""