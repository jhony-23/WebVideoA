from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import models
import os
from videos.models import Media
from videos.utils import VideoProcessor

class Command(BaseCommand):
    help = 'Recalculate and fix duration for processed media using ffprobe (VideoProcessor).'

    def add_arguments(self, parser):
        parser.add_argument('--only-missing', action='store_true', help='Only update media with missing or zero duration')

    def handle(self, *args, **options):
        only_missing = options.get('only_missing')
        qs = Media.objects.filter(is_stream_ready=True)
        if only_missing:
            qs = qs.filter(models.Q(duration__isnull=True) | models.Q(duration__lte=0))

        total = qs.count()
        self.stdout.write(f'Found {total} media to check')

        for m in qs:
            try:
                input_path = os.path.join(settings.MEDIA_ROOT, str(m.file))
                if not os.path.exists(input_path):
                    self.stdout.write(self.style.WARNING(f'File not found for media {m.id}: {input_path}'))
                    continue

                vp = VideoProcessor(input_path)
                info = vp._get_video_info()
                if not info:
                    self.stdout.write(self.style.ERROR(f'ffprobe failed for media {m.id}'))
                    continue

                fmt_dur = info.get('format', {}).get('duration')
                stream_dur = None
                streams = info.get('streams') or []
                if streams:
                    stream_dur = streams[0].get('duration')

                duration = 0.0
                try:
                    if fmt_dur is not None:
                        duration = float(fmt_dur)
                    elif stream_dur is not None:
                        duration = float(stream_dur)
                except Exception:
                    duration = float(stream_dur or 0.0)

                if duration and abs((m.duration or 0.0) - duration) > 0.5:
                    m.duration = duration
                    m.save()
                    self.stdout.write(self.style.SUCCESS(f'Updated media {m.id} duration -> {duration:.2f}s'))
                else:
                    self.stdout.write(f'No change for media {m.id} (duration {m.duration})')

            except Exception as e:
                self.stderr.write(f'Error processing media {m.id}: {e}')
