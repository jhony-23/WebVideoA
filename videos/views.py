from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.db import models
from django.db.models import Q
from functools import wraps
from .models import Media, PlaylistState, PerfilUsuario, Proyecto, Tarea, MiembroProyecto
from .forms import MediaForm, ProyectoForm, TareaForm, MiembroProyectoForm
from django.contrib import messages
from django.utils.timezone import localtime
import json
import random

# Decorador personalizado para repositorio
def repositorio_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('repositorio_login')
        return view_func(request, *args, **kwargs)
    return wrapper

def home(request):
    media_qs = Media.objects.all().order_by('uploaded_at')
    media_items = []
    for m in media_qs:
        stream_url = m.get_stream_url() if m.media_type == 'video' else m.file.url
        media_items.append({
            'id': m.id,
            'title': m.title,
            'file': m.file.url,
            'media_type': m.media_type,
            'uploaded_at': localtime(m.uploaded_at).strftime('%Y-%m-%d %H:%M:%S'),
            'is_stream_ready': m.is_stream_ready,
            'stream_status': m.stream_status,
            'hls_path': m.hls_path,
            'available_qualities': m.available_qualities,
            'stream_url': stream_url,
        })
    return render(request, 'videos/home.html', {'media_items': media_items})



def edit_media(request, media_id):
    media = get_object_or_404(Media, id=media_id)

    if request.method == 'POST':
        form = MediaForm(request.POST, request.FILES, instance=media)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cambios guardados correctamente')
            return redirect('upload')
        else:
            print(form.errors)  # Solo para depuración
    else:
        form = MediaForm(instance=media)

    return render(request, 'videos/edit_video.html', {'form': form, 'media': media})


def delete_media(request, media_id):
    media = get_object_or_404(Media, id=media_id)
    if request.method == 'POST':
        media.delete()
        messages.success(request, f'El archivo "{media.title}" ha sido eliminado')
        return redirect('upload')
    return render(request, 'videos/delete_confirm.html', {'media': media})


@require_GET
def media_status(request, media_id):
    """Endpoint JSON para consultar estado de procesamiento HLS."""
    media = get_object_or_404(Media, id=media_id)
    if media.media_type != 'video':
        return JsonResponse({'error': 'No es un video'}, status=400)
    return JsonResponse({
        'id': media.id,
        'stream_status': media.stream_status,
        'is_stream_ready': media.is_stream_ready,
        'available_qualities': media.available_qualities,
        'stream_url': media.get_stream_url(),
        'error_message': media.error_message,
    })

# ============ NUEVAS VISTAS PARA SISTEMA LIVE ============

