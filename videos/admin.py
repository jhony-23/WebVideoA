from django.contrib import admin
from .models import Media
from django.utils.html import format_html

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
