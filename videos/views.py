from django.shortcuts import render, redirect, get_object_or_404
from .models import Media
from .forms import MediaForm
from django.contrib import messages

def home(request):
    media_qs = Media.objects.all().order_by('uploaded_at')
    media_items = [
        {
            "id": m.id,
            "title": m.title,
            "file": m.file.url,
            "media_type": m.media_type,
            "uploaded_at": m.uploaded_at,
        } 
        for m in media_qs
    ]
    return render(request, 'videos/home.html', {'media_items': media_items})


def upload_media(request):
    if request.method == 'POST':
        form = MediaForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
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
