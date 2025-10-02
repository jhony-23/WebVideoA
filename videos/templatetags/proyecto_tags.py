from django import template
from django.contrib.auth.models import User

register = template.Library()

@register.filter
def puede_gestionar(proyecto, usuario):
    """
    Template filter para verificar si un usuario puede gestionar un proyecto.
    Uso: {% if proyecto|puede_gestionar:user %}
    """
    if not usuario or not hasattr(proyecto, 'puede_gestionar'):
        return False
    return proyecto.puede_gestionar(usuario)

@register.filter
def es_admin(proyecto, usuario):
    """
    Template filter para verificar si un usuario es admin de un proyecto.
    Uso: {% if proyecto|es_admin:user %}
    """
    if not usuario or not hasattr(proyecto, 'es_admin'):
        return False
    return proyecto.es_admin(usuario)

@register.filter
def es_jefe_proyecto(proyecto, usuario):
    """
    Template filter para verificar si un usuario es jefe de un proyecto.
    Uso: {% if proyecto|es_jefe_proyecto:user %}
    """
    if not usuario or not hasattr(proyecto, 'es_jefe_proyecto'):
        return False
    return proyecto.es_jefe_proyecto(usuario)

@register.filter
def es_miembro(proyecto, usuario):
    """
    Template filter para verificar si un usuario es miembro de un proyecto.
    Uso: {% if proyecto|es_miembro:user %}
    """
    if not usuario or not hasattr(proyecto, 'miembros'):
        return False
    return proyecto.miembros.filter(usuario=usuario).exists()