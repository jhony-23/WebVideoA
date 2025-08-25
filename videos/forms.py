from django import forms
from .models import Video

class VideoForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ('title', 'videofile')  # Usa los nombres del modelo
        labels = {
            'title': 'Título',
            'videofile': 'Cargar video',
        }