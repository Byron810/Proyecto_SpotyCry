"""
Módulo de conexión TCP con el servidor SpotiCry.
Maneja el protocolo JSON sobre TCP con delimitador de nueva línea.
"""

import socket
import json


class ServerConnection:
    def __init__(self, host='127.0.0.1', port=7878):
        self.host = host
        self.port = port
        self._socket = None
        self.connected = False

    def connect(self) -> tuple[bool, str | None]:
        """Establece conexión con el servidor. Retorna (éxito, mensaje_error)."""
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(5.0)
            self._socket.connect((self.host, self.port))
            self._socket.settimeout(10.0)
            self.connected = True
            return True, None
        except ConnectionRefusedError:
            self.connected = False
            return False, f"Conexión rechazada en {self.host}:{self.port}. ¿Está el servidor corriendo?"
        except socket.timeout:
            self.connected = False
            return False, f"Tiempo de espera agotado conectando a {self.host}:{self.port}"
        except Exception as e:
            self.connected = False
            return False, str(e)

    def disconnect(self):
        """Cierra la conexión con el servidor."""
        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
        self._socket = None
        self.connected = False

    def send_command(self, cmd: str, payload: dict = None) -> tuple[dict | None, str | None]:
        """
        Envía un comando al servidor y retorna la respuesta.
        Retorna (respuesta_dict, mensaje_error).
        """
        if not self.connected:
            return None, "No hay conexión con el servidor"

        if payload is None:
            payload = {}

        message = json.dumps({"cmd": cmd, "payload": payload}) + "\n"

        try:
            self._socket.sendall(message.encode('utf-8'))

            response_data = b""
            while True:
                chunk = self._socket.recv(65536)
                if not chunk:
                    self.connected = False
                    return None, "El servidor cerró la conexión"
                response_data += chunk
                if b'\n' in response_data:
                    break

            first_line = response_data.decode('utf-8').split('\n')[0].strip()
            return json.loads(first_line), None

        except socket.timeout:
            return None, "Tiempo de espera agotado esperando respuesta del servidor"
        except json.JSONDecodeError as e:
            return None, f"Respuesta inválida del servidor: {e}"
        except Exception as e:
            self.connected = False
            return None, str(e)

    def ping(self) -> bool:
        """Verifica si la conexión sigue activa."""
        resp, err = self.send_command("PING")
        return err is None and resp is not None and resp.get("status") == "ok"
