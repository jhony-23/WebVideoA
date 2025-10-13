"""
Comando Django para gestión automática de streaming
Horarios: Lunes a Viernes 7:30 AM - 6:00 PM
Funciones: Auto-inicio, monitoreo, limpieza, auto-reinicio
"""

import os
import subprocess
import logging
from datetime import datetime, time
from django.core.management.base import BaseCommand
from django.conf import settings
from videos.models import Media
import psutil
import glob

# Configurar logging
log_dir = os.path.join(os.path.dirname(settings.BASE_DIR), 'logs')
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'streaming_auto.log')),
        logging.StreamHandler()
    ]
)

class Command(BaseCommand):
    help = 'Gestión automática de streaming con horarios de oficina'
    
    def __init__(self):
        super().__init__()
        self.streaming_process = None
        self.current_media = None
        
        # Configuración de horarios (Guatemala timezone)
        self.HORARIO_INICIO = time(7, 30)  # 7:30 AM
        self.HORARIO_FIN = time(18, 0)     # 6:00 PM
        self.DIAS_LABORALES = [0, 1, 2, 3, 4]  # Lunes=0 a Viernes=4
        
    def add_arguments(self, parser):
        parser.add_argument(
            '--modo',
            type=str,
            choices=['monitor', 'iniciar', 'parar', 'limpiar', 'status'],
            default='monitor',
            help='Modo de operación del comando'
        )
        
        parser.add_argument(
            '--forzar',
            action='store_true',
            help='Forzar acción ignorando horarios'
        )

    def handle(self, *args, **options):
        modo = options['modo']
        forzar = options['forzar']
        
        self.stdout.write(f"🤖 Iniciando streaming automático - Modo: {modo}")
        logging.info(f"Comando ejecutado - Modo: {modo}, Forzar: {forzar}")
        
        if modo == 'monitor':
            self.monitorear_streaming(forzar)
        elif modo == 'iniciar':
            self.iniciar_streaming(forzar)
        elif modo == 'parar':
            self.parar_streaming()
        elif modo == 'limpiar':
            self.limpiar_archivos_temporales()
        elif modo == 'status':
            self.mostrar_status()
    
    def es_horario_oficina(self):
        """Determina si estamos en horario de oficina"""
        ahora = datetime.now()
        
        # Verificar si es día laboral
        if ahora.weekday() not in self.DIAS_LABORALES:
            return False, "Fin de semana"
            
        # Verificar horario
        hora_actual = ahora.time()
        if self.HORARIO_INICIO <= hora_actual <= self.HORARIO_FIN:
            return True, "Horario de oficina"
        else:
            return False, f"Fuera de horario ({self.HORARIO_INICIO} - {self.HORARIO_FIN})"
    
    def monitorear_streaming(self, forzar=False):
        """Monitorea y gestiona el streaming automáticamente"""
        self.stdout.write("🔍 Monitoreando streaming...")
        
        en_horario, razon = self.es_horario_oficina()
        streaming_activo = self.verificar_streaming_activo()
        
        self.stdout.write(f"⏰ Horario: {razon}")
        self.stdout.write(f"📡 Streaming activo: {'Sí' if streaming_activo else 'No'}")
        
        if forzar or en_horario:
            if not streaming_activo:
                self.stdout.write("🚀 Iniciando streaming automático...")
                self.iniciar_streaming(forzar=True)
            else:
                # Verificar que el proceso esté funcionando bien
                if not self.verificar_salud_proceso():
                    self.stdout.write("⚠️ Problema detectado, reiniciando...")
                    self.parar_streaming()
                    self.iniciar_streaming(forzar=True)
                else:
                    self.stdout.write("✅ Streaming funcionando correctamente")
        else:
            if streaming_activo:
                self.stdout.write("🛑 Parando streaming fuera de horario...")
                self.parar_streaming()
        
        # Limpieza periódica
        self.limpiar_archivos_temporales()
    
    def iniciar_streaming(self, forzar=False):
        """Inicia el streaming automáticamente"""
        en_horario, razon = self.es_horario_oficina()
        
        if not forzar and not en_horario:
            self.stdout.write(f"❌ No se puede iniciar: {razon}")
            return False
        
        # Parar streaming existente
        if self.verificar_streaming_activo():
            self.parar_streaming()
        
        # Obtener video por defecto o el primero disponible
        media = self.obtener_media_para_streaming()
        if not media:
            self.stdout.write("❌ No hay videos disponibles para streaming")
            return False
        
        # Iniciar proceso de streaming
        return self.ejecutar_streaming(media)
    
    def obtener_media_para_streaming(self):
        """Obtiene el video para hacer streaming"""
        try:
            # Buscar video marcado como "por defecto" o el primero disponible
            media = Media.objects.filter(file__isnull=False).first()
            if media and os.path.exists(media.file.path):
                return media
        except Exception as e:
            logging.error(f"Error obteniendo media: {e}")
        return None
    
    def ejecutar_streaming(self, media):
        """Ejecuta el comando FFmpeg para streaming"""
        try:
            input_file = media.file.path
            output_dir = os.path.join(settings.MEDIA_ROOT, 'hls', 'live')
            
            # Crear directorio si no existe
            os.makedirs(output_dir, exist_ok=True)
            
            # Comando FFmpeg para streaming HLS
            cmd = [
                'ffmpeg',
                '-re',  # Leer a velocidad nativa
                '-stream_loop', '-1',  # Loop infinito
                '-i', input_file,
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-preset', 'medium',
                '-b:v', '2M',  # Bitrate video
                '-b:a', '128k',  # Bitrate audio
                '-hls_time', '6',  # Duración de segmentos
                '-hls_list_size', '10',  # Número de segmentos en playlist
                '-hls_flags', 'delete_segments',  # Borrar segmentos antiguos
                '-f', 'hls',
                os.path.join(output_dir, 'stream.m3u8')
            ]
            
            # Ejecutar proceso
            self.streaming_process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.current_media = media
            self.stdout.write(f"✅ Streaming iniciado: {media.original_name}")
            logging.info(f"Streaming iniciado - Video: {media.original_name}")
            
            return True
            
        except Exception as e:
            self.stdout.write(f"❌ Error iniciando streaming: {e}")
            logging.error(f"Error iniciando streaming: {e}")
            return False
    
    def parar_streaming(self):
        """Para el streaming actual"""
        try:
            # Buscar procesos FFmpeg
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if proc.info['name'] == 'ffmpeg.exe' or proc.info['name'] == 'ffmpeg':
                    if 'hls' in ' '.join(proc.info['cmdline']):
                        proc.terminate()
                        proc.wait(timeout=10)
                        self.stdout.write(f"🛑 Proceso FFmpeg terminado (PID: {proc.info['pid']})")
                        logging.info(f"Proceso FFmpeg terminado - PID: {proc.info['pid']}")
            
            self.streaming_process = None
            self.current_media = None
            self.stdout.write("✅ Streaming detenido")
            
        except Exception as e:
            self.stdout.write(f"❌ Error parando streaming: {e}")
            logging.error(f"Error parando streaming: {e}")
    
    def verificar_streaming_activo(self):
        """Verifica si hay streaming activo"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if proc.info['name'] == 'ffmpeg.exe' or proc.info['name'] == 'ffmpeg':
                    if 'hls' in ' '.join(proc.info['cmdline']):
                        return True
            return False
        except Exception:
            return False
    
    def verificar_salud_proceso(self):
        """Verifica que el proceso de streaming esté saludable"""
        try:
            # Verificar que se estén generando archivos HLS recientes
            hls_dir = os.path.join(settings.MEDIA_ROOT, 'hls', 'live')
            playlist_file = os.path.join(hls_dir, 'stream.m3u8')
            
            if not os.path.exists(playlist_file):
                return False
            
            # Verificar que el archivo playlist sea reciente (menos de 30 segundos)
            mtime = os.path.getmtime(playlist_file)
            age = datetime.now().timestamp() - mtime
            
            return age < 30  # Archivo debe ser reciente
            
        except Exception as e:
            logging.error(f"Error verificando salud: {e}")
            return False
    
    def limpiar_archivos_temporales(self):
        """Limpia archivos temporales antiguos"""
        try:
            hls_dir = os.path.join(settings.MEDIA_ROOT, 'hls')
            
            # Limpiar archivos .ts antiguos (más de 1 hora)
            pattern = os.path.join(hls_dir, '**', '*.ts')
            archivos_ts = glob.glob(pattern, recursive=True)
            
            eliminados = 0
            for archivo in archivos_ts:
                try:
                    mtime = os.path.getmtime(archivo)
                    age = datetime.now().timestamp() - mtime
                    
                    if age > 3600:  # 1 hora
                        os.remove(archivo)
                        eliminados += 1
                except Exception:
                    pass
            
            if eliminados > 0:
                self.stdout.write(f"🧹 Archivos temporales eliminados: {eliminados}")
                logging.info(f"Limpieza completada - {eliminados} archivos eliminados")
                
        except Exception as e:
            logging.error(f"Error en limpieza: {e}")
    
    def mostrar_status(self):
        """Muestra el estado actual del streaming"""
        self.stdout.write("📊 ESTADO DEL STREAMING AUTOMÁTICO")
        self.stdout.write("=" * 50)
        
        # Horario actual
        en_horario, razon = self.es_horario_oficina()
        self.stdout.write(f"⏰ Horario actual: {razon}")
        
        # Estado del streaming
        activo = self.verificar_streaming_activo()
        self.stdout.write(f"📡 Streaming: {'🟢 ACTIVO' if activo else '🔴 INACTIVO'}")
        
        # Salud del proceso
        if activo:
            saludable = self.verificar_salud_proceso()
            self.stdout.write(f"💚 Salud: {'✅ Buena' if saludable else '⚠️ Problemas detectados'}")
        
        # Archivos HLS
        hls_dir = os.path.join(settings.MEDIA_ROOT, 'hls', 'live')
        playlist_file = os.path.join(hls_dir, 'stream.m3u8')
        
        if os.path.exists(playlist_file):
            mtime = datetime.fromtimestamp(os.path.getmtime(playlist_file))
            self.stdout.write(f"📄 Playlist actualizado: {mtime.strftime('%H:%M:%S')}")
        
        self.stdout.write("=" * 50)