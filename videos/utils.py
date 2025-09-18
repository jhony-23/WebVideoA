import os
import subprocess
import json
from django.conf import settings
from pathlib import Path

class VideoProcessor:
    """Maneja la transcodificación de videos a múltiples calidades usando FFmpeg"""
    
    # Configuración base para todos los perfiles
    BASE_CONFIG = {
        'preset': 'veryfast',
        'tune': 'fastdecode',
        'audio_codec': 'aac',
        'video_codec': 'libx264'
    }

    # Perfiles de calidad dinámicos
    QUALITY_PROFILES = {
        '1080p': {
            'max_width': 1920,
            'max_height': 1920,
            'bitrate_multiplier': 4.5,  # Mbps por millón de píxeles
            'audio_bitrate': '192k',
            'bufsize_multiplier': 1.5
        },
        '720p': {
            'max_width': 1280,
            'max_height': 1280,
            'bitrate_multiplier': 3.0,
            'audio_bitrate': '128k',
            'bufsize_multiplier': 1.5
        },
        '480p': {
            'max_width': 854,
            'max_height': 854,
            'bitrate_multiplier': 2.0,
            'audio_bitrate': '96k',
            'bufsize_multiplier': 1.5
        }
    }

    def __init__(self, input_path):
        self.input_path = input_path
        self.output_dir = self._get_hls_output_dir()
        self.segment_time = 4  # 4 segundos por segmento (óptimo para WebOS)
        self.keyframe_time = 2  # Keyframes cada 2s para cambios rápidos de calidad

    def _get_hls_output_dir(self):
        """Genera el directorio de salida para los streams HLS"""
        base_name = Path(self.input_path).stem
        hls_dir = Path(settings.MEDIA_ROOT) / 'hls' / base_name
        return str(hls_dir)

    def _ensure_output_dir(self):
        """Crea el directorio de salida si no existe"""
        os.makedirs(self.output_dir, exist_ok=True)

    def _get_video_info(self):
        """Obtiene información del video usando FFprobe"""
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height,duration',
            '-of', 'json',
            self.input_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Error getting video info: {e}")
            return None

    def _calculate_target_resolution(self, source_width, source_height, max_width, max_height):
        """Calcula la resolución objetivo manteniendo la relación de aspecto"""
        aspect_ratio = source_width / source_height
        
        if source_width <= max_width and source_height <= max_height:
            # Si el video es más pequeño que el máximo, mantener tamaño original
            return source_width, source_height
            
        if aspect_ratio > 1:  # Video horizontal
            new_width = min(source_width, max_width)
            new_height = int(new_width / aspect_ratio)
            if new_height > max_height:
                new_height = max_height
                new_width = int(new_height * aspect_ratio)
        else:  # Video vertical
            new_height = min(source_height, max_height)
            new_width = int(new_height * aspect_ratio)
            if new_width > max_width:
                new_width = max_width
                new_height = int(new_width / aspect_ratio)
                
        # Asegurar que ambas dimensiones sean pares (requerido por h264)
        new_width = new_width - (new_width % 2)
        new_height = new_height - (new_height % 2)
        
        return new_width, new_height

    def _calculate_bitrate(self, width, height, multiplier):
        """Calcula el bitrate basado en la resolución"""
        pixels = width * height
        megapixels = pixels / 1000000
        bitrate_mbps = megapixels * multiplier
        return f"{int(bitrate_mbps * 1000)}k"

    def transcode_to_hls(self):
        """Transcodifica el video a múltiples calidades HLS"""
        self._ensure_output_dir()
        
        # Obtener información del video original
        video_info = self._get_video_info()
        if not video_info or 'streams' not in video_info or not video_info['streams']:
            raise ValueError("No se pudo obtener la información del video")
            
        source_width = int(video_info['streams'][0].get('width', 0))
        source_height = int(video_info['streams'][0].get('height', 0))
        
        if source_width == 0 or source_height == 0:
            raise ValueError("Dimensiones de video inválidas")
        
        # Crear master playlist
        master_content = '#EXTM3U\n'
        
        try:
            # Ordenar perfiles de mayor a menor calidad
            sorted_profiles = sorted(
                self.QUALITY_PROFILES.items(),
                key=lambda x: x[1]['max_width'] * x[1]['max_height'],
                reverse=True
            )
            
            for quality, profile in sorted_profiles:
                # Calcular resolución manteniendo aspect ratio
                target_width, target_height = self._calculate_target_resolution(
                    source_width, source_height,
                    profile['max_width'],
                    profile['max_height']
                )
                
                # Si la resolución es demasiado pequeña, saltar este perfil
                if target_width * target_height < 0.5 * source_width * source_height:
                    continue
                    
                # Calcular bitrate basado en la resolución
                bitrate = self._calculate_bitrate(target_width, target_height, profile['bitrate_multiplier'])
                maxrate = f"{int(int(bitrate[:-1]) * 1.07)}k"  # 7% más que el bitrate
                bufsize = f"{int(int(bitrate[:-1]) * profile['bufsize_multiplier'])}k"
                
                variant_path = os.path.join(self.output_dir, f'{quality}.m3u8')
                segments_path = os.path.join(self.output_dir, f'{quality}_%03d.ts')
                
                # Comando optimizado para velocidad y calidad
                cmd = [
                    'ffmpeg', '-y',
                    '-i', self.input_path,
                    '-c:v', self.BASE_CONFIG['video_codec'],
                    '-preset', self.BASE_CONFIG['preset'],
                    '-tune', self.BASE_CONFIG['tune'],
                    '-vf', f'scale={target_width}:{target_height}:force_original_aspect_ratio=disable',
                    '-b:v', bitrate,
                    '-maxrate', maxrate,
                    '-bufsize', bufsize,
                    '-c:a', self.BASE_CONFIG['audio_codec'],
                    '-b:a', profile['audio_bitrate'],
                    '-hls_time', str(self.segment_time),
                    '-hls_playlist_type', 'vod',
                    '-hls_flags', 'independent_segments',
                    '-threads', 'auto',
                    '-hls_segment_filename', segments_path,
                    variant_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    raise Exception(f"Error al crear stream {quality}: {result.stderr}")
                
                # Agregar entrada al master playlist
                bandwidth = int(bitrate[:-1]) * 1000
                master_content += f'#EXT-X-STREAM-INF:BANDWIDTH={bandwidth},RESOLUTION={target_width}x{target_height}\n'
                master_content += f'{quality}.m3u8\n'
            
            # Guardar master playlist
            with open(os.path.join(self.output_dir, 'master.m3u8'), 'w') as f:
                f.write(master_content)
            
            return True
            
        except Exception as e:
            print(f"Error en la transcodificación: {str(e)}")
            return False

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