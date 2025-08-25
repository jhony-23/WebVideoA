from django.shortcuts import render, redirect, get_object_or_404
from .models import Media
from .forms import MediaForm

def home(request):
    media_qs = Media.objects.all().order_by('uploaded_at')
    media_items = [{"title": m.title, "file": m.file.url, "media_type": m.media_type} for m in media_qs]
    return render(request, 'videos/home.html', {'media_items': media_items})

def upload_media(request):
    if request.method == 'POST':
        form = MediaForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
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
            return redirect('upload')
    else:
        form = MediaForm(instance=media)
    return render(request, 'videos/edit_video.html', {'form': form, 'media': media})

def delete_media(request, media_id):
    media = get_object_or_404(Media, id=media_id)
    if request.method == 'POST':
        media.delete()
        return redirect('upload')
    return render(request, 'videos/delete_confirm.html', {'media': media})
