from django.db import models
from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver


# Create your models here.
class Media(models.Model):
    MEDIA_TYPES = (
        ('video', 'Video'),
        ('image', 'Imagen'),
    )

    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='media/')  # Carpeta única para videos e imágenes
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.media_type})"


# --- Eliminar archivo anterior al actualizar ---
@receiver(pre_save, sender=Media)
def delete_old_file_on_update(sender, instance, **kwargs):
    if not instance.pk:
        return  # si es nuevo no hacemos nada
    try:
        old_file = Media.objects.get(pk=instance.pk).file
    except Media.DoesNotExist:
        return
    new_file = instance.file
    if old_file and old_file != new_file:
        old_file.delete(False)


# --- Eliminar archivo al borrar registro ---
@receiver(post_delete, sender=Media)
def delete_file_on_delete(sender, instance, **kwargs):
    if instance.file:
        instance.file.delete(False)
