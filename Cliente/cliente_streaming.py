"""
SpotiCry - Cliente con Streaming de Audio (VERSIÓN FINAL)
Descarga incremental y reproduce sin errores de permisos.
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
        self.started_playback = False
        
        self.temp_path = None
        
        # Inicializar pygame
        pygame.init()
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=8192)
        print("🎵 Pygame inicializado")
    
    def connect(self):
        """Conecta al servidor."""
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
        """Desconecta del servidor."""
        self.stop()
        if self.socket:
            self.socket.close()
        self.connected = False
        pygame.quit()
        print("👋 Desconectado")
    
    def send_command(self, cmd, payload=None):
        """Envía un comando JSON y retorna la respuesta."""
        if not self.connected:
            print("❌ No hay conexión")
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
            print(f"❌ Error en comunicación: {e}")
            return None
    
    def list_songs(self):
        """Lista todas las canciones."""
        return self.send_command("LIST_SONGS")
    
    def play_song(self, song_id):
        """Descarga y reproduce una canción."""
        self.stop()
        
        self.current_song_id = song_id
        
        response = self.send_command("PLAY", {"song_id": song_id})
        
        if not response or response.get("status") != "ok":
            print(f"❌ Error al reproducir: {response}")
            return False
        
        data = response.get("data", {})
        self.current_song_info = data.get("song", {})
        self.file_size = data.get("file_size", 0)
        
        # Crear archivo temporal
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        self.temp_path = temp_file.name
        temp_file.close()
        
        # Guardar primer chunk
        chunk_b64 = data.get("chunk", "")
        if chunk_b64:
            chunk_bytes = base64.b64decode(chunk_b64)
            with open(self.temp_path, 'wb') as f:
                f.write(chunk_bytes)
            self.downloaded_bytes = len(chunk_bytes)
        
        print(f"📥 Descargando: {self.current_song_info.get('name', 'Desconocida')}")
        print(f"   Tamaño total: {self.file_size} bytes")
        
        self.is_downloading = True
        self.is_playing = True
        self.started_playback = False
        
        # Iniciar hilo de descarga
        threading.Thread(target=self._download_loop, daemon=True).start()
        
        return True
    
    def _download_loop(self):
        """Descarga chunks incrementalmente."""
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
                    
                    # Escribir al archivo (abrir y cerrar para no bloquear)
                    try:
                        with open(self.temp_path, 'ab') as f:
                            f.write(chunk_bytes)
                    except:
                        pass
                    
                    self.downloaded_bytes += len(chunk_bytes)
                    
                    # Mostrar progreso
                    if self.file_size > 0:
                        percent = (self.downloaded_bytes * 100) // self.file_size
                        print(f"   📥 Descargado: {percent}%", end='\r')
                    
                    # Iniciar reproducción cuando tengamos ~15% descargado
                    if not self.started_playback and self.downloaded_bytes > self.file_size * 0.15:
                        self.started_playback = True
                        threading.Thread(target=self._start_playback, daemon=True).start()
            else:
                time.sleep(0.1)
        
        if self.downloaded_bytes >= self.file_size:
            print(f"\n   ✅ Descarga completa: {self.downloaded_bytes} bytes")
            
            # Si aún no empezó la reproducción, iniciarla ahora
            if not self.started_playback:
                self.started_playback = True
                threading.Thread(target=self._start_playback, daemon=True).start()
        
        self.is_downloading = False
    
    def _start_playback(self):
        """Inicia la reproducción del archivo descargado."""
        # Esperar un poco para que el archivo tenga datos suficientes
        time.sleep(1)
        
        if not self.is_playing:
            return
        
        try:
            print(f"\n   ▶️ Iniciando reproducción...")
            pygame.mixer.music.load(self.temp_path)
            pygame.mixer.music.play()
            
            # Monitorear fin de reproducción
            while self.is_playing:
                if not pygame.mixer.music.get_busy() and not self.is_paused:
                    # Si terminó y ya descargó todo
                    if self.downloaded_bytes >= self.file_size and not self.is_downloading:
                        print("\n🏁 Fin de la canción")
                        self.is_playing = False
                        break
                    else:
                        # Esperar más datos
                        time.sleep(0.5)
                else:
                    time.sleep(0.5)
                    
        except Exception as e:
            print(f"\n❌ Error reproduciendo: {e}")
            # Reintentar
            time.sleep(1)
            if self.is_playing:
                try:
                    pygame.mixer.music.load(self.temp_path)
                    pygame.mixer.music.play()
                except:
                    pass
    
    def stop(self):
        """Detiene la reproducción y descarga."""
        self.is_playing = False
        self.is_downloading = False
        self.started_playback = False
        
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
        
        # Pequeña pausa para que pygame libere el archivo
        time.sleep(0.5)
        
        if self.temp_path and os.path.exists(self.temp_path):
            try:
                os.unlink(self.temp_path)
            except:
                pass
        
        self.temp_path = None
        self.current_song_id = None
        self.downloaded_bytes = 0
        print("⏹️ Reproducción detenida")
    
    def pause(self):
        """Pausa/Reanuda la reproducción."""
        if not self.is_playing:
            print("❌ No hay canción reproduciéndose")
            return
        
        if self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False
            print("▶️ Reanudado")
        else:
            pygame.mixer.music.pause()
            self.is_paused = True
            print("⏸️ Pausado")


def main():
    client = SpotiCryStreamingClient()
    
    if not client.connect():
        return
    
    print("\n" + "=" * 50)
    print("🎵 SPOTICRY - CLIENTE STREAMING")
    print("=" * 50)
    print("  /list       - Listar canciones")
    print("  /play <id>  - Reproducir")
    print("  /pause      - Pausar/Reanudar")
    print("  /stop       - Detener")
    print("  /quit       - Salir")
    print("-" * 50)
    
    try:
        while True:
            cmd = input("\n> ").strip()
            
            if not cmd:
                continue
            
            parts = cmd.split(maxsplit=1)
            action = parts[0].lower()
            
            if action == "/quit":
                client.stop()
                break
            
            elif action == "/list":
                response = client.list_songs()
                if response and response.get("status") == "ok":
                    songs = response.get("data", [])
                    if songs:
                        print("\n📀 Canciones disponibles:")
                        for song in songs:
                            print(f"  [ID:{song['id']}] {song['name']} - {song['artist']}")
                    else:
                        print("📭 No hay canciones")
            
            elif action == "/play":
                if len(parts) < 2:
                    print("❌ Uso: /play <id>")
                else:
                    try:
                        song_id = int(parts[1])
                        client.play_song(song_id)
                    except ValueError:
                        print("❌ ID debe ser un número")
            
            elif action == "/pause":
                client.pause()
            
            elif action == "/stop":
                client.stop()
            
            else:
                print(f"❌ Comando desconocido: {action}")
                
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupción por usuario")
    finally:
        client.disconnect()


if __name__ == "__main__":
    main()