def login_view(request):
    """Vista de login para upload"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Autenticar con email como username
        user = authenticate(request, username=email, password=password)
        if user is not None and user.email == 'publicidad@adicla.org.gt':
            # Configurar sesión de 8 horas (28800 segundos)
            request.session.set_expiry(28800)
            login(request, user)
            return redirect('upload')
        else:
            messages.error(request, 'Credenciales inválidas')
    
    return render(request, 'videos/login.html')

def logout_view(request):
    """Cerrar sesión"""
    logout(request)
    return redirect('login')

@login_required
def upload_media(request):
    """Vista de upload protegida con login"""
    if request.method == 'POST':
        form = MediaForm(request.POST, request.FILES)
        if form.is_valid():
            media = form.save()
            # Respuesta JSON para peticiones AJAX
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'id': media.id,
                    'title': media.title,
                    'status': media.stream_status,
                    'is_stream_ready': media.is_stream_ready,
                    'stream_url': media.get_stream_url(),
                })
            messages.success(request, 'Contenido subido correctamente')
            return redirect('upload')
    else:
        form = MediaForm()

    # Estado de reproducción para mostrar botón correcto
    state = PlaylistState.get_current_state()
    
    media_items = Media.objects.all().order_by('-uploaded_at')
    return render(request, 'videos/upload.html', {
        'form': form,
        'media_items': media_items,
        'playlist_state': state,
    })

@require_POST
@login_required
def start_playlist(request):
    """Iniciar reproducción sincronizada"""
    state = PlaylistState.get_current_state()
    
    # Generar playlist aleatoria
    videos = list(Media.objects.filter(media_type='video', is_stream_ready=True))
    images = list(Media.objects.filter(media_type='image'))
    
    # Combinar y shuffle
    all_media = videos + images
    random.shuffle(all_media)
    
    if not all_media:
        return JsonResponse({'error': 'No hay contenido disponible'}, status=400)
    
    # Actualizar estado
    state.is_active = True
    state.current_media_id = all_media[0].id
    state.playlist_data = [m.id for m in all_media]
    state.started_at = timezone.now()
    state.save()
    
    return JsonResponse({'success': True, 'message': 'Reproducción iniciada exitosamente'})

@require_POST  
@login_required
def stop_playlist(request):
    """Detener reproducción sincronizada"""
    state = PlaylistState.get_current_state()
    state.is_active = False
    state.current_media_id = None
    state.started_at = None
    state.save()
    
    return JsonResponse({'success': True})

@require_GET
def sync_status(request):
    """API para sincronización de clientes"""
    state = PlaylistState.get_current_state()
    
    if not state.is_active or not state.playlist_data:
        return JsonResponse({
            'active': False,
            'message': 'Reproducción no iniciada'
        })
    
    current_media = state.get_current_media()
    if not current_media:
        return JsonResponse({
            'active': False,
            'message': 'Media no encontrado'
        })
    
    # Completar con respuesta válida
    return JsonResponse({
        'active': True,
        'current_media': current_media.id,
        'position': state.get_current_position(),
        'playlist': state.playlist_data
    })

# ================================
# DECORADOR PARA SISTEMA DE TAREAS
# ================================

def tareas_login_required(view_func):
    """Decorador personalizado para el sistema de tareas"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.session.get('tareas_user'):
            return redirect('tareas_login')
        if not request.user.email.endswith('@adicla.org.gt'):
            messages.error(request, 'Acceso no autorizado')
            return redirect('tareas_login')
        return view_func(request, *args, **kwargs)
    return wrapper

# ================================
# VISTAS DEL SISTEMA DE TAREAS
# ================================

@tareas_login_required
def tareas_lista(request):
    """Vista para listar todas las tareas del usuario"""
    # Obtener todas las tareas donde el usuario está involucrado
    tareas = Tarea.objects.filter(
        Q(creador=request.user) | Q(asignados=request.user)
    ).distinct().order_by('-created_at')
    
    # Filtros
    busqueda = request.GET.get('q', '')
    estado_filtro = request.GET.get('estado', '')
    prioridad_filtro = request.GET.get('prioridad', '')
    proyecto_filtro = request.GET.get('proyecto', '')
    
    if busqueda:
        tareas = tareas.filter(
            Q(titulo__icontains=busqueda) | Q(descripcion__icontains=busqueda)
        )
    
    if estado_filtro:
        tareas = tareas.filter(estado=estado_filtro)
    
    if prioridad_filtro:
        tareas = tareas.filter(prioridad=prioridad_filtro)
    
    if proyecto_filtro:
        tareas = tareas.filter(proyecto_id=proyecto_filtro)
    
    # Datos para los filtros
    proyectos_disponibles = Proyecto.objects.filter(
        Q(creador=request.user) | Q(miembros__usuario=request.user)
    ).distinct()
    
    estados_disponibles = Tarea.ESTADOS_TAREA
    prioridades_disponibles = Tarea.PRIORIDADES
    
    context = {
        'tareas': tareas,
        'busqueda': busqueda,
        'estado_filtro': estado_filtro,
        'prioridad_filtro': prioridad_filtro,
        'proyecto_filtro': proyecto_filtro,
        'proyectos_disponibles': proyectos_disponibles,
        'estados_disponibles': estados_disponibles,
        'prioridades_disponibles': prioridades_disponibles,
    }
    
    return render(request, 'videos/tareas_lista.html', context)

