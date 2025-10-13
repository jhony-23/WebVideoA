from django import forms
from .models import PerfilUsuario


class PerfilUsuarioForm(forms.ModelForm):
    """Formulario para completar perfil de usuario"""
    
    class Meta:
        model = PerfilUsuario
        fields = ['nombres', 'apellidos', 'area_trabajo', 'cargo', 'telefono_extension']
        labels = {
            'nombres': '👤 Nombres',
            'apellidos': '👤 Apellidos', 
            'area_trabajo': '🏢 Área de Trabajo',
            'cargo': '💼 Cargo o Posición',
            'telefono_extension': '📞 Teléfono/Extensión'
        }
        widgets = {
            'nombres': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Juan Pablo',
                'required': True
            }),
            'apellidos': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ej: Ixcamparic Escun',
                'required': True
            }),
            'area_trabajo': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'cargo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Analista de Sistemas'
            }),
            'telefono_extension': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 7955-2500 ext. 105'
            })
        }
        help_texts = {
            'nombres': 'Ingresa tu(s) nombre(s) completo(s)',
            'apellidos': 'Ingresa tus apellidos completos',
            'area_trabajo': 'Selecciona el área donde trabajas en ADICLA',
            'cargo': 'Tu posición o cargo específico (opcional)',
            'telefono_extension': 'Teléfono directo o extensión (opcional)'
        }