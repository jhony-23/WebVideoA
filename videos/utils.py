import os
import subprocess
import json
import logging
from django.conf import settings
from pathlib import Path

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
        '480p': {
            'width': 854,
            'height': 480,
            'video_bitrate': 1400,
            'maxrate_ratio': 1.1,
            'bufsize_ratio': 1.5,
            'audio_bitrate': 96
        }
    }

    def __init__(self, input_path):
        self.input_path = input_path
        self.output_dir = self._get_hls_output_dir()
        self.segment_time = 4  # Segmentos de 4s
        self.fps = None        # Determinado dinámicamente
        self.logger_prefix = f"[VideoProcessor:{os.path.basename(input_path)}]"
        self.logger = logging.getLogger('videos.ffmpeg')

    def _get_hls_output_dir(self):
        """Genera el directorio de salida para los streams HLS"""
        base_name = Path(self.input_path).stem
        hls_dir = Path(settings.MEDIA_ROOT) / 'hls' / base_name
        return str(hls_dir)

    def _ensure_output_dir(self):
        """Crea el directorio de salida si no existe"""
        os.makedirs(self.output_dir, exist_ok=True)

    def _get_video_info(self):
        """Obtiene información ampliada (fps, dimensiones, duración)."""
        cmd = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height,duration,r_frame_rate,avg_frame_rate',
            '-show_entries', 'format=duration,bit_rate',
            '-of', 'json', self.input_path
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

    def transcode_to_hls(self):
        """Transcodifica el video a múltiples calidades HLS de forma robusta."""
        self._ensure_output_dir()

        info = self._get_video_info()
        if not info:
            self.logger.error(f"{self.logger_prefix} No se pudo obtener info del video")
            return False

        stream = info['streams'][0]
        source_w = int(stream.get('width', 0))
        source_h = int(stream.get('height', 0))
        if not source_w or not source_h:
            self.logger.error(f"{self.logger_prefix} Resolución inválida")
            return False

        # Calcular GOP (fps * segment_time)
        fps = self.fps or 25
        gop = max(12, int(fps * self.segment_time))

        successful = []
        master_lines = ['#EXTM3U']

        # Ordenar perfiles por resolución descendente
        for quality, profile in sorted(self.QUALITY_PROFILES.items(), key=lambda x: x[1]['width'], reverse=True):
            try:
                t_w, t_h = self._adapt_to_source(profile['width'], profile['height'], source_w, source_h)
                if t_w * t_h < (0.20 * source_w * source_h):
                    self.logger.info(f"{self.logger_prefix} Saltando {quality}, demasiado pequeño vs origen")
                    continue

                v_kbps = profile['video_bitrate']
                maxrate = int(v_kbps * profile['maxrate_ratio'])
                bufsize = int(v_kbps * profile['bufsize_ratio'])
                a_kbps = profile['audio_bitrate']

                variant_path = os.path.join(self.output_dir, f"{quality}.m3u8")
                segments_pattern = os.path.join(self.output_dir, f"{quality}_%03d.ts")

                # Construir comando ffmpeg para la variante
                # Usamos scale a las dimensiones calculadas (t_w,t_h) ya adaptadas
                # por _adapt_to_source para mantener aspect ratio y forzar pares.
                cmd = [
                    'ffmpeg', '-y', '-i', self.input_path,
                    '-c:v', self.BASE_CONFIG['video_codec'],
                    '-preset', self.BASE_CONFIG['preset'],
                    '-tune', self.BASE_CONFIG['tune'],
                    '-vf', f'scale={t_w}:{t_h}',
                    '-b:v', self._format_bitrate(v_kbps),
                    '-maxrate', self._format_bitrate(maxrate),
                    '-bufsize', self._format_bitrate(bufsize),
                    '-g', str(gop), '-keyint_min', str(gop), '-sc_threshold', '0',
                    '-c:a', self.BASE_CONFIG['audio_codec'], '-b:a', f'{a_kbps}k', '-ac', '2', '-ar', '48000',
                    '-hls_time', str(self.segment_time),
                    '-hls_playlist_type', 'vod',
                    '-hls_flags', 'independent_segments',
                    '-hls_segment_filename', segments_pattern,
                    '-f', 'hls', variant_path
                ]

                self.logger.info(f"{self.logger_prefix} Generando {quality} {t_w}x{t_h} @ {v_kbps}kbps (fps={fps}, gop={gop})")
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
                if result.returncode != 0:
                    self.logger.error(f"{self.logger_prefix} Error {quality}: {result.stderr[:400]}")
                    continue
                if not os.path.exists(variant_path):
                    self.logger.error(f"{self.logger_prefix} Variante {quality} no creada")
                    continue

                bandwidth = v_kbps * 1000 + a_kbps * 1000
                master_lines.append(
                    f"#EXT-X-STREAM-INF:BANDWIDTH={bandwidth},AVERAGE-BANDWIDTH={bandwidth - 50000},RESOLUTION={t_w}x{t_h},CODECS=\"avc1.64001f,mp4a.40.2\""
                )
                master_lines.append(f"{quality}.m3u8")
                successful.append(quality)

            except subprocess.TimeoutExpired:
                self.logger.error(f"{self.logger_prefix} Timeout en {quality}")
                continue
            except Exception as e:
                self.logger.exception(f"{self.logger_prefix} Excepción en {quality}: {e}")
                continue

        if not successful:
            self.logger.error(f"{self.logger_prefix} Ninguna calidad generada")
            # Limpiar directorio si vacío
            try:
                import shutil
                shutil.rmtree(self.output_dir)
            except Exception:
                pass
            return False

        master_path = os.path.join(self.output_dir, 'master.m3u8')
        with open(master_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(master_lines) + '\n')
        self.logger.info(f"{self.logger_prefix} Master playlist creada con calidades: {', '.join(successful)}")
        return True

    def create_thumbnail(self, time=2):
        """Genera un thumbnail del video en el segundo especificado"""
        thumbnail_path = os.path.join(self.output_dir, 'thumbnail.jpg')
        cmd = [
            'ffmpeg',
            '-y',
            '-i', self.input_path,
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