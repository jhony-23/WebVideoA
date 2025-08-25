from django.contrib import admin
from .models import Media  # Antes estaba 'Video'

@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = ('title', 'media_type', 'uploaded_at')
