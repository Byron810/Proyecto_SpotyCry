import socket
import sys

class ClienteSpotiCry:
    def __init__(self, host='127.0.0.1', port=7878):
        self.host = host
        self.port = port
        self.socket = None
    
    def conectar(self):
        """Establece conexión con el servidor"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            print(f"✅ Conectado al servidor {self.host}:{self.port}")
            return True
        except ConnectionRefusedError:
            print("❌ Error: No se pudo conectar. ¿Está el servidor ejecutándose?")
            return False
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            return False
    
    def enviar_mensaje(self, mensaje):
        """Envía un mensaje y espera respuesta"""
        try:
            # Enviar mensaje (codificado a bytes)
            self.socket.send(mensaje.encode('utf-8'))
            print(f"📤 Enviado: {mensaje}")
            
            # Recibir respuesta
            respuesta = self.socket.recv(1024).decode('utf-8')
            print(f"📨 Respuesta del servidor: {respuesta}")
            return respuesta
            
        except BrokenPipeError:
            print("❌ Conexión perdida con el servidor")
            return None
        except Exception as e:
            print(f"❌ Error en comunicación: {e}")
            return None
    
    def desconectar(self):
        """Cierra la conexión"""
        if self.socket:
            self.socket.close()
            print("👋 Desconectado del servidor")
    
    def menu_interactivo(self):
        """Menú simple para probar la comunicación"""
        print("\n" + "="*50)
        print("🎵 SpotiCry - Cliente de Prueba")
        print("="*50)
        print("Comandos disponibles:")
        print("  /ping     - Probar conexión")
        print("  /search   - Simular búsqueda")
        print("  /quit     - Salir")
        print("-"*50)
        
        while True:
            comando = input("\n> ").strip()
            
            if comando.lower() == '/quit':
                break
            elif comando.lower() == '/ping':
                self.enviar_mensaje('{"cmd": "PING"}')
            elif comando.lower() == '/search':
                artista = input("Artista a buscar: ")
                mensaje = f'{{"cmd": "SEARCH", "criterion": "artist", "query": "{artista}"}}'
                self.enviar_mensaje(mensaje)
            elif comando:
                self.enviar_mensaje(comando)

def main():
    cliente = ClienteSpotiCry()
    
    if cliente.conectar():
        try:
            cliente.menu_interactivo()
        except KeyboardInterrupt:
            print("\n\n⚠️ Interrupción por usuario")
        finally:
            cliente.desconectar()

if __name__ == "__main__":
    main()