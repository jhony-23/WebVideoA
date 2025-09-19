from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .models import Media
from .forms import MediaForm
from django.contrib import messages
from django.utils.timezone import localtime

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


def upload_media(request):
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

    media_items = Media.objects.all().order_by('-uploaded_at')
    return render(request, 'videos/upload.html', {
        'form': form,
        'media_items': media_items,
    })

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
