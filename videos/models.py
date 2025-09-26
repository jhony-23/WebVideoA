from django.db import models
from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
import os
import json
from django.conf import settings
from django.utils import timezone

class PlaylistState(models.Model):
    """Estado global de la reproducción sincronizada"""
    is_active = models.BooleanField(default=False)
    current_media_id = models.IntegerField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    playlist_data = models.JSONField(default=list, blank=True)  # Lista de IDs shuffled
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'playlist_state'
    
    @classmethod
    def get_current_state(cls):
        """Obtiene o crea el estado actual"""
        state, created = cls.objects.get_or_create(pk=1)
        return state
    
    def get_current_media(self):
        """Obtiene el media actual basado en el tiempo transcurrido y duración"""
        if not self.playlist_data or not self.is_active or not self.started_at:
            return None
        
        # Calcular qué elemento debería estar reproduciéndose ahora
        total_elapsed = int((timezone.now() - self.started_at).total_seconds())
        current_time = 0
        
        for i, media_id in enumerate(self.playlist_data):
            try:
                media = Media.objects.get(id=media_id)
                
                # Duración del elemento actual
                if media.media_type == 'image':
                    duration = 10  # Imágenes 10 segundos
                else:
                    duration = int(media.duration) if media.duration else 30
                
                # Si estamos dentro del tiempo de este elemento
                if total_elapsed < current_time + duration:
                    # Actualizar current_media_id si cambió
                    if self.current_media_id != media_id:
                        self.current_media_id = media_id
                        self.save()
                    return media
                
                current_time += duration
                
            except Media.DoesNotExist:
                continue
        
        # Si llegamos aquí, la playlist terminó - reiniciar
        if self.playlist_data:
            first_media_id = self.playlist_data[0]
            try:
                first_media = Media.objects.get(id=first_media_id)
                self.started_at = timezone.now()  # Reiniciar tiempo
                self.current_media_id = first_media_id
                self.save()
                return first_media
            except Media.DoesNotExist:
                pass
        
        return None
    
    def get_elapsed_time(self):
        """Calcula tiempo transcurrido del media actual en segundos"""
        if not self.started_at or not self.is_active or not self.playlist_data:
            return 0
        
        total_elapsed = int((timezone.now() - self.started_at).total_seconds())
        current_time = 0
        
        for media_id in self.playlist_data:
            try:
                media = Media.objects.get(id=media_id)
                
                # Duración del elemento
                if media.media_type == 'image':
                    duration = 10
                else:
                    duration = int(media.duration) if media.duration else 30
                
                # Si es el elemento actual, devolver tiempo dentro de él
                if total_elapsed < current_time + duration:
                    return total_elapsed - current_time
                
                current_time += duration
                
            except Media.DoesNotExist:
                continue
        
        return 0

    def get_current_index(self):
        """Obtiene el índice actual en la playlist"""
        if not self.playlist_data or not self.current_media_id:
            return 0
        
        try:
            return self.playlist_data.index(self.current_media_id)
        except ValueError:
            return 0

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
        if not self.hls_path:
            return None
        # Aceptar también antiguos estados 'completed'
        if not (self.is_stream_ready or self.stream_status in ('ready', 'completed')):
            return None

        raw = self.hls_path.strip('/')
        # Si accidentalmente incluye MEDIA_URL, removerlo
        media_url_clean = settings.MEDIA_URL.strip('/')
        if raw.startswith(media_url_clean):
            raw = raw[len(media_url_clean):].lstrip('/')
        # Si termina en master.m3u8 (estado antiguo) quitarlo para evitar duplicación
        if raw.endswith('master.m3u8'):
            raw = raw[:-len('master.m3u8')].rstrip('/')
        # Ahora raw debería ser 'hls/<basename>'
        return f"{settings.MEDIA_URL}{raw}/master.m3u8"

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
