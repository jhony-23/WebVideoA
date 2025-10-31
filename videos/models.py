from django.db import models
from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
import os
import json
import uuid
from pathlib import Path
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
from django.urls import reverse


def media_upload_to(instance, filename):
    """Generate a structured upload path inside MEDIA_ROOT/uploads."""
    timestamp = timezone.now()
    base_name = Path(filename).stem
    extension = Path(filename).suffix
    safe_name = slugify(base_name) or 'media'
    unique_suffix = uuid.uuid4().hex[:8]
    new_name = f"{safe_name}-{unique_suffix}{extension}" if extension else f"{safe_name}-{unique_suffix}"
    return os.path.join(
        'uploads',
        timestamp.strftime('%Y'),
        timestamp.strftime('%m'),
        new_name
    )

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
    file = models.FileField(upload_to=media_upload_to)  # Carpeta única para videos e imágenes
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


# ==================== MODELOS PARA GESTIÓN DE TAREAS ====================


class Proyecto(models.Model):
    """Modelo para gestión de proyectos"""
    ESTADOS_PROYECTO = [
        ('activo', 'Activo'),
        ('pausado', 'Pausado'),
        ('completado', 'Completado'),
        ('cancelado', 'Cancelado'),
    ]
    
    TIPOS_VISIBILIDAD = [
        ('publico', 'Público'),
        ('privado', 'Privado'),
    ]
    
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    codigo = models.CharField(max_length=20, unique=True, help_text="Código único del proyecto")
    
    # Fechas
    fecha_inicio = models.DateField()
    fecha_fin_estimada = models.DateField(null=True, blank=True)
    fecha_fin_real = models.DateField(null=True, blank=True)
    
    # Estado y visibilidad
    estado = models.CharField(max_length=20, choices=ESTADOS_PROYECTO, default='activo')
    visibilidad = models.CharField(max_length=20, choices=TIPOS_VISIBILIDAD, default='privado')
    
    # Usuario que creó el proyecto (automáticamente admin del proyecto)
    creador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='proyectos_creados')
    
    # Configuración
    color = models.CharField(max_length=7, default='#3498db', help_text="Color en formato hex")
    icono = models.CharField(max_length=50, default='📋', help_text="Emoji o icono")
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'proyecto'
        verbose_name = 'Proyecto'
        verbose_name_plural = 'Proyectos'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
    
    def get_absolute_url(self):
        return reverse('proyecto_detalle', kwargs={'pk': self.pk})
    
    def get_progreso(self):
        """Calcula el progreso del proyecto basado en tareas completadas"""
        total_tareas = self.tareas.count()
        if total_tareas == 0:
            return 0
        tareas_completadas = self.tareas.filter(estado='completada').count()
        return round((tareas_completadas / total_tareas) * 100, 1)
    
    def get_total_tareas(self):
        return self.tareas.count()
    
    def get_tareas_completadas(self):
        return self.tareas.filter(estado='completada').count()
    
    def get_tareas_pendientes(self):
        return self.tareas.exclude(estado='completada').count()
    
    def get_miembros(self):
        """Retorna todos los miembros del proyecto"""
        return User.objects.filter(
            models.Q(proyectos_creados=self) |
            models.Q(miembro_proyectos__proyecto=self)
        ).distinct()
    
    def es_admin(self, usuario):
        """Verifica si el usuario es administrador del proyecto"""
        if usuario == self.creador:
            return True
        return self.miembros.filter(usuario=usuario, rol='admin').exists()
    
    def es_jefe_proyecto(self, usuario):
        """Verifica si el usuario es jefe del proyecto"""
        return self.miembros.filter(usuario=usuario, rol='jefe').exists()
    
    def puede_gestionar(self, usuario):
        """Verifica si el usuario puede gestionar el proyecto (admin o jefe)"""
        return self.es_admin(usuario) or self.es_jefe_proyecto(usuario)


