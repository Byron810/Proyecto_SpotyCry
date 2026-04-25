"""
SpotiCry - Cliente con Streaming de Audio (VERSIÓN FINAL)
Descarga completa, reproducción secuencial, barra de progreso y seeking.
"""

import socket
import json
import base64
import threading
import time
import tempfile
import os

import pygame

class SpotiCryStreamingClient:
    def __init__(self, host='127.0.0.1', port=7878):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        
        self.current_song_id = None
        self.current_song_info = None
        self.file_size = 0
        self.downloaded_bytes = 0
        self.is_downloading = False
        self.is_playing = False
        self.is_paused = False
        self.seek_requested = None  # (position_seconds)
        
        self.temp_path = None
        
        # Callback para actualizar GUI
        self.on_status = None
        self.on_progress = None  # (current_seconds, total_seconds)
        
        pygame.init()
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
        print("🎵 Pygame inicializado")
    
    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            print(f"✅ Conectado al servidor {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"❌ Error de conexión: {e}")
            return False
    
    def disconnect(self):
        self.stop()
        if self.socket:
            self.socket.close()
        self.connected = False
        pygame.quit()
        print("👋 Desconectado")
    
    def send_command(self, cmd, payload=None):
        if not self.connected:
            return None
        if payload is None:
            payload = {}
        message = {"cmd": cmd, "payload": payload}
        try:
            json_str = json.dumps(message) + "\n"
            self.socket.send(json_str.encode('utf-8'))
            response_data = b""
            while True:
                chunk = self.socket.recv(65536)
                if not chunk:
                    break
                response_data += chunk
                if b'\n' in chunk:
                    break
            lines = response_data.decode('utf-8').strip().split('\n')
            if lines:
                return json.loads(lines[0])
            return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def list_songs(self):
        return self.send_command("LIST_SONGS")
    
    def play_song(self, song_id):
        """Descarga y reproduce una canción. Retorna True si inicia correctamente."""
        self.stop()
        self.current_song_id = song_id
        
        response = self.send_command("PLAY", {"song_id": song_id})
        
        if not response or response.get("status") != "ok":
            print(f"❌ Error: {response}")
            return False
        
        data = response.get("data", {})
        self.current_song_info = data.get("song", {})
        self.file_size = data.get("file_size", 0)
        
        # Crear archivo en carpeta cache fija (mejor para seeking)
        cache_dir = os.path.join(os.path.dirname(__file__), "_cache")
        os.makedirs(cache_dir, exist_ok=True)
        self.temp_path = os.path.join(cache_dir, f"song_{song_id}.mp3")
        
        chunk_b64 = data.get("chunk", "")
        if chunk_b64:
            chunk_bytes = base64.b64decode(chunk_b64)
            with open(self.temp_path, 'wb') as f:
                f.write(chunk_bytes)
            self.downloaded_bytes = len(chunk_bytes)
        
        song_name = self.current_song_info.get('name', 'Desconocida')
        duration = self.current_song_info.get('duration_secs', 0)
        
        if self.on_status:
            self.on_status(f"Descargando: {song_name}")
        
        self.is_downloading = True
        self.is_playing = True
        self.seek_requested = None
        
        # Descargar en hilo
        threading.Thread(target=self._download_full, daemon=True).start()
        
        return True
    
    def _download_full(self):
        """Descarga la canción completa."""
        while self.is_downloading and self.downloaded_bytes < self.file_size:
            response = self.send_command("SEEK", {
                "song_id": self.current_song_id,
                "offset": self.downloaded_bytes
            })
            
            if response and response.get("status") == "ok":
                data = response.get("data", {})
                chunk_b64 = data.get("chunk", "")
                if chunk_b64:
                    chunk_bytes = base64.b64decode(chunk_b64)
                    try:
                        with open(self.temp_path, 'ab') as f:
                            f.write(chunk_bytes)
                    except:
                        pass
                    self.downloaded_bytes += len(chunk_bytes)
                    
                    if self.on_progress and self.file_size > 0:
                        percent = (self.downloaded_bytes * 100) // self.file_size
                        self.on_progress(percent, 100)
            else:
                time.sleep(0.1)
        
        if self.downloaded_bytes >= self.file_size:
            print("DEBUG: Descarga completa, iniciando playback")
            self.is_downloading = False
            self._start_playback()
            return
        
        self.is_downloading = False
        
    def _start_playback(self):
        """Inicia reproducción con monitoreo de progreso."""
        if not self.is_playing or not self.temp_path:
            return
        
        try:
            time.sleep(0.2)
            pygame.mixer.music.load(self.temp_path)
            pygame.mixer.music.play()
            
            song_name = self.current_song_info.get('name', '')
            duration = self.current_song_info.get('duration_secs', 0)
            
            if self.on_status:
                self.on_status(f"Reproduciendo: {song_name}")
            
            # Monitorear reproducción
            self._start_time = time.time()
            self._seek_offset = 0.0
            
            while self.is_playing:
                if self.is_paused:
                    time.sleep(0.2)
                    continue
                
               
                # Reportar progreso
                elapsed = time.time() - self._start_time
                if self.on_progress and duration > 0:
                    self.on_progress(int(elapsed), duration)
                
                # Verificar fin
                if not pygame.mixer.music.get_busy():
                    time.sleep(0.3)
                    if not pygame.mixer.music.get_busy():
                        if self.on_status:
                            self.on_status(f"Terminó: {song_name}")
                        break
                
                time.sleep(0.3)
            
            self.is_playing = False
            
        except Exception as e:
            print(f"❌ Error reproduciendo: {e}")
            self.is_playing = False
    
    def _get_current_position(self):
        """Retorna la posición actual en segundos."""
        if self.is_paused:
            return self._seek_offset
        if hasattr(self, '_start_time'):
            return time.time() - self._start_time
        return 0
    
    def stop(self):
        """Detiene reproducción y libera recursos."""
        self._start_time = 0
        self._seek_offset = 0.0
        self.is_playing = False
        self.is_downloading = False
        self.seek_requested = None
        
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
        
        time.sleep(0.3)
        
        if self.temp_path and os.path.exists(self.temp_path):
            try:
                os.unlink(self.temp_path)
            except:
                pass
        
        self.temp_path = None
        self.current_song_id = None
        self.downloaded_bytes = 0
    
    def pause(self):
        if not self.is_playing:
            return
        if self.is_paused:
            pygame.mixer.music.unpause()
            self._start_time = time.time() - self._seek_offset
            self.is_paused = False
        else:
            pygame.mixer.music.pause()
            self._seek_offset = time.time() - self._start_time
            self.is_paused = True
    
    def seek(self, seconds: float):
        """Adelanta/retrocede a una posición en segundos."""
        if not self.is_playing or self.is_downloading:
            return
        
        pos = max(0, seconds)
        duration = self.current_song_info.get('duration_secs', 0)
        if duration > 0 and pos > duration:
            pos = duration
        
        print(f"SEEK a {pos}s")
        
        try:
            # Intentar set_pos primero (no reinicia)
            pygame.mixer.music.set_pos(pos)
            self._start_time = time.time() - pos
            self._seek_offset = pos
            print(f"SEEK exitoso a {pos}s")
        except:
            # Si falla, recargar desde esa posición
            try:
                pygame.mixer.music.stop()
                pygame.mixer.music.play(start=pos)
                self._start_time = time.time() - pos
                self._seek_offset = pos
                print(f"SEEK con play(start={pos})")
            except Exception as e:
                print(f"Error en seek: {e}")
    
    def get_duration(self):
        """Retorna la duración total en segundos."""
        return self.current_song_info.get('duration_secs', 0)