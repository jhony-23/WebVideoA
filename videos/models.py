from django.db import models
from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
import os
from django.conf import settings

class Media(models.Model):
    MEDIA_TYPES = (
        ('video', 'Video'),
        ('image', 'Imagen'),
    )
    
    PROCESSING_STATUS = (
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('ready', 'Listo'),
        ('failed', 'Error'),
    )

    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='')  # Carpeta única para videos e imágenes
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # Campos para streaming adaptativo
    is_stream_ready = models.BooleanField(default=False)
    stream_status = models.CharField(
        max_length=20, 
        choices=PROCESSING_STATUS,
        default='pending'
    )
    hls_path = models.CharField(max_length=255, blank=True)
    duration = models.FloatField(null=True, blank=True)
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    available_qualities = models.JSONField(default=list, blank=True)
    error_message = models.TextField(blank=True)

    def __str__(self):
        return f"{self.title} ({self.media_type})"
    
    def get_hls_manifest_url(self):
        """Retorna la URL del master playlist HLS"""
        if self.is_stream_ready and self.hls_path:
            return os.path.join(settings.MEDIA_URL, 'hls', os.path.basename(self.hls_path), 'master.m3u8')
        return None

    def get_stream_url(self):
        """Retorna la URL para reproducción, HLS si está listo, sino el archivo original"""
        if self.media_type == 'video':
            if self.is_stream_ready:
                return self.get_hls_manifest_url()
        return self.file.url


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
