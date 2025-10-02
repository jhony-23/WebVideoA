from django import forms
from django.contrib.auth.models import User
from django.db import models
from .models import Media, Proyecto, Tarea, MiembroProyecto

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


# ==================== FORMULARIOS PARA GESTIÓN DE TAREAS ====================

class ProyectoForm(forms.ModelForm):
    """Formulario para crear y editar proyectos"""
    
    class Meta:
        model = Proyecto
        fields = [
            'nombre', 'codigo', 'descripcion', 'fecha_inicio', 
            'fecha_fin_estimada', 'estado', 'visibilidad', 'color', 'icono'
        ]
        labels = {
            'nombre': 'Nombre del Proyecto',
            'codigo': 'Código del Proyecto',
            'descripcion': 'Descripción',
            'fecha_inicio': 'Fecha de Inicio',
            'fecha_fin_estimada': 'Fecha de Finalización Estimada',
            'estado': 'Estado del Proyecto',
            'visibilidad': 'Visibilidad',
            'color': 'Color del Proyecto',
            'icono': 'Icono/Emoji',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Sistema de Inventario'
            }),
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: SINV-2025',
                'maxlength': 20
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe los objetivos y alcance del proyecto...'
            }),
            'fecha_inicio': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'fecha_fin_estimada': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'visibilidad': forms.Select(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
            'icono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '📋 (Emoji o icono)',
                'maxlength': 50
            }),
        }
        help_texts = {
            'codigo': 'Código único que identifica el proyecto',
            'fecha_fin_estimada': 'Opcional - Puedes definirla más adelante',
            'visibilidad': 'Público: Visible para todos. Privado: Solo miembros',
            'icono': 'Agrega un emoji o icono que represente el proyecto',
        }

    def clean_codigo(self):
        """Validar que el código sea único"""
        codigo = self.cleaned_data.get('codigo')
        if codigo:
            codigo = codigo.upper().strip()
            # Verificar unicidad
            qs = Proyecto.objects.filter(codigo=codigo)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError('Ya existe un proyecto con este código.')
        return codigo

    def clean(self):
        """Validaciones adicionales"""
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin_estimada = cleaned_data.get('fecha_fin_estimada')
        
        if fecha_inicio and fecha_fin_estimada:
            if fecha_fin_estimada <= fecha_inicio:
                raise forms.ValidationError('La fecha de finalización debe ser posterior a la fecha de inicio.')
        
        return cleaned_data


class TareaForm(forms.ModelForm):
    """Formulario para crear y editar tareas"""
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.proyecto_inicial = kwargs.pop('proyecto_inicial', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar proyectos a los que el usuario tiene acceso
        if self.user:
            proyectos_accesibles = Proyecto.objects.filter(
                models.Q(creador=self.user) | models.Q(miembros__usuario=self.user)
            ).distinct()
            self.fields['proyecto'].queryset = proyectos_accesibles
            
            # Filtrar usuarios asignables (miembros de proyectos accesibles)
            usuarios_asignables = User.objects.filter(
                models.Q(proyectos_creados__in=proyectos_accesibles) |
                models.Q(miembro_proyectos__proyecto__in=proyectos_accesibles)
            ).distinct()
            self.fields['asignados'].queryset = usuarios_asignables
            
            # Filtrar dependencias a tareas del mismo usuario
            tareas_disponibles = Tarea.objects.filter(
                models.Q(creador=self.user) | models.Q(asignados=self.user)
            ).distinct()
            if self.instance.pk:
                tareas_disponibles = tareas_disponibles.exclude(pk=self.instance.pk)
            self.fields['dependencias'].queryset = tareas_disponibles
        
        # Si hay proyecto inicial, establecerlo
        if self.proyecto_inicial:
            self.fields['proyecto'].initial = self.proyecto_inicial
            self.fields['proyecto'].widget.attrs['readonly'] = True
    
    class Meta:
        model = Tarea
        fields = [
            'titulo', 'descripcion', 'proyecto', 'asignados', 'estado', 
            'prioridad', 'fecha_vencimiento', 'fecha_inicio_estimada',
            'tiempo_estimado', 'dependencias', 'tags'
        ]
        labels = {
            'titulo': 'Título de la Tarea',
            'descripcion': 'Descripción Detallada',
            'proyecto': 'Proyecto',
            'asignados': 'Asignados a la Tarea',
            'estado': 'Estado Actual',
            'prioridad': 'Prioridad',
            'fecha_vencimiento': 'Fecha de Vencimiento',
            'fecha_inicio_estimada': 'Fecha de Inicio Estimada',
            'tiempo_estimado': 'Tiempo Estimado',
            'dependencias': 'Tareas de las que Depende',
            'tags': 'Etiquetas',
        }
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Implementar login de usuarios'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Describe detalladamente qué debe hacerse...'
            }),
            'proyecto': forms.Select(attrs={'class': 'form-control'}),
            'asignados': forms.SelectMultiple(attrs={
                'class': 'form-control',
                'size': 4
            }),
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'prioridad': forms.Select(attrs={'class': 'form-control'}),
            'fecha_vencimiento': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'fecha_inicio_estimada': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'tiempo_estimado': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 2:30:00 (2 horas 30 minutos)'
            }),
            'dependencias': forms.SelectMultiple(attrs={
                'class': 'form-control',
                'size': 4
            }),
            'tags': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: frontend, urgent, bug'
            }),
        }
        help_texts = {
            'asignados': 'Mantén presionado Ctrl (Cmd en Mac) para seleccionar múltiples usuarios',
            'fecha_vencimiento': 'Opcional - Fecha límite para completar la tarea',
            'tiempo_estimado': 'Formato: HH:MM:SS (ej: 4:30:00 para 4h 30m)',
            'dependencias': 'Tareas que deben completarse antes que esta',
            'tags': 'Palabras clave separadas por comas para organizar',
        }

    def clean_tiempo_estimado(self):
        """Validar formato de tiempo estimado"""
        tiempo = self.cleaned_data.get('tiempo_estimado')
        if tiempo:
            # Django ya maneja la conversión a DurationField
            return tiempo
        return None

    def clean(self):
        """Validaciones adicionales"""
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio_estimada')
        fecha_vencimiento = cleaned_data.get('fecha_vencimiento')
        
        if fecha_inicio and fecha_vencimiento:
            if fecha_vencimiento.date() < fecha_inicio:
                raise forms.ValidationError('La fecha de vencimiento debe ser posterior a la fecha de inicio.')
        
        return cleaned_data


class MiembroProyectoForm(forms.ModelForm):
    """Formulario para agregar miembros a proyectos"""
    
    def __init__(self, *args, **kwargs):
        self.proyecto = kwargs.pop('proyecto', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar usuarios que NO sean ya miembros del proyecto
        if self.proyecto:
            usuarios_existentes = self.proyecto.miembros.values_list('usuario_id', flat=True)
            usuarios_disponibles = User.objects.filter(
                email__endswith='@adicla.org.gt'
            ).exclude(id__in=usuarios_existentes).exclude(id=self.proyecto.creador.id)
            self.fields['usuario'].queryset = usuarios_disponibles
    
    class Meta:
        model = MiembroProyecto
        fields = ['usuario', 'rol']
        labels = {
            'usuario': 'Usuario',
            'rol': 'Rol en el Proyecto',
        }
        widgets = {
            'usuario': forms.Select(attrs={'class': 'form-control'}),
            'rol': forms.Select(attrs={'class': 'form-control'}),
        }
        help_texts = {
            'rol': 'Usuario: Acceso básico. Jefe: Puede gestionar tareas. Admin: Control total',
        }
