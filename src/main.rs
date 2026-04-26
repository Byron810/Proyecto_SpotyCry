// SpotiCry - Servidor de música | Lenguajes de Programación
// Punto de entrada: inicia el servidor TCP y crea un hilo por cliente.

mod handlers;
mod models;
mod persistence;
mod playlist;
mod protocol;
mod streaming;

use     std::io::{BufRead, BufReader, Write};
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

            "remove" => {
                if parts.len() < 2 {
                    println!("❌ Uso: remove <id>");
                    continue;
                }
                let id = match parts[1].parse::<u32>() {
                    Ok(v) => v,
                    Err(_) => {
                        println!("❌ ID inválido");
                        continue;
                    }
                };
                let payload = json!({ "id": id });
                let cmd = Command { cmd: "DELETE_SONG".to_string(), payload };
                let response = handlers::route_command(&state, cmd);
                if response.status == "ok" {
                    println!("✅ {}", response.message.unwrap_or_default());
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

use std::fs;

/// Carga metadatos desde catalogo.json y los aplica a las canciones en music/

use serde::Deserialize;

#[derive(Deserialize)]
struct CatalogEntry {
    name: String,
    artist: String,
    album: String,
    genre: String,
    file_path: String,
    duration_secs: u32,
}
fn load_music_with_metadata(state: &Arc<Mutex<AppState>>) {
    let music_dir = Path::new("music");

    // Crear carpeta si no existe
    if !music_dir.exists() {
        println!("📁 Carpeta music/ no encontrada, creando...");
        fs::create_dir_all(music_dir).ok();
        return;
    }

    // Cargar catalogo.json si existe
    let catalog_entries: Vec<CatalogEntry> = {
        let catalog_path = Path::new("catalogo.json");
        if catalog_path.exists() {
            match fs::read_to_string(catalog_path) {
                Ok(json) => match serde_json::from_str::<Vec<CatalogEntry>>(&json) {
                    Ok(entries) => entries,
                    Err(e) => {
                        eprintln!("⚠️  Error parseando catalogo.json: {}", e);
                        Vec::new()
                    }
                },
                Err(_) => Vec::new(),
            }
        } else {
            println!("📁 catalogo.json no encontrado.");
            Vec::new()
        }
    };

    let mut songs_added = 0;
    let mut metadata_updated = 0;

    // Escanear archivos en music/
    if let Ok(entries) = fs::read_dir(music_dir) {
        for entry in entries.flatten() {
            let path = entry.path();

            if !path.is_file() {
                continue;
            }

            let ext = path.extension()
                .and_then(|e| e.to_str())
                .unwrap_or("")
                .to_lowercase();

            if !matches!(ext.as_str(), "mp3" | "wav" | "flac" | "ogg") {
                continue;
            }

            let file_name = path.file_name()
                .unwrap_or_default()
                .to_string_lossy()
                .to_string();

            let file_path = path.to_string_lossy().to_string();

            // Buscar metadatos en catalogo.json
            let catalog_info = catalog_entries.iter().find(|c| {
                let c_name = Path::new(&c.file_path)
                    .file_name()
                    .unwrap_or_default()
                    .to_string_lossy()
                    .to_string();
                c_name == file_name
            });

            // Verificar si ya existe en el catálogo
            let already_exists = {
                let guard = state.lock().unwrap();
                guard.songs.iter().any(|s| {
                    let s_name = Path::new(&s.file_path)
                        .file_name()
                        .unwrap_or_default()
                        .to_string_lossy()
                        .to_string();
                    s_name == file_name
                })
            };

            if already_exists {
                // Actualizar metadatos si es necesario
                if let Some(info) = catalog_info {
                    if let Ok(mut guard) = state.lock() {
                        if let Some(song) = guard.songs.iter_mut().find(|s| {
                            let s_name = Path::new(&s.file_path)
                                .file_name()
                                .unwrap_or_default()
                                .to_string_lossy()
                                .to_string();
                            s_name == file_name
                        }) {
                            if song.artist == "Por clasificar" || song.artist == "Desconocido" {
                                song.name = info.name.clone();
                                song.artist = info.artist.clone();
                                song.album = info.album.clone();
                                song.genre = info.genre.clone();
                                song.duration_secs = info.duration_secs;
                                metadata_updated += 1;
                                println!("   📋 Actualizado: {} -> {}", file_name, info.artist);
                            }
                        }
                    }
                }
            } else {
                // Agregar nueva canción con metadatos si existen
                let name = catalog_info.map_or_else(
                    || path.file_stem().unwrap_or_default().to_string_lossy().to_string(),
                    |c| c.name.clone()
                );
                let artist = catalog_info.map_or_else(
                    || "Por clasificar".to_string(),
                    |c| c.artist.clone()
                );
                let album = catalog_info.map_or_else(
                    || "Por clasificar".to_string(),
                    |c| c.album.clone()
                );
                let genre = catalog_info.map_or_else(
                    || "Por clasificar".to_string(),
                    |c| c.genre.clone()
                );
                let duration = catalog_info.map_or(0, |c| c.duration_secs);

                let payload = serde_json::json!({
                    "name": name,
                    "artist": artist,
                    "album": album,
                    "genre": genre,
                    "file_path": file_path,
                    "duration_secs": duration
                });

                let cmd = Command {
                    cmd: "ADD_SONG".to_string(),
                    payload,
                };

                let response = handlers::route_command(&state, cmd);

                if response.status == "ok" {
                    songs_added += 1;
                    println!("   ✅ Agregada: {} - {}", name, artist);
                }
            }
        }
    }

    let guard = state.lock().unwrap();
    let total = guard.songs.len();
    drop(guard);

    println!("📀 {} cancione(s) en catálogo ({} nuevas, {} actualizadas)",
             total, songs_added, metadata_updated);

    if songs_added > 0 || metadata_updated > 0 {
        if let Ok(s) = state.lock() {
            persistence::save_state(&s);
        }
    }
}

// ========== MAIN ==========
fn main() {
    let address = "127.0.0.1:7878";

    // Cargar estado previo o iniciar vacío
    let app_state = persistence::load_state();
    let state: Arc<Mutex<AppState>> = Arc::new(Mutex::new(app_state));

    let listener = TcpListener::bind(address).expect("❌ No se pudo iniciar el servidor");
    println!("🚀 Servidor SpotiCry escuchando en {}", address);

    // Escanear carpeta music/ y agregar canciones nuevas
    println!("🔍 Escaneando carpeta music/...");
    load_music_with_metadata(&state);

    let admin_state = Arc::clone(&state);
    thread::spawn(move || {
        admin_console(admin_state);
    });

    println!("📝 Esperando conexiones...\n");

    for stream in listener.incoming() {
        match stream {
            Ok(stream) => {
                let state_clone = Arc::clone(&state);
                thread::spawn(move || {
                    handle_client(stream, state_clone);
                });
            }
            Err(e) => println!("❌ Error aceptando conexión: {}", e),
        }
    }
}