class MiembroProyecto(models.Model):
    """Relación entre usuarios y proyectos con roles específicos"""
    ROLES = [
        ('usuario', 'Usuario'),
        ('jefe', 'Jefe de Proyecto'),
        ('admin', 'Administrador'),
    ]
    
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='miembros')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='miembro_proyectos')
    rol = models.CharField(max_length=20, choices=ROLES, default='usuario')
    
    # Metadatos
    fecha_incorporacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'miembro_proyecto'
        verbose_name = 'Miembro de Proyecto'
        verbose_name_plural = 'Miembros de Proyecto'
        unique_together = ['proyecto', 'usuario']
    
    def __str__(self):
        return f"{self.usuario.get_full_name() or self.usuario.username} - {self.proyecto.nombre} ({self.get_rol_display()})"


class Tarea(models.Model):
    """Modelo para gestión de tareas"""
    ESTADOS_TAREA = [
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En Proceso'),
        ('en_revision', 'En Revisión'),
        ('completada', 'Completada'),
    ]
    
    PRIORIDADES = [
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('critica', 'Crítica'),
    ]
    
    # Información básica
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='tareas')
    
    # Asignación
    creador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tareas_creadas')
    asignados = models.ManyToManyField(User, related_name='tareas_asignadas', blank=True)
    
    # Estado y prioridad
    estado = models.CharField(max_length=20, choices=ESTADOS_TAREA, default='pendiente')
    prioridad = models.CharField(max_length=20, choices=PRIORIDADES, default='media')
    
    # Fechas
    fecha_vencimiento = models.DateTimeField(null=True, blank=True)
    fecha_inicio_estimada = models.DateField(null=True, blank=True)
    fecha_inicio_real = models.DateTimeField(null=True, blank=True)
    fecha_completada = models.DateTimeField(null=True, blank=True)
    
    # Estimaciones
    tiempo_estimado = models.DurationField(null=True, blank=True, help_text="Tiempo estimado en formato HH:MM:SS")
    tiempo_real = models.DurationField(null=True, blank=True)
    
    # Dependencias
    dependencias = models.ManyToManyField('self', blank=True, symmetrical=False, related_name='dependientes')
    
    # Configuración
    tags = models.CharField(max_length=500, blank=True, help_text="Etiquetas separadas por comas")
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tarea'
        verbose_name = 'Tarea'
        verbose_name_plural = 'Tareas'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.titulo} - {self.proyecto.codigo}"
    
    def get_absolute_url(self):
        return reverse('tarea_detalle', kwargs={'pk': self.pk})
    
    def get_tags_list(self):
        """Retorna lista de tags"""
        if self.tags:
            return [t.strip() for t in self.tags.split(',') if t.strip()]
        return []
    
    def esta_vencida(self):
        """Verifica si la tarea está vencida"""
        if self.fecha_vencimiento and self.estado != 'completada':
            return timezone.now() > self.fecha_vencimiento
        return False
    
    def dias_para_vencimiento(self):
        """Calcula días hasta el vencimiento"""
        if self.fecha_vencimiento:
            delta = self.fecha_vencimiento - timezone.now()
            return delta.days
        return None
    
    def puede_iniciar(self):
        """Verifica si la tarea puede iniciarse (dependencias completadas)"""
        return not self.dependencias.exclude(estado='completada').exists()
    
    def get_progreso_dependencias(self):
        """Calcula progreso de dependencias"""
        total = self.dependencias.count()
        if total == 0:
            return 100
        completadas = self.dependencias.filter(estado='completada').count()
        return round((completadas / total) * 100, 1)


class ArchivoProyecto(models.Model):
    """Archivos adjuntos a proyectos"""
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='archivos')
    archivo = models.FileField(upload_to='proyectos/archivos/%Y/%m/')
    nombre_original = models.CharField(max_length=255)
    descripcion = models.CharField(max_length=500, blank=True)
    subido_por = models.ForeignKey(User, on_delete=models.CASCADE, related_name='archivos_proyecto_subidos')
    
    # Metadatos
    tamaño = models.PositiveIntegerField(help_text="Tamaño en bytes")
    tipo_archivo = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'archivo_proyecto'
        verbose_name = 'Archivo de Proyecto'
        verbose_name_plural = 'Archivos de Proyecto'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.nombre_original} - {self.proyecto.nombre}"
    
    def get_tamaño_legible(self):
        """Convierte bytes a formato legible"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.tamaño < 1024.0:
                return f"{self.tamaño:.1f} {unit}"
            self.tamaño /= 1024.0
        return f"{self.tamaño:.1f} TB"
    
    def get_icono(self):
        """Retorna emoji según tipo de archivo"""
        if 'image' in self.tipo_archivo.lower():
            return '🖼️'
        elif 'pdf' in self.tipo_archivo.lower():
            return '📄'
        elif 'word' in self.tipo_archivo.lower() or 'doc' in self.tipo_archivo.lower():
            return '📝'
        elif 'excel' in self.tipo_archivo.lower() or 'sheet' in self.tipo_archivo.lower():
            return '📊'
        elif 'powerpoint' in self.tipo_archivo.lower() or 'presentation' in self.tipo_archivo.lower():
            return '📋'
        else:
            return '📎'


class ArchivoTarea(models.Model):
    """Archivos adjuntos a tareas"""
    tarea = models.ForeignKey(Tarea, on_delete=models.CASCADE, related_name='archivos')
    archivo = models.FileField(upload_to='tareas/archivos/%Y/%m/')
    nombre_original = models.CharField(max_length=255)
    descripcion = models.CharField(max_length=500, blank=True)
    subido_por = models.ForeignKey(User, on_delete=models.CASCADE, related_name='archivos_tarea_subidos')
    
    # Metadatos
    tamaño = models.PositiveIntegerField(help_text="Tamaño en bytes")
    tipo_archivo = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'archivo_tarea'
        verbose_name = 'Archivo de Tarea'
        verbose_name_plural = 'Archivos de Tarea'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.nombre_original} - {self.tarea.titulo}"
    
    def get_tamaño_legible(self):
        """Convierte bytes a formato legible"""
        tamaño = self.tamaño
        for unit in ['B', 'KB', 'MB', 'GB']:
            if tamaño < 1024.0:
                return f"{tamaño:.1f} {unit}"
            tamaño /= 1024.0
        return f"{tamaño:.1f} TB"
    
    def get_icono(self):
        """Retorna emoji según tipo de archivo"""
        if 'image' in self.tipo_archivo.lower():
            return '🖼️'
        elif 'pdf' in self.tipo_archivo.lower():
            return '📄'
        elif 'word' in self.tipo_archivo.lower() or 'doc' in self.tipo_archivo.lower():
            return '📝'
        elif 'excel' in self.tipo_archivo.lower() or 'sheet' in self.tipo_archivo.lower():
            return '📊'
        elif 'powerpoint' in self.tipo_archivo.lower() or 'presentation' in self.tipo_archivo.lower():
            return '📋'
        else:
            return '📎'


class ComentarioProyecto(models.Model):
    """Comentarios en proyectos"""
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='comentarios')
    autor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comentarios_proyecto')
    contenido = models.TextField()
    
    # Para hilos de comentarios
    comentario_padre = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='respuestas')
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'comentario_proyecto'
        verbose_name = 'Comentario de Proyecto'
        verbose_name_plural = 'Comentarios de Proyecto'
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comentario de {self.autor.username} en {self.proyecto.nombre}"
    
    def get_respuestas(self):
        """Obtiene las respuestas ordenadas"""
        return self.respuestas.all().order_by('created_at')
    
    def es_respuesta(self):
        """Verifica si es una respuesta a otro comentario"""
        return self.comentario_padre is not None


class ComentarioTarea(models.Model):
    """Comentarios en tareas"""
    tarea = models.ForeignKey(Tarea, on_delete=models.CASCADE, related_name='comentarios')
    autor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comentarios_tarea')
    contenido = models.TextField()
    
    # Para hilos de comentarios
    comentario_padre = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='respuestas')
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'comentario_tarea'
        verbose_name = 'Comentario de Tarea'
        verbose_name_plural = 'Comentarios de Tarea'
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comentario de {self.autor.username} en {self.tarea.titulo}"
    
    def get_respuestas(self):
        """Obtiene las respuestas ordenadas"""
        return self.respuestas.all().order_by('created_at')
    
    def es_respuesta(self):
        """Verifica si es una respuesta a otro comentario"""
        return self.comentario_padre is not None


class ArchivoComentario(models.Model):
    """Archivos adjuntos a comentarios"""
    comentario_proyecto = models.ForeignKey(ComentarioProyecto, on_delete=models.CASCADE, null=True, blank=True, related_name='archivos')
    comentario_tarea = models.ForeignKey(ComentarioTarea, on_delete=models.CASCADE, null=True, blank=True, related_name='archivos')
    
    archivo = models.FileField(upload_to='comentarios/archivos/%Y/%m/')
    nombre_original = models.CharField(max_length=255)
    subido_por = models.ForeignKey(User, on_delete=models.CASCADE, related_name='archivos_comentario_subidos')
    
    # Metadatos
    tamaño = models.PositiveIntegerField(help_text="Tamaño en bytes")
    tipo_archivo = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'archivo_comentario'
        verbose_name = 'Archivo de Comentario'
        verbose_name_plural = 'Archivos de Comentario'
        ordering = ['-created_at']
    
    def __str__(self):
        if self.comentario_proyecto:
            return f"{self.nombre_original} - Comentario Proyecto"
        else:
            return f"{self.nombre_original} - Comentario Tarea"
    
    def get_tamaño_legible(self):
        """Convierte bytes a formato legible"""
        tamaño = self.tamaño
        for unit in ['B', 'KB', 'MB', 'GB']:
            if tamaño < 1024.0:
                return f"{tamaño:.1f} {unit}"
            tamaño /= 1024.0
        return f"{tamaño:.1f} TB"
    
    def get_icono(self):
        """Retorna emoji según tipo de archivo"""
        if 'image' in self.tipo_archivo.lower():
            return '🖼️'
        elif 'pdf' in self.tipo_archivo.lower():
            return '📄'
        elif 'word' in self.tipo_archivo.lower() or 'doc' in self.tipo_archivo.lower():
            return '📝'
        elif 'excel' in self.tipo_archivo.lower() or 'sheet' in self.tipo_archivo.lower():
            return '📊'
        elif 'powerpoint' in self.tipo_archivo.lower() or 'presentation' in self.tipo_archivo.lower():
            return '📋'
        else:
            return '📎'


class PerfilUsuario(models.Model):
    """Perfil extendido para usuarios de ADICLA"""
    AREAS_TRABAJO = [
        ('informatica', 'Informática/IT'),
        ('contabilidad', 'Contabilidad'),
        ('administracion', 'Administración'),
        ('gerencia', 'Gerencia'),
        ('mercadotecnia', 'Mercadotecnia'),
        ('creditos', 'Créditos'),
        ('recursos_humanos', 'Recursos Humanos'),
        ('legal', 'Legal'),
        ('auditoria', 'Auditoría'),
        ('secretaria', 'Secretaría'),
        ('otro', 'Otro')
    ]
    
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    
    # Información personal
    nombres = models.CharField(max_length=100, verbose_name="Nombres")
    apellidos = models.CharField(max_length=100, verbose_name="Apellidos")
    
    # Información laboral
    area_trabajo = models.CharField(max_length=50, choices=AREAS_TRABAJO, verbose_name="Área de Trabajo")
    cargo = models.CharField(max_length=100, blank=True, verbose_name="Cargo/Posición")
    telefono_extension = models.CharField(max_length=20, blank=True, verbose_name="Teléfono/Extensión")
    
    # Configuración de perfil
    perfil_completado = models.BooleanField(default=False)
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'perfil_usuario'
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuario'
    
    def __str__(self):
        return f"{self.get_nombre_completo()} - {self.get_area_trabajo_display()}"
    
    def get_nombre_completo(self):
        """Retorna nombre completo del usuario"""
        return f"{self.nombres} {self.apellidos}".strip()
    
    def get_iniciales(self):
        """Retorna iniciales del usuario"""
        nombres_parts = self.nombres.split()
        apellidos_parts = self.apellidos.split()
        
        iniciales = ""
        if nombres_parts:
            iniciales += nombres_parts[0][0].upper()
        if apellidos_parts:
            iniciales += apellidos_parts[0][0].upper()
        
        return iniciales or "U"


# Señales para crear perfil automáticamente
@receiver(models.signals.post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    """Crear perfil automáticamente al crear usuario"""
    if created and not hasattr(instance, 'perfil'):
        PerfilUsuario.objects.create(usuario=instance)

@receiver(models.signals.post_save, sender=User)
def guardar_perfil_usuario(sender, instance, **kwargs):
    """Guardar perfil cuando se guarda usuario"""
    if hasattr(instance, 'perfil'):
        instance.perfil.save()
