import os
import subprocess
import json
import logging
import shutil
from pathlib import Path

from django.conf import settings
from django.utils.text import slugify

class VideoProcessor:
    """Maneja la transcodificación de videos a múltiples calidades usando FFmpeg.

    Refactor enfocado en estabilidad para streaming HLS bajo WhiteNoise/Waitress:
    - Bitrates fijos por perfil (evita exceder ancho de banda en conexiones medias)
    - GOP alineado con duración de segmentos (seg_time * fps)
    - Master playlist con atributos recomendados
    - Manejo resiliente: si una calidad falla continúa con las demás
    - Limpieza de artefactos si ninguna calidad se genera
    """

    # Configuración base para todos los perfiles
    BASE_CONFIG = {
        'preset': 'veryfast',        # Compromiso velocidad/calidad
        'tune': 'fastdecode',        # Decodificación más ligera en clientes
        'audio_codec': 'aac',
        'video_codec': 'libx264'
    }

    # Perfiles de calidad fijos (bitrate de video)
    QUALITY_PROFILES = {
        '1080p': {
            'width': 1920,
            'height': 1080,
            'video_bitrate': 5000,   # kbps
            'maxrate_ratio': 1.1,
            'bufsize_ratio': 1.5,
            'audio_bitrate': 192
        },
        '720p': {
            'width': 1280,
            'height': 720,
            'video_bitrate': 3000,
            'maxrate_ratio': 1.1,
            'bufsize_ratio': 1.5,
            'audio_bitrate': 128
        },
        '360p': {
            'width': 640,
            'height': 360,
            'video_bitrate': 900,
            'maxrate_ratio': 1.1,
            'bufsize_ratio': 1.5,
            'audio_bitrate': 96
        }
    }

    def __init__(self, input_path, media_id=None):
        self.input_path = Path(str(input_path))
        self.media_id = media_id
        self.media_root = Path(settings.MEDIA_ROOT)
        self.logger_prefix = f"[VideoProcessor:{self.input_path.name}]"
        self.logger = logging.getLogger('videos.ffmpeg')
        self.segment_time = int(os.getenv('HLS_SEGMENT_SECONDS', '4'))
        self.fps = None        # Determinado dinámicamente

        self._configure_binaries()
        self.output_dir = self._get_hls_output_dir()

    def _configure_binaries(self):
        """Enforce PATH and binary names for ffmpeg/ffprobe."""
        ffmpeg_dir = getattr(settings, 'FFMPEG_BIN_DIR', None) or os.getenv('FFMPEG_BIN_DIR')
        if ffmpeg_dir:
            current_path = os.environ.get('PATH', '')
            search_paths = current_path.split(os.pathsep) if current_path else []
            if ffmpeg_dir not in search_paths:
                os.environ['PATH'] = os.pathsep.join([ffmpeg_dir, current_path]) if current_path else ffmpeg_dir
        self.ffmpeg_binary = getattr(settings, 'FFMPEG_BIN', None) or os.getenv('FFMPEG_BIN', 'ffmpeg')
        self.ffprobe_binary = (
            getattr(settings, 'FFPROBE_BIN', None)
            or os.getenv('FFPROBE_BIN')
            or os.getenv('FFMPEG_PROBE_BIN')
            or 'ffprobe'
        )

    def _get_hls_output_dir(self):
        """Genera el directorio de salida único para los streams HLS."""
        safe_name = slugify(self.input_path.stem) or self.input_path.stem or 'stream'
        if self.media_id:
            folder = f"media_{self.media_id}"
            if safe_name:
                folder = f"{folder}_{safe_name}"
        else:
            folder = safe_name
        return (self.media_root / 'hls' / folder).resolve()

    def _prepare_output_dir(self):
        """Limpiar y recrear el directorio de salida."""
        try:
            if self.output_dir.exists():
                shutil.rmtree(self.output_dir)
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            self.logger.warning(f"{self.logger_prefix} No se pudo preparar directorio HLS: {exc}")
            raise

    @property
    def relative_output_dir(self):
        try:
            return self.output_dir.relative_to(self.media_root).as_posix()
        except ValueError:
            return self.output_dir.as_posix()

    def _get_video_info(self):
        """Obtiene información ampliada (fps, dimensiones, duración)."""
        cmd = [
            self.ffprobe_binary, '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height,duration,r_frame_rate,avg_frame_rate',
            '-show_entries', 'format=duration,bit_rate',
            '-of', 'json', self.input_path.as_posix()
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
            data = json.loads(result.stdout)
            if 'streams' not in data or not data['streams']:
                raise ValueError('Sin stream de video detectable')
            stream = data['streams'][0]
            # Calcular FPS real
            fr_raw = stream.get('avg_frame_rate') or stream.get('r_frame_rate') or '0/0'
            try:
                num, den = fr_raw.split('/')
                fps = float(num) / float(den) if float(den) != 0 else 25.0
            except Exception:
                fps = 25.0
            self.fps = max(1, int(round(fps)))
            return data
        except Exception as e:
            self.logger.error(f"{self.logger_prefix} ffprobe error: {e}")
            return None

    def _adapt_to_source(self, target_w, target_h, source_w, source_h):
        """Escala manteniendo aspecto sin superar dimensiones originales."""
        if source_w < target_w and source_h < target_h:
            # No escalar hacia arriba
            target_w, target_h = source_w, source_h
        aspect = source_w / source_h if source_h else 1
        # Ajuste manteniendo aspect ratio
        if target_w / target_h > aspect:
            target_w = int(target_h * aspect)
        else:
            target_h = int(target_w / aspect)
        # Forzar par
        target_w -= target_w % 2
        target_h -= target_h % 2
        return max(2, target_w), max(2, target_h)

    def _format_bitrate(self, kbps):
        return f"{int(kbps)}k"

    def _extract_duration(self, ffprobe_data):
        """Obtiene la duración en segundos con tolerancia a valores ausentes."""
        if not ffprobe_data:
            return 0.0
        format_info = ffprobe_data.get('format', {})
        duration_candidates = [
            format_info.get('duration'),
        ]
        streams = ffprobe_data.get('streams') or []
        if streams:
            duration_candidates.append(streams[0].get('duration'))
        for value in duration_candidates:
            if value is None:
                continue
            try:
                return float(value)
            except (TypeError, ValueError):
                continue
        return 0.0

    def transcode_to_hls(self):
        """Transcodifica el video a múltiples calidades HLS de forma robusta."""
        self._prepare_output_dir()

        info = self._get_video_info()
        if not info:
            self.logger.error(f"{self.logger_prefix} No se pudo obtener info del video")
            return False, {'error': 'ffprobe_failed'}

        stream = info['streams'][0]
        source_w = int(stream.get('width', 0))
        source_h = int(stream.get('height', 0))
        if not source_w or not source_h:
            self.logger.error(f"{self.logger_prefix} Resolución inválida")
            return False, {'error': 'invalid_resolution'}

        # Calcular GOP (fps * segment_time)
        fps = self.fps or 25
        gop = max(12, int(fps * self.segment_time))

        successful = []
        variant_meta = {}
        master_lines = ['#EXTM3U', '#EXT-X-VERSION:3', '#EXT-X-INDEPENDENT-SEGMENTS']
        frame_rate_str = f"{fps:.3f}".rstrip('0').rstrip('.')

        # Ordenar perfiles por resolución descendente
        for quality, profile in sorted(self.QUALITY_PROFILES.items(), key=lambda x: x[1]['width'], reverse=True):
            try:
                target_w, target_h = self._adapt_to_source(profile['width'], profile['height'], source_w, source_h)
                if target_w * target_h < (0.20 * source_w * source_h):
                    self.logger.info(f"{self.logger_prefix} Saltando {quality}, demasiado pequeño vs origen")
                    continue

                v_kbps = profile['video_bitrate']
                maxrate = int(v_kbps * profile['maxrate_ratio'])
                bufsize = int(v_kbps * profile['bufsize_ratio'])
                a_kbps = profile['audio_bitrate']

                variant_manifest = (self.output_dir / f"{quality}.m3u8").as_posix()
                segments_pattern = (self.output_dir / f"{quality}_%03d.ts").as_posix()

                cmd = [
                    self.ffmpeg_binary, '-y', '-i', self.input_path.as_posix(),
                    '-c:v', self.BASE_CONFIG['video_codec'],
                    '-preset', self.BASE_CONFIG['preset'],
                    '-tune', self.BASE_CONFIG['tune'],
                    '-vf', f'scale={target_w}:{target_h}',
                    '-b:v', self._format_bitrate(v_kbps),
                    '-maxrate', self._format_bitrate(maxrate),
                    '-bufsize', self._format_bitrate(bufsize),
                    '-g', str(gop), '-keyint_min', str(gop), '-sc_threshold', '0',
                    '-c:a', self.BASE_CONFIG['audio_codec'], '-b:a', f'{a_kbps}k', '-ac', '2', '-ar', '48000',
                    '-hls_time', str(self.segment_time),
                    '-hls_playlist_type', 'vod',
                    '-hls_flags', 'independent_segments',
                    '-hls_segment_filename', segments_pattern,
                    '-f', 'hls', variant_manifest
                ]

                self.logger.info(
                    f"{self.logger_prefix} Generando {quality} {target_w}x{target_h} @ {v_kbps}kbps (fps={fps}, gop={gop})"
                )
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
                if result.returncode != 0:
                    self.logger.error(f"{self.logger_prefix} Error {quality}: {result.stderr[:400]}")
                    continue
                if not Path(variant_manifest).exists():
                    self.logger.error(f"{self.logger_prefix} Variante {quality} no creada")
                    continue

                bandwidth = (v_kbps + a_kbps) * 1000
                avg_bandwidth = max(50000, bandwidth - 50000)
                master_lines.append(
                    (
                        "#EXT-X-STREAM-INF:BANDWIDTH={bw},AVERAGE-BANDWIDTH={avg},RESOLUTION={res},"
                        "FRAME-RATE={fps},CODECS=\"avc1.64001f,mp4a.40.2\""
                    ).format(
                        bw=bandwidth,
                        avg=avg_bandwidth,
                        res=f"{target_w}x{target_h}",
                        fps=frame_rate_str,
                    )
                )
                master_lines.append(f"{quality}.m3u8")
                successful.append(quality)
                variant_meta[quality] = {
                    'width': target_w,
                    'height': target_h,
                    'video_bitrate': v_kbps,
                    'audio_bitrate': a_kbps,
                }

            except subprocess.TimeoutExpired:
                self.logger.error(f"{self.logger_prefix} Timeout en {quality}")
                continue
            except Exception as exc:
                self.logger.exception(f"{self.logger_prefix} Excepción en {quality}: {exc}")
                continue

        if not successful:
            self.logger.error(f"{self.logger_prefix} Ninguna calidad generada")
            try:
                shutil.rmtree(self.output_dir)
            except Exception:
                pass
            return False, {'error': 'no_variant_generated'}

        master_path = self.output_dir / 'master.m3u8'
        with master_path.open('w', encoding='utf-8') as manifest:
            manifest.write('\n'.join(master_lines) + '\n')

        duration = self._extract_duration(info)

        metadata = {
            'qualities': successful,
            'variants': variant_meta,
            'relative_output_dir': self.relative_output_dir,
            'output_dir': self.output_dir.as_posix(),
            'duration': duration,
            'width': source_w,
            'height': source_h,
            'fps': fps,
        }

        self.logger.info(
            f"{self.logger_prefix} Master playlist creada con calidades: {', '.join(successful)}"
        )
        return True, metadata

    def create_thumbnail(self, time=2):
        """Genera un thumbnail del video en el segundo especificado"""
        thumbnail_path = (self.output_dir / 'thumbnail.jpg').as_posix()
        cmd = [
            self.ffmpeg_binary,
            '-y',
            '-i', self.input_path.as_posix(),
            '-ss', str(time),
            '-vframes', '1',
            '-vf', 'scale=640:-1',
            thumbnail_path
        ]
        
        try:
            subprocess.run(cmd, check=True)
            return True, thumbnail_path
        except subprocess.CalledProcessError as e:
            print(f"Error creating thumbnail: {e}")
            return False, str(e)