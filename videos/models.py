from django.db import models
from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver

# Create your models here.

class Video(models.Model):
    title = models.CharField(max_length=200)
    videofile = models.FileField(upload_to='videos/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

# --- Eliminar archivo anterior al actualizar ---
@receiver(pre_save, sender=Video)
def delete_old_file_on_update(sender, instance, **kwargs):
    if not instance.pk:
        return  # si es nuevo no hacemos nada
    try:
        old_file = Video.objects.get(pk=instance.pk).videofile
    except Video.DoesNotExist:
        return
    new_file = instance.videofile
    if old_file and old_file != new_file:
        old_file.delete(False)


# --- Eliminar archivo al borrar registro ---
@receiver(post_delete, sender=Video)
def delete_file_on_delete(sender, instance, **kwargs):
    if instance.videofile:
        instance.videofile.delete(False)