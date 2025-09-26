from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import Media, PlaylistState
from .forms import MediaForm
from django.contrib import messages
from django.utils.timezone import localtime
import json
import random

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
    
    context = {
        'user': request.user,
    }
    return render(request, 'videos/tareas_dashboard.html', context)