@tareas_login_required
def tarea_detalle(request, tarea_id):
    """Vista para ver el detalle de una tarea"""
    tarea = get_object_or_404(Tarea, id=tarea_id)
    
    # Verificar permisos
    if not (tarea.creador == request.user or 
            request.user in tarea.asignados.all() or 
            tarea.proyecto.puede_gestionar(request.user)):
        messages.error(request, '❌ No tienes permisos para ver esta tarea')
        return redirect('tareas_lista')
    
    # Obtener tareas relacionadas del mismo proyecto
    tareas_relacionadas = Tarea.objects.filter(
        proyecto=tarea.proyecto
    ).exclude(id=tarea.id).order_by('-created_at')[:5]
    
    context = {
        'tarea': tarea,
        'tareas_relacionadas': tareas_relacionadas,
        'estados_disponibles': Tarea.ESTADOS_TAREA,
    }
    
    return render(request, 'videos/tarea_detalle.html', context)

@tareas_login_required
def tarea_crear(request, proyecto_pk=None):
    """Vista para crear una nueva tarea"""
    proyecto = None
    if proyecto_pk:
        proyecto = get_object_or_404(Proyecto, pk=proyecto_pk)
        # Verificar permisos para crear tareas en el proyecto
        if not (proyecto.creador == request.user or 
                proyecto.miembros.filter(usuario=request.user).exists()):
            messages.error(request, '❌ No tienes permisos para crear tareas en este proyecto')
            return redirect('proyecto_detalle', proyecto_pk)
    
    if request.method == 'POST':
        form = TareaForm(request.POST, user=request.user)
        if form.is_valid():
            tarea = form.save(commit=False)
            tarea.creador = request.user
            # Si se especificó un proyecto y no se seleccionó otro en el form
            if proyecto and not tarea.proyecto:
                tarea.proyecto = proyecto
            tarea.save()
            form.save_m2m()  # Guardar relaciones many-to-many
            
            messages.success(request, f'✅ Tarea "{tarea.titulo}" creada exitosamente')
            return redirect('tarea_detalle', tarea.id)
    else:
        form = TareaForm(user=request.user, initial={'proyecto': proyecto} if proyecto else {})
    
    context = {
        'form': form,
        'title': 'Crear Nueva Tarea',
        'proyecto': proyecto,
    }
    
    return render(request, 'videos/tarea_crear.html', context)

@tareas_login_required
def tarea_editar(request, tarea_id):
    """Vista para editar una tarea existente"""
    tarea = get_object_or_404(Tarea, id=tarea_id)
    
    # Verificar permisos de edición
    if not (tarea.creador == request.user or tarea.proyecto.puede_gestionar(request.user)):
        messages.error(request, '❌ No tienes permisos para editar esta tarea')
        return redirect('tarea_detalle', tarea.id)
    
    if request.method == 'POST':
        form = TareaForm(request.POST, instance=tarea, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'✅ Tarea "{tarea.titulo}" actualizada exitosamente')
            return redirect('tarea_detalle', tarea.id)
    else:
        form = TareaForm(instance=tarea, user=request.user)
    
    context = {
        'form': form,
        'tarea': tarea,
        'title': f'Editar Tarea: {tarea.titulo}',
    }
    
    return render(request, 'videos/tarea_crear.html', context)

@require_POST
@tareas_login_required
def tarea_cambiar_estado(request, tarea_id):
    """Vista AJAX para cambiar el estado de una tarea"""
    try:
        tarea = get_object_or_404(Tarea, id=tarea_id)
        
        # Verificar permisos
        if not (tarea.creador == request.user or 
                request.user in tarea.asignados.all() or 
                tarea.proyecto.puede_gestionar(request.user)):
            return JsonResponse({
                'success': False, 
                'error': 'No tienes permisos para cambiar el estado de esta tarea'
            })
        
        nuevo_estado = request.POST.get('estado')
        
        # Validar que el estado sea válido
        estados_validos = [choice[0] for choice in Tarea.ESTADOS_TAREA]
        if nuevo_estado not in estados_validos:
            return JsonResponse({
                'success': False, 
                'error': 'Estado no válido'
            })
        
        # Actualizar estado
        tarea.estado = nuevo_estado
        tarea.save()
        
        return JsonResponse({
            'success': True,
            'nuevo_estado': tarea.get_estado_display(),
            'message': f'Estado cambiado a: {tarea.get_estado_display()}'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error interno: {str(e)}'
        })

