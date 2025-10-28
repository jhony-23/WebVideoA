import os
import sys
from pathlib import Path

# Setup Django environment (like video_processor.py)
sys.path.append(str(Path(__file__).parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AdiclaVideo.settings')
import django
django.setup()

from django.conf import settings
from videos.models import Media
from videos.utils import VideoProcessor

m = Media.objects.first()
if not m:
    print('No media found')
    sys.exit(1)

path = os.path.join(settings.MEDIA_ROOT, str(m.file))
print('Updating media', m.id, 'path=', path)
vp = VideoProcessor(path)
info = vp._get_video_info()
if not info:
    print('ffprobe failed')
    sys.exit(1)

fmt_dur = info.get('format', {}).get('duration')
streams = info.get('streams') or []
stream_dur = streams[0].get('duration') if streams else None
try:
    duration = float(fmt_dur) if fmt_dur is not None else float(stream_dur or 0.0)
except Exception:
    duration = float(stream_dur or 0.0)

qualities = []
base = os.path.join(settings.MEDIA_ROOT, 'hls', Path(path).stem)
for q in ['1080p','720p','480p']:
    qpath = os.path.join(base, f"{q}.m3u8")
    if os.path.exists(qpath):
        qualities.append(q)

m.stream_status = 'ready'
m.is_stream_ready = True
m.hls_path = f'hls/{m.file.name.replace(".mp4","")}'
m.available_qualities = qualities
m.duration = duration
m.save()
print('Updated media', m.id, 'hls_path=', m.hls_path, 'qualities=', qualities, 'duration=', m.duration)
