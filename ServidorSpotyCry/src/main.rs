use std::io::{Read, Write};
use std::net::{TcpListener, TcpStream};
use std::thread;

/// Maneja la conexión de un cliente individual
fn handle_client(mut stream: TcpStream) {
    // Mostrar información del cliente conectado
    println!("✅ Nuevo cliente conectado desde: {}", stream.peer_addr().unwrap());

    // Buffer para almacenar los datos recibidos
    let mut buffer = [0; 1024];

    loop {
        // Leer datos del cliente
        match stream.read(&mut buffer) {
            Ok(size) => {
                if size == 0 {
                    // Si size es 0, el cliente cerró la conexión
                    println!("❌ Cliente desconectado");
                    break;
                }

                // Convertir bytes recibidos a String
                let received = String::from_utf8_lossy(&buffer[..size]);
                println!("📨 Mensaje recibido: {}", received);

                // Preparar respuesta
                let response = format!("Servidor recibió: '{}'", received.trim());

                // Enviar respuesta al cliente
                if let Err(e) = stream.write(response.as_bytes()) {
                    println!("❌ Error enviando respuesta: {}", e);
                    break;
                }

                // Forzar el envío inmediato
                if let Err(e) = stream.flush() {
                    println!("❌ Error haciendo flush: {}", e);
                    break;
                }

                println!("📤 Respuesta enviada: {}", response);
            }
            Err(e) => {
                println!("❌ Error leyendo del socket: {}", e);
                break;
            }
        }
    }
}

fn main() {
    // Dirección y puerto donde escuchará el servidor
    let address = "127.0.0.1:7878";

    // Crear el listener TCP
    let listener = TcpListener::bind(address).expect("❌ No se pudo iniciar el servidor");
    println!("🚀 Servidor SpotiCry escuchando en {}", address);
    println!("📝 Esperando conexiones...\n");

    // Aceptar conexiones entrantes en un loop infinito
    for stream in listener.incoming() {
        match stream {
            Ok(stream) => {
                // Por cada cliente, crear un nuevo hilo
                thread::spawn(|| {
                    handle_client(stream);
                });
            }
            Err(e) => {
                println!("❌ Error aceptando conexión: {}", e);
            }
        }
    }
}