@tareas_login_required
def tarea_eliminar(request, tarea_id):
    """Vista para eliminar una tarea"""
    tarea = get_object_or_404(Tarea, id=tarea_id)
    
    # Verificar permisos de eliminación
    if not (tarea.creador == request.user or tarea.proyecto.puede_gestionar(request.user)):
        messages.error(request, '❌ No tienes permisos para eliminar esta tarea')
        return redirect('tarea_detalle', tarea.id)
    
    if request.method == 'POST':
        proyecto_id = tarea.proyecto.id
        titulo_tarea = tarea.titulo
        tarea.delete()
        messages.success(request, f'✅ Tarea "{titulo_tarea}" eliminada exitosamente')
        return redirect('proyecto_detalle', proyecto_id)
    
    context = {
        'tarea': tarea,
        'title': f'Eliminar Tarea: {tarea.titulo}',
    }
    
    return render(request, 'videos/tarea_eliminar.html', context)

    elapsed = state.get_elapsed_time()
    
    # Determinar duración según tipo
    if current_media.media_type == 'image':
        duration = 10  # 10 segundos para imágenes
    else:
        duration = current_media.duration or 0
    
    # Serializar media actual
    stream_url = current_media.get_stream_url() if current_media.media_type == 'video' else current_media.file.url
    
    return JsonResponse({
        'active': True,
        'current_media': {
            'id': current_media.id,
            'title': current_media.title,
            'file': current_media.file.url,
            'media_type': current_media.media_type,
            'stream_url': stream_url,
            'is_stream_ready': current_media.is_stream_ready,
        },
        'elapsed': elapsed,
        'duration': duration,
        'current_index': state.get_current_index(),
        'total_items': len(state.playlist_data)
    })

# ===================== NUEVAS VISTAS PARA LA PLATAFORMA ADICLA =====================

def landing_page(request):
    """Nueva página de inicio - Landing de ADICLA"""
    return render(request, 'videos/landing.html')

def tareas_login(request):
    """Login para Gestión de Tareas con validación @adicla.org.gt"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        
        # Validar dominio @adicla.org.gt
        if not email.endswith('@adicla.org.gt'):
            messages.error(request, 'Solo se permiten usuarios con dominio @adicla.org.gt')
            return render(request, 'videos/tareas_login.html')
        
        # Crear usuario si no existe (registro automático)
        from django.contrib.auth.models import User
        user, created = User.objects.get_or_create(
            username=email,
            defaults={
                'email': email,
                'first_name': email.split('@')[0],
            }
        )
        
        if created:
            user.set_password(password)
            user.save()
            messages.success(request, f'Usuario creado exitosamente: {email}')
        else:
            # Verificar contraseña
            if not user.check_password(password):
                messages.error(request, 'Contraseña incorrecta')
                return render(request, 'videos/tareas_login.html')
        
        # Iniciar sesión
        login(request, user)
        request.session['tareas_user'] = True
        return redirect('tareas_dashboard')
    
    return render(request, 'videos/tareas_login.html')

def tareas_logout(request):
    """Cerrar sesión de Gestión de Tareas"""
    if 'tareas_user' in request.session:
        del request.session['tareas_user']
    logout(request)
    return redirect('tareas_login')

def tareas_dashboard(request):
    """Dashboard principal de Gestión de Tareas"""
    # Verificar que sea un usuario de tareas
    if not request.user.is_authenticated or not request.session.get('tareas_user'):
        return redirect('tareas_login')
    
    # Verificar dominio del usuario
    if not request.user.email.endswith('@adicla.org.gt'):
        messages.error(request, 'Acceso no autorizado')
        return redirect('tareas_login')
    
    # Importar modelos de tareas
    from .models import Proyecto, Tarea, MiembroProyecto
    
    # Obtener estadísticas del usuario
    proyectos_creados = Proyecto.objects.filter(creador=request.user)
    proyectos_como_miembro = Proyecto.objects.filter(miembros__usuario=request.user)
    todos_mis_proyectos = (proyectos_creados | proyectos_como_miembro).distinct()
    
    # Tareas asignadas al usuario
    mis_tareas = Tarea.objects.filter(asignados=request.user)
    tareas_pendientes = mis_tareas.filter(estado='pendiente').count()
    tareas_en_proceso = mis_tareas.filter(estado='en_proceso').count()
    tareas_completadas = mis_tareas.filter(estado='completada').count()
    
    # Tareas por prioridad
    tareas_criticas = mis_tareas.filter(prioridad='critica').exclude(estado='completada').count()
    tareas_altas = mis_tareas.filter(prioridad='alta').exclude(estado='completada').count()
    
    # Proyectos recientes
    proyectos_recientes = todos_mis_proyectos.order_by('-updated_at')[:5]
    
    # Tareas próximas a vencer (siguientes 7 días)
    from datetime import datetime, timedelta
    fecha_limite = timezone.now() + timedelta(days=7)
    tareas_proximas = mis_tareas.filter(
        fecha_vencimiento__lte=fecha_limite,
        fecha_vencimiento__gte=timezone.now()
    ).exclude(estado='completada').order_by('fecha_vencimiento')[:5]
    
    context = {
        'user': request.user,
        'total_proyectos': todos_mis_proyectos.count(),
        'proyectos_activos': todos_mis_proyectos.filter(estado='activo').count(),
        'total_tareas': mis_tareas.count(),
        'tareas_pendientes': tareas_pendientes,
        'tareas_en_proceso': tareas_en_proceso,
        'tareas_completadas': tareas_completadas,
        'tareas_criticas': tareas_criticas,
        'tareas_altas': tareas_altas,
        'proyectos_recientes': proyectos_recientes,
        'tareas_proximas': tareas_proximas,
        'es_primer_acceso': not todos_mis_proyectos.exists(),
    }
    return render(request, 'videos/tareas_dashboard.html', context)

@repositorio_login_required
def repositorio_view(request):
    """Vista para el sistema de repositorio - requiere login"""
    return render(request, 'videos/repositorio.html')

def repositorio_login(request):
    """Vista de login para repositorio"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Validar que el email sea de @adicla.org.gt
        if not email.endswith('@adicla.org.gt'):
            messages.error(request, 'Solo se permiten usuarios con email @adicla.org.gt')
            return render(request, 'videos/repositorio_login.html')
        
        # Autenticar con email como username
        user = authenticate(request, username=email, password=password)
        if user is not None:
            # Configurar sesión de 8 horas (28800 segundos)
            request.session.set_expiry(28800)
            login(request, user)
            return redirect('repositorio')
        else:
            messages.error(request, 'Credenciales inválidas')
    
    return render(request, 'videos/repositorio_login.html')

def repositorio_logout(request):
    """Cerrar sesión de repositorio"""
    logout(request)
    return redirect('repositorio_login')

# =============== SISTEMA DE RECUPERACIÓN DE CONTRASEÑAS ===============

def upload_password_reset(request):
    """Recuperación de contraseña para upload/admin"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        # Validaciones
        if not email or not password or not confirm_password:
            messages.error(request, 'Todos los campos son obligatorios')
            return render(request, 'videos/upload_password_reset.html')
        
        if password != confirm_password:
            messages.error(request, 'Las contraseñas no coinciden')
            return render(request, 'videos/upload_password_reset.html')
        
        if len(password) < 6:
            messages.error(request, 'La contraseña debe tener al menos 6 caracteres')
            return render(request, 'videos/upload_password_reset.html')
        
        # Verificar que el usuario existe
        try:
            user = User.objects.get(email=email)
            user.set_password(password)
            user.save()
            messages.success(request, f'🎉 ¡Contraseña actualizada exitosamente para {email}! Ya puedes iniciar sesión con tu nueva contraseña.')
            return redirect('login')
        except User.DoesNotExist:
            messages.error(request, f'❌ No existe un usuario registrado con el email: {email}')
            return render(request, 'videos/upload_password_reset.html')
    
    return render(request, 'videos/upload_password_reset.html')

def tareas_password_reset(request):
    """Recuperación de contraseña para tareas"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        # Validaciones
        if not email or not password or not confirm_password:
            messages.error(request, 'Todos los campos son obligatorios')
            return render(request, 'videos/tareas_password_reset.html')
        
        if not email.endswith('@adicla.org.gt'):
            messages.error(request, 'Solo se permiten correos @adicla.org.gt')
            return render(request, 'videos/tareas_password_reset.html')
        
        if password != confirm_password:
            messages.error(request, 'Las contraseñas no coinciden')
            return render(request, 'videos/tareas_password_reset.html')
        
        if len(password) < 6:
            messages.error(request, 'La contraseña debe tener al menos 6 caracteres')
            return render(request, 'videos/tareas_password_reset.html')
        
        # Verificar que el usuario existe y actualizar contraseña
        try:
            user = User.objects.get(email=email)
            user.set_password(password)
            user.save()
            messages.success(request, f'🎉 ¡Contraseña actualizada exitosamente para {email}! Ya puedes acceder a Gestión de Tareas con tu nueva contraseña.')
            return redirect('tareas_login')
        except User.DoesNotExist:
            messages.error(request, f'❌ No existe un usuario registrado con el email: {email}. Contacta al administrador para crear tu cuenta.')
            return render(request, 'videos/tareas_password_reset.html')
    
    return render(request, 'videos/tareas_password_reset.html')

def repositorio_password_reset(request):
    """Recuperación de contraseña para repositorio"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        # Validaciones
        if not email or not password or not confirm_password:
            messages.error(request, 'Todos los campos son obligatorios')
            return render(request, 'videos/repositorio_password_reset.html')
        
        if not email.endswith('@adicla.org.gt'):
            messages.error(request, 'Solo se permiten correos @adicla.org.gt')
            return render(request, 'videos/repositorio_password_reset.html')
        
        if password != confirm_password:
            messages.error(request, 'Las contraseñas no coinciden')
            return render(request, 'videos/repositorio_password_reset.html')
        
        if len(password) < 6:
            messages.error(request, 'La contraseña debe tener al menos 6 caracteres')
            return render(request, 'videos/repositorio_password_reset.html')
        
        # Verificar que el usuario existe y actualizar contraseña
        try:
            user = User.objects.get(email=email)
            user.set_password(password)
            user.save()
            messages.success(request, f'🎉 ¡Contraseña actualizada exitosamente para {email}! Ya puedes acceder al Repositorio con tu nueva contraseña.')
            return redirect('repositorio_login')
        except User.DoesNotExist:
            messages.error(request, f'❌ No existe un usuario registrado con el email: {email}. Contacta al administrador para crear tu cuenta.')
            return render(request, 'videos/repositorio_password_reset.html')
    
    return render(request, 'videos/repositorio_password_reset.html')


# ==================== VISTAS PARA GESTIÓN DE PROYECTOS Y TAREAS ====================

# ==================== GESTIÓN DE PROYECTOS ====================

@tareas_login_required
def proyectos_lista(request):
    """Lista de todos los proyectos del usuario"""
    from .models import Proyecto, MiembroProyecto
    
    # Proyectos donde el usuario es creador o miembro
    proyectos_creados = Proyecto.objects.filter(creador=request.user)
    proyectos_como_miembro = Proyecto.objects.filter(miembros__usuario=request.user)
    
    # Combinar y eliminar duplicados
    todos_proyectos = (proyectos_creados | proyectos_como_miembro).distinct().order_by('-created_at')
    
    # Filtros
    estado_filtro = request.GET.get('estado', '')
    if estado_filtro:
        todos_proyectos = todos_proyectos.filter(estado=estado_filtro)
    
    busqueda = request.GET.get('q', '')
    if busqueda:
        todos_proyectos = todos_proyectos.filter(
            models.Q(nombre__icontains=busqueda) |
            models.Q(codigo__icontains=busqueda) |
            models.Q(descripcion__icontains=busqueda)
        )
    
    context = {
        'proyectos': todos_proyectos,
        'estado_filtro': estado_filtro,
        'busqueda': busqueda,
        'estados_disponibles': Proyecto.ESTADOS_PROYECTO,
    }
    return render(request, 'videos/proyectos_lista.html', context)

@tareas_login_required
def proyecto_crear(request):
    """Crear nuevo proyecto"""
    from .models import Proyecto
    from .forms import ProyectoForm
    
    if request.method == 'POST':
        form = ProyectoForm(request.POST)
        if form.is_valid():
            proyecto = form.save(commit=False)
            proyecto.creador = request.user
            proyecto.save()
            messages.success(request, f'✅ Proyecto "{proyecto.nombre}" creado exitosamente!')
            return redirect('proyecto_detalle', pk=proyecto.pk)
    else:
        form = ProyectoForm()
    
    return render(request, 'videos/proyecto_crear.html', {'form': form})

@tareas_login_required
def proyecto_detalle(request, pk):
    """Detalle de un proyecto específico"""
    from .models import Proyecto, Tarea
    
    proyecto = get_object_or_404(Proyecto, pk=pk)
    
    # Verificar que el usuario tenga acceso al proyecto
    if not (proyecto.creador == request.user or proyecto.miembros.filter(usuario=request.user).exists()):
        messages.error(request, 'No tienes acceso a este proyecto')
        return redirect('proyectos_lista')
    
    # Obtener tareas del proyecto
    tareas = proyecto.tareas.all().order_by('-created_at')
    
    # Estadísticas del proyecto
    estadisticas = {
        'total_tareas': tareas.count(),
        'tareas_pendientes': tareas.filter(estado='pendiente').count(),
        'tareas_en_proceso': tareas.filter(estado='en_proceso').count(),
        'tareas_en_revision': tareas.filter(estado='en_revision').count(),
        'tareas_completadas': tareas.filter(estado='completada').count(),
        'progreso': proyecto.get_progreso(),
    }
    
    # Miembros del proyecto
    miembros = proyecto.get_miembros()
    
    context = {
        'proyecto': proyecto,
        'tareas': tareas,
        'estadisticas': estadisticas,
        'miembros': miembros,
        'es_admin': proyecto.es_admin(request.user),
        'puede_gestionar': proyecto.puede_gestionar(request.user),
    }
    return render(request, 'videos/proyecto_detalle.html', context)

@tareas_login_required
def proyecto_editar(request, pk):
    """Editar proyecto existente"""
    from .models import Proyecto
    from .forms import ProyectoForm
    
    proyecto = get_object_or_404(Proyecto, pk=pk)
    
    # Solo el creador o admins pueden editar
    if not proyecto.puede_gestionar(request.user):
        messages.error(request, 'No tienes permisos para editar este proyecto')
        return redirect('proyecto_detalle', pk=proyecto.pk)
    
    if request.method == 'POST':
        form = ProyectoForm(request.POST, instance=proyecto)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Proyecto actualizado exitosamente!')
            return redirect('proyecto_detalle', pk=proyecto.pk)
    else:
        form = ProyectoForm(instance=proyecto)
    
    context = {
        'form': form,
        'proyecto': proyecto,
        'editando': True,
    }
    return render(request, 'videos/proyecto_crear.html', context)

@tareas_login_required
def proyecto_eliminar(request, pk):
    """Eliminar proyecto"""
    from .models import Proyecto
    
    proyecto = get_object_or_404(Proyecto, pk=pk)
    
    # Solo el creador puede eliminar
    if proyecto.creador != request.user:
        messages.error(request, 'Solo el creador del proyecto puede eliminarlo')
        return redirect('proyecto_detalle', pk=proyecto.pk)
    
    if request.method == 'POST':
        confirmacion = request.POST.get('confirmacion', '').strip()
        if confirmacion == proyecto.nombre:
            nombre_proyecto = proyecto.nombre
            proyecto.delete()
            messages.success(request, f'🗑️ Proyecto "{nombre_proyecto}" eliminado exitosamente')
            return redirect('proyectos_lista')
        else:
            messages.error(request, '❌ El nombre del proyecto no coincide. Eliminación cancelada.')
            return render(request, 'videos/proyecto_eliminar.html', {'proyecto': proyecto})
    
    context = {'proyecto': proyecto}
    return render(request, 'videos/proyecto_eliminar.html', context)

# Funciones duplicadas eliminadas - se mantienen las versiones anteriores con tarea_id
