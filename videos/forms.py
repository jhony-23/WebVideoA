from django import forms
from .models import Video

class CustomClearableFileInput(forms.ClearableFileInput):
    template_with_initial = (
        '%(initial_text)s: %(initial)s <br>'
        '%(input_text)s: %(input)s'
    )
    initial_text = 'Actualmente'
    input_text = 'Reemplazar'

class VideoForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ('title', 'videofile')
        labels = {
            'title': 'Título',
            'videofile': 'Cargar video',
        }
        widgets = {
            'videofile': CustomClearableFileInput,
        }