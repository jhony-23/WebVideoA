from django.core.management.base import BaseCommand
from videos.models import Media

class Command(BaseCommand):
    help = "Normaliza hls_path removiendo sufijo master.m3u8 y corrige stream_status 'completed' -> 'ready'"

    def handle(self, *args, **options):
        updated = 0
        for m in Media.objects.exclude(hls_path=''):
            original = m.hls_path
            changed = False
            if m.hls_path.endswith('master.m3u8'):
                m.hls_path = m.hls_path[:-len('master.m3u8')].rstrip('/')
                changed = True
            if m.stream_status == 'completed':
                m.stream_status = 'ready'
                m.is_stream_ready = True
                changed = True
            if changed:
                m.save(update_fields=['hls_path','stream_status','is_stream_ready'])
                updated += 1
                self.stdout.write(self.style.SUCCESS(f"Actualizado id={m.id} de '{original}' -> '{m.hls_path}' status={m.stream_status}"))
        self.stdout.write(self.style.WARNING(f"Registros revisados: {Media.objects.count()} | Actualizados: {updated}"))
