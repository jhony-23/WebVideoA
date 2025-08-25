from django import forms
from .models import Media

class CustomClearableFileInput(forms.ClearableFileInput):
    template_with_initial = (
        '%(initial_text)s: %(initial)s <br>'
        '%(input_text)s: %(input)s'
    )
    initial_text = 'Actualmente'
    input_text = 'Reemplazar'
    # Permitimos solo ciertos tipos de archivo (videos e imágenes)
    def __init__(self, attrs=None):
        super().__init__(attrs)
        self.attrs.update({'accept': 'video/*,image/*'})

class MediaForm(forms.ModelForm):
    class Meta:
        model = Media
        fields = ('title', 'file', 'media_type')
        labels = {
            'title': 'Título',
            'file': 'Cargar archivo',
            'media_type': 'Tipo de archivo',
        }
        widgets = {
            'file': CustomClearableFileInput(),
        }
