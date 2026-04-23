// SpotiCry - Servidor de música | Lenguajes de Programación
// Punto de entrada: inicia el servidor TCP y crea un hilo por cliente.

mod handlers;
mod models;
mod persistence;
mod playlist;
mod protocol;
mod streaming;

use std::io::{BufRead, BufReader, Write};
use std::net::{TcpListener, TcpStream};
use std::sync::{Arc, Mutex};
use std::thread;
use std::path::Path;

use models::AppState;
use protocol::{Command, Response};
use serde_json::json;

// ========== PARSER DE COMANDOS QUE RESPETA COMILLAS ==========
fn parse_command(input: &str) -> Vec<String> {
    let mut parts = Vec::new();
    let mut current = String::new();
    let mut in_quotes = false;

    for ch in input.chars() {
        match ch {
            '"' => {
                in_quotes = !in_quotes;
            }
            ' ' if !in_quotes => {
                if !current.is_empty() {
                    parts.push(current.clone());
                    current.clear();
                }
            }
            _ => {
                current.push(ch);
            }
        }
    }

    if !current.is_empty() {
        parts.push(current);
    }

    parts
}

// ========== MANEJO DE CLIENTES TCP ==========
fn handle_client(stream: TcpStream, state: Arc<Mutex<AppState>>) {
    let addr = stream.peer_addr().unwrap();
    println!("✅ Nuevo cliente conectado: {}", addr);

    let reader = BufReader::new(stream.try_clone().unwrap());
    let mut writer = stream;

    for line in reader.lines() {
        match line {
            Ok(raw) if raw.trim().is_empty() => continue,
            Ok(raw) => {
                println!("📨 [{}] Recibido: {}", addr, raw);

                let response = match serde_json::from_str::<Command>(&raw) {
                    Ok(cmd)  => handlers::route_command(&state, cmd),
                    Err(err) => Response::error(&format!("JSON inválido: {}", err)),
                };

                let mut json_out = serde_json::to_string(&response).unwrap();
                json_out.push('\n');

                if let Err(e) = writer.write_all(json_out.as_bytes()) {
                    println!("❌ [{}] Error enviando respuesta: {}", addr, e);
                    break;
                }

                println!("📤 [{}] Respuesta: {}", addr, json_out.trim());
            }
            Err(_) => break,
        }
    }

    println!("❌ Cliente desconectado: {}", addr);
}

// ========== CONSOLA DE ADMINISTRACIÓN ==========
fn admin_console(state: Arc<Mutex<AppState>>) {
    println!("\n╔══════════════════════════════════════════════════════════════╗");
    println!("║           🎵 CONSOLA DE ADMINISTRACIÓN SPOTICRY 🎵           ║");
    println!("╠══════════════════════════════════════════════════════════════╣");
    println!("║  Comandos: add <ruta> | remove <id> | list | playlists       ║");
    println!("╚══════════════════════════════════════════════════════════════╝\n");

    loop {
        print!("admin> ");
        std::io::stdout().flush().unwrap();

        let mut input = String::new();
        std::io::stdin().read_line(&mut input).unwrap();
        let input = input.trim();

        if input.is_empty() { continue; }

        let parts = parse_command(input);
        if parts.is_empty() { continue; }

        match parts[0].as_str() {
            "add" => {
                if parts.len() < 2 {
                    println!("❌ Uso: add <ruta_archivo>");
                    continue;
                }

                let file_path = parts[1].trim_matches('"');
                let path = Path::new(file_path);

                println!("🔍 Verificando: {}", file_path);

                if !path.exists() {
                    println!("❌ El archivo no existe: {}", file_path);
                    continue;
                }

                let file_stem = path.file_stem().unwrap_or_default().to_string_lossy().to_string();

                let payload = json!({
                    "name": file_stem,
                    "artist": "Desconocido",
                    "album": "Desconocido",
                    "genre": "Desconocido",
                    "file_path": file_path,
                    "duration_secs": 0
                });

                let cmd = Command { cmd: "ADD_SONG".to_string(), payload };
                let response = handlers::route_command(&state, cmd);

                if response.status == "ok" {
                    println!("✅ Canción agregada y guardada");
                } else {
                    println!("❌ Error: {}", response.message.unwrap_or_default());
                }
            }

            "list" => {
                let cmd = Command { cmd: "LIST_SONGS".to_string(), payload: json!({}) };
                let response = handlers::route_command(&state, cmd);

                if response.status == "ok" {
                    if let Some(data) = response.data {
                        if let Some(songs) = data.as_array() {
                            for song in songs {
                                let id = song.get("id").and_then(|v| v.as_u64()).unwrap_or(0);
                                let name = song.get("name").and_then(|v| v.as_str()).unwrap_or("");
                                println!("  [ID: {}] {}", id, name);
                            }
                        }
                    }
                }
            }

            "exit" => break,
            "" => continue,
            _ => println!("❌ Comando desconocido: {}", parts[0]),
        }
    }
}

// ========== MAIN ==========
fn main() {
    let address = "127.0.0.1:7878";
    let state: Arc<Mutex<AppState>> = Arc::new(Mutex::new(persistence::load_state()));
    let listener = TcpListener::bind(address).expect("❌ No se pudo iniciar el servidor");

    println!("🚀 Servidor SpotiCry escuchando en {}", address);

    let admin_state = Arc::clone(&state);
    thread::spawn(move || { admin_console(admin_state); });

    println!("📝 Esperando conexiones...\n");

    for stream in listener.incoming() {
        match stream {
            Ok(stream) => {
                let state_clone = Arc::clone(&state);
                thread::spawn(move || { handle_client(stream, state_clone); });
            }
            Err(e) => println!("❌ Error: {}", e),
        }
    }
}
