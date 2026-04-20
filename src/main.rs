// SpotiCry - Servidor de música | Lenguajes de Programación
// Punto de entrada: inicia el servidor TCP y crea un hilo por cliente.

mod handlers;
mod models;
mod playlist;
mod protocol;

use std::io::{BufRead, BufReader, Write};
use std::net::{TcpListener, TcpStream};
use std::sync::{Arc, Mutex};
use std::thread;

use models::AppState;
use protocol::{Command, Response};

/// Atiende la conexión de un cliente en su propio hilo.
/// Protocolo: cada mensaje es una línea JSON terminada en '\n'.
fn handle_client(stream: TcpStream, state: Arc<Mutex<AppState>>) {
    let addr = stream.peer_addr().unwrap();
    println!("✅ Nuevo cliente conectado: {}", addr);

    // BufReader permite leer línea por línea en lugar de byte a byte
    let reader = BufReader::new(stream.try_clone().unwrap());
    let mut writer = stream;

    for line in reader.lines() {
        match line {
            Ok(raw) if raw.trim().is_empty() => continue,
            Ok(raw) => {
                println!("📨 [{}] Recibido: {}", addr, raw);

                // Parsear JSON → Command; responder con error si el formato es inválido
                let response = match serde_json::from_str::<Command>(&raw) {
                    Ok(cmd)  => handlers::route_command(&state, cmd),
                    Err(err) => Response::error(&format!("JSON inválido: {}", err)),
                };

                // Serializar y enviar la respuesta terminada en '\n' (delimitador de mensajes)
                let mut json_out = serde_json::to_string(&response).unwrap();
                json_out.push('\n');

                if let Err(e) = writer.write_all(json_out.as_bytes()) {
                    println!("❌ [{}] Error enviando respuesta: {}", addr, e);
                    break;
                }

                println!("📤 [{}] Respuesta: {}", addr, json_out.trim());
            }
            Err(_) => break, // error de lectura = cliente desconectado
        }
    }

    println!("❌ Cliente desconectado: {}", addr);
}

fn main() {
    let address = "127.0.0.1:7878";

    // Arc<Mutex<T>>: Arc comparte el puntero entre hilos sin copiar datos;
    // Mutex garantiza que solo un hilo modifica el estado a la vez.
    let state: Arc<Mutex<AppState>> = Arc::new(Mutex::new(AppState::new()));

    let listener = TcpListener::bind(address).expect("❌ No se pudo iniciar el servidor");
    println!("🚀 Servidor SpotiCry escuchando en {}", address);
    println!("📝 Esperando conexiones...\n");

    for stream in listener.incoming() {
        match stream {
            Ok(stream) => {
                let state_clone = Arc::clone(&state); // clonar el puntero, no los datos
                thread::spawn(move || {
                    handle_client(stream, state_clone);
                });
            }
            Err(e) => println!("❌ Error aceptando conexión: {}", e),
        }
    }
}
