from django.contrib import admin
from .models import Media, PerfilUsuario, Proyecto, Tarea, MiembroProyecto
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = ['title', 'media_type', 'uploaded_at', 'stream_status_badge', 'preview_link']
    list_filter = ['media_type', 'stream_status', 'uploaded_at']
    search_fields = ['title']
    readonly_fields = ['stream_status', 'is_stream_ready', 'hls_path', 'duration', 
                      'width', 'height', 'available_qualities', 'error_message']
    
    def stream_status_badge(self, obj):
        """Muestra el estado del streaming con colores"""
        colors = {
            'pending': 'gray',
            'processing': 'blue',
            'ready': 'green',
            'failed': 'red'
        }
        if obj.media_type != 'video':
            return '---'
            
        color = colors.get(obj.stream_status, 'gray')
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_stream_status_display()
        )
    stream_status_badge.short_description = 'Estado'
    
    def preview_link(self, obj):
        """Link para previsualizar el video/imagen"""
        if obj.media_type == 'video' and obj.is_stream_ready:
            return format_html(
                '<a href="{}" target="_blank">Ver HLS</a> | <a href="{}" target="_blank">Ver Original</a>',
                obj.get_hls_manifest_url(),
                obj.file.url
            )
        return format_html('<a href="{}" target="_blank">Ver</a>', obj.file.url)
    preview_link.short_description = 'Preview'

    fieldsets = (
        ('Información Básica', {
            'fields': ('title', 'media_type', 'file')
        }),
        ('Estado de Streaming', {
            'fields': ('stream_status', 'is_stream_ready', 'available_qualities'),
            'classes': ('collapse',),
        }),
        ('Información Técnica', {
            'fields': ('duration', 'width', 'height', 'hls_path', 'error_message'),
            'classes': ('collapse',),
        }),
    )


# ==================== ADMIN PARA GESTIÓN DE TAREAS ====================

@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'departamento', 'puesto', 'tema_preferido', 'created_at']
    list_filter = ['departamento', 'puesto', 'tema_preferido', 'zona_horaria']
    search_fields = ['usuario__username', 'usuario__email', 'usuario__first_name', 'usuario__last_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Usuario', {
            'fields': ('usuario',)
        }),
        ('Información Personal', {
            'fields': ('foto', 'telefono', 'departamento', 'puesto', 'fecha_ingreso', 'bio')
        }),
        ('Habilidades', {
            'fields': ('habilidades',)
        }),
        ('Preferencias', {
            'fields': ('tema_preferido', 'idioma', 'zona_horaria', 'configuracion_notificaciones')
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


class MiembroProyectoInline(admin.TabularInline):
    model = MiembroProyecto
    extra = 1
    autocomplete_fields = ['usuario']


@admin.register(Proyecto)
class ProyectoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'codigo', 'estado', 'creador', 'progreso_display', 'created_at']
    list_filter = ['estado', 'visibilidad', 'created_at', 'fecha_inicio']
    search_fields = ['nombre', 'codigo', 'descripcion', 'creador__username']
    readonly_fields = ['created_at', 'updated_at', 'progreso_display']
    autocomplete_fields = ['creador']
    inlines = [MiembroProyectoInline]
    
    def progreso_display(self, obj):
        progreso = obj.get_progreso()
        color = '#10b981' if progreso >= 75 else '#f59e0b' if progreso >= 50 else '#ef4444'
        return format_html(
            '<div style="background: #f3f4f6; border-radius: 10px; height: 20px; width: 100px; position: relative;">'
            '<div style="background: {}; height: 100%; width: {}%; border-radius: 10px;"></div>'
            '<span style="position: absolute; top: 2px; left: 5px; font-size: 12px; color: #374151;">{}%</span>'
            '</div>',
            color, progreso, progreso
        )
    progreso_display.short_description = 'Progreso'
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'codigo', 'descripcion')
        }),
        ('Fechas', {
            'fields': ('fecha_inicio', 'fecha_fin_estimada', 'fecha_fin_real')
        }),
        ('Estado y Configuración', {
            'fields': ('estado', 'visibilidad', 'creador', 'color', 'icono')
        }),
        ('Estadísticas', {
            'fields': ('progreso_display',),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(Tarea)
class TareaAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'proyecto', 'estado', 'prioridad', 'creador', 'fecha_vencimiento', 'vencida_display']
    list_filter = ['estado', 'prioridad', 'proyecto', 'created_at', 'fecha_vencimiento']
    search_fields = ['titulo', 'descripcion', 'proyecto__nombre', 'creador__username']
    readonly_fields = ['created_at', 'updated_at', 'vencida_display']
    autocomplete_fields = ['creador', 'proyecto']
    filter_horizontal = ['asignados', 'dependencias']
    
    def vencida_display(self, obj):
        if obj.esta_vencida():
            return format_html('<span style="color: #ef4444; font-weight: bold;">🚨 VENCIDA</span>')
        elif obj.fecha_vencimiento:
            dias = obj.dias_para_vencimiento()
            if dias is not None:
                if dias <= 1:
                    return format_html('<span style="color: #f59e0b;">⚠️ Vence pronto</span>')
                else:
                    return format_html('<span style="color: #10b981;">✅ A tiempo</span>')
        return '---'
    vencida_display.short_description = 'Estado Vencimiento'
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('titulo', 'descripcion', 'proyecto')
        }),
        ('Asignación', {
            'fields': ('creador', 'asignados')
        }),
        ('Estado y Prioridad', {
            'fields': ('estado', 'prioridad', 'tags')
        }),
        ('Fechas', {
            'fields': ('fecha_vencimiento', 'fecha_inicio_estimada', 'fecha_inicio_real', 'fecha_completada')
        }),
        ('Tiempo', {
            'fields': ('tiempo_estimado', 'tiempo_real'),
            'classes': ('collapse',)
        }),
        ('Dependencias', {
            'fields': ('dependencias',),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at', 'vencida_display'),
            'classes': ('collapse',)
        })
    )


@admin.register(MiembroProyecto)
class MiembroProyectoAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'proyecto', 'rol', 'fecha_incorporacion', 'activo']
    list_filter = ['rol', 'activo', 'fecha_incorporacion']
    search_fields = ['usuario__username', 'proyecto__nombre']
    autocomplete_fields = ['usuario', 'proyecto']
