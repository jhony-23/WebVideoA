from django.shortcuts import render, redirect, get_object_or_404
from .models import Video
from .forms import VideoForm


def home(request):
    videos_qs = Video.objects.all().order_by('uploaded_at')
    videos = [{"title": v.title, "videofile": v.videofile.url} for v in videos_qs]
    return render(request, 'videos/home.html', {'videos': videos})


def upload_video(request):
    if request.method == 'POST':
        form = VideoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('upload')
    else:
        form = VideoForm()
    videos = Video.objects.all().order_by('-uploaded_at')
    return render(request, 'videos/upload.html', {'form': form, 'videos': videos})


def edit_video(request, video_id):
    video = get_object_or_404(Video, id=video_id)
    if request.method == 'POST':
        form = VideoForm(request.POST, request.FILES, instance=video)
        if form.is_valid():
            form.save()
            return redirect('upload')
    else:
        form = VideoForm(instance=video)
    return render(request, 'videos/edit_video.html', {'form': form, 'video': video})


def delete_video(request, video_id):
    video = get_object_or_404(Video, id=video_id)
    if request.method == 'POST':
        video.delete()
        return redirect('upload')
    return render(request, 'videos/delete_confirm.html', {'video': video})
