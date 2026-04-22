// Handlers de cada comando y función de routing.
// Cada cmd_* recibe el estado y el payload del comando, y devuelve una Response.

use std::sync::{Arc, Mutex};

use serde_json::Value;

use crate::models::{AppState, Playlist, Song};
use crate::playlist::{playlist_filter, playlist_sort_by_field, playlist_total_duration};
use crate::protocol::{Command, Response};

// ─── CANCIONES ───────────────────────────────────────────────

/// Agrega una nueva canción al catálogo.
/// Payload: { name, artist, album, genre, file_path, duration_secs }
pub fn cmd_add_song(state: &mut AppState, payload: &Value) -> Response {
    let name      = payload["name"].as_str().unwrap_or("").to_string();
    let artist    = payload["artist"].as_str().unwrap_or("").to_string();
    let album     = payload["album"].as_str().unwrap_or("").to_string();
    let genre     = payload["genre"].as_str().unwrap_or("").to_string();
    let file_path = payload["file_path"].as_str().unwrap_or("").to_string();
    let duration  = payload["duration_secs"].as_u64().unwrap_or(0) as u32;

    if name.is_empty() || file_path.is_empty() {
        return Response::error("Faltan campos obligatorios: name, file_path");
    }

    let song = Song {
        id: state.next_song_id,
        name,
        artist,
        album,
        genre,
        file_path,
        duration_secs: duration,
    };

    state.next_song_id += 1;
    state.songs.push(song.clone());

    println!("🎵 Canción agregada: {} (id={})", song.name, song.id);
    Response::ok(serde_json::to_value(&song).unwrap())
}

/// Elimina una canción por ID.
/// No se permite eliminar si la canción está siendo reproducida.
/// Payload: { id }
pub fn cmd_delete_song(state: &mut AppState, payload: &Value) -> Response {
    let id = match payload["id"].as_u64() {
        Some(v) => v as u32,
        None    => return Response::error("Se requiere campo 'id'"),
    };

    if state.playing_song_ids.contains(&id) {
        return Response::error("No se puede eliminar: la canción está en reproducción");
    }

    let before = state.songs.len();
    state.songs.retain(|s| s.id != id); // retain: elimina el elemento con ese id

    if state.songs.len() < before {
        println!("🗑️  Canción eliminada id={}", id);
        Response::ok_msg(&format!("Canción {} eliminada correctamente", id))
    } else {
        Response::error("Canción no encontrada")
    }
}

/// Devuelve todas las canciones del catálogo.
pub fn cmd_list_songs(state: &AppState) -> Response {
    Response::ok(serde_json::to_value(&state.songs).unwrap())
}

/// Busca canciones por hasta 3 criterios combinados con AND.
/// Criterios: name, artist, genre. Un campo vacío no filtra.
/// Payload: { name?, artist?, genre? }
pub fn cmd_search(state: &AppState, payload: &Value) -> Response {
    let name_q   = payload["name"].as_str().unwrap_or("").to_lowercase();
    let artist_q = payload["artist"].as_str().unwrap_or("").to_lowercase();
    let genre_q  = payload["genre"].as_str().unwrap_or("").to_lowercase();

    // Cada filter es un criterio independiente; criterio vacío pasa todo
    let results: Vec<&Song> = state.songs.iter()
        .filter(|s| name_q.is_empty()   || s.name.to_lowercase().contains(&name_q))
        .filter(|s| artist_q.is_empty() || s.artist.to_lowercase().contains(&artist_q))
        .filter(|s| genre_q.is_empty()  || s.genre.to_lowercase().contains(&genre_q))
        .collect();

    println!("🔍 Búsqueda: {} resultado(s)", results.len());
    Response::ok(serde_json::to_value(&results).unwrap())
}

// ─── PLAYLISTS ───────────────────────────────────────────────

/// Crea una nueva playlist vacía.
/// Payload: { name }
pub fn cmd_create_playlist(state: &mut AppState, payload: &Value) -> Response {
    let name = payload["name"].as_str().unwrap_or("").to_string();
    if name.is_empty() {
        return Response::error("Se requiere campo 'name'");
    }

    let playlist = Playlist {
        id: state.next_playlist_id,
        name,
        song_ids: Vec::new(),
    };

    state.next_playlist_id += 1;
    state.playlists.push(playlist.clone());

    println!("📋 Playlist creada: {} (id={})", playlist.name, playlist.id);
    Response::ok(serde_json::to_value(&playlist).unwrap())
}

/// Agrega una canción existente a una playlist.
/// Payload: { playlist_id, song_id }
pub fn cmd_add_to_playlist(state: &mut AppState, payload: &Value) -> Response {
    let playlist_id = match payload["playlist_id"].as_u64() {
        Some(v) => v as u32,
        None    => return Response::error("Se requiere 'playlist_id'"),
    };
    let song_id = match payload["song_id"].as_u64() {
        Some(v) => v as u32,
        None    => return Response::error("Se requiere 'song_id'"),
    };

    if !state.songs.iter().any(|s| s.id == song_id) {
        return Response::error("Canción no encontrada");
    }

    match state.playlists.iter_mut().find(|p| p.id == playlist_id) {
        Some(playlist) => {
            if playlist.song_ids.contains(&song_id) {
                return Response::error("La canción ya está en la playlist");
            }
            playlist.song_ids.push(song_id);
            Response::ok_msg("Canción agregada a la playlist")
        }
        None => Response::error("Playlist no encontrada"),
    }
}

/// Elimina una canción de una playlist específica.
/// Payload: { playlist_id, song_id }
pub fn cmd_remove_from_playlist(state: &mut AppState, payload: &Value) -> Response {
    let playlist_id = match payload["playlist_id"].as_u64() {
        Some(v) => v as u32,
        None    => return Response::error("Se requiere 'playlist_id'"),
    };
    let song_id = match payload["song_id"].as_u64() {
        Some(v) => v as u32,
        None    => return Response::error("Se requiere 'song_id'"),
    };

    match state.playlists.iter_mut().find(|p| p.id == playlist_id) {
        Some(playlist) => {
            let before = playlist.song_ids.len();
            playlist.song_ids.retain(|id| *id != song_id);
            if playlist.song_ids.len() < before {
                Response::ok_msg("Canción eliminada de la playlist")
            } else {
                Response::error("La canción no estaba en la playlist")
            }
        }
        None => Response::error("Playlist no encontrada"),
    }
}

/// Devuelve las canciones de una playlist con filtrado y ordenamiento opcionales.
/// Usa las operaciones funcionales de playlist.rs (filter, sort, fold).
/// Payload: { playlist_id, filter_genre?, sort_by? }
pub fn cmd_get_playlist(state: &AppState, payload: &Value) -> Response {
    let playlist_id = match payload["playlist_id"].as_u64() {
        Some(v) => v as u32,
        None    => return Response::error("Se requiere 'playlist_id'"),
    };

    let playlist = match state.playlists.iter().find(|p| p.id == playlist_id) {
        Some(p) => p,
        None    => return Response::error("Playlist no encontrada"),
    };

    // Filtrado funcional por género; closure captura el valor buscado
    let filter_genre = payload["filter_genre"].as_str().unwrap_or("").to_lowercase();
    let songs = if filter_genre.is_empty() {
        playlist_filter(&state.songs, &playlist.song_ids, |_| true)
    } else {
        let genre = filter_genre.clone();
        playlist_filter(&state.songs, &playlist.song_ids, move |s| {
            s.genre.to_lowercase().contains(&genre)
        })
    };

    // Ordenamiento por campo; retorna colección nueva sin tocar la original
    let sort_by = payload["sort_by"].as_str().unwrap_or("");
    let songs = if sort_by.is_empty() {
        songs
    } else {
        playlist_sort_by_field(&state.songs, &playlist.song_ids, sort_by)
    };

    // Duración total acumulada con fold
    let total_duration = playlist_total_duration(&state.songs, &playlist.song_ids);

    Response::ok(serde_json::json!({
        "playlist": playlist,
        "songs": songs,
        "total_duration_secs": total_duration,
    }))
}

// ─── STREAMING DE AUDIO ───────────────────────────────────────

use crate::streaming;

/// Inicia la reproducción de una canción.
/// Retorna información del archivo y el primer chunk de audio.
/// Payload: { song_id }
pub fn cmd_play(state: &mut AppState, payload: &Value) -> Response {
    let song_id = match payload["song_id"].as_u64() {
        Some(v) => v as u32,
        None => return Response::error("Se requiere 'song_id'"),
    };

    let song = match state.songs.iter().find(|s| s.id == song_id) {
        Some(s) => s.clone(),
        None => return Response::error("Canción no encontrada"),
    };

    if !streaming::is_supported_audio(&song.file_path) {
        return Response::error("Formato de audio no soportado");
    }

    let file_size = match streaming::get_file_size(&song.file_path) {
        Ok(sz) => sz,
        Err(e) => return Response::error(&e),
    };

    let chunk = match streaming::read_audio_chunk(&song.file_path, 0, 8192) {
        Ok(c) => c,
        Err(e) => return Response::error(&e),
    };

    if !state.playing_song_ids.contains(&song_id) {
        state.playing_song_ids.push(song_id);
    }

    println!("▶️  Reproduciendo: {} ({} bytes totales)", song.name, file_size);

    use base64::{Engine as _, engine::general_purpose::STANDARD as BASE64};
    let chunk_b64 = BASE64.encode(&chunk);

    Response::ok(serde_json::json!({
        "song": song,
        "file_size": file_size,
        "chunk": chunk_b64,
        "chunk_size": chunk.len(),
        "offset": 0,
        "eof": chunk.len() == 0
    }))
}

/// Obtiene un chunk de audio desde una posición específica (para seeking).
/// Payload: { song_id, offset }
pub fn cmd_seek(state: &AppState, payload: &Value) -> Response {
    let song_id = match payload["song_id"].as_u64() {
        Some(v) => v as u32,
        None => return Response::error("Se requiere 'song_id'"),
    };

    let offset = match payload["offset"].as_u64() {
        Some(v) => v,
        None => return Response::error("Se requiere 'offset'"),
    };

    let song = match state.songs.iter().find(|s| s.id == song_id) {
        Some(s) => s,
        None => return Response::error("Canción no encontrada"),
    };

    let chunk = match streaming::read_audio_chunk(&song.file_path, offset, 8192) {
        Ok(c) => c,
        Err(e) => return Response::error(&e),
    };

    use base64::{Engine as _, engine::general_purpose::STANDARD as BASE64};
    let chunk_b64 = BASE64.encode(&chunk);

    Response::ok(serde_json::json!({
        "chunk": chunk_b64,
        "chunk_size": chunk.len(),
        "offset": offset,
        "eof": chunk.len() == 0
    }))
}

/// Detiene la reproducción de una canción.
/// Payload: { song_id }
pub fn cmd_stop(state: &mut AppState, payload: &Value) -> Response {
    let song_id = match payload["song_id"].as_u64() {
        Some(v) => v as u32,
        None => return Response::error("Se requiere 'song_id'"),
    };

    state.playing_song_ids.retain(|&id| id != song_id);

    println!("⏹️  Reproducción detenida: id={}", song_id);
    Response::ok_msg(&format!("Canción {} detenida", song_id))
}

// ─── ROUTING ─────────────────────────────────────────────────

/// Despacha un comando al handler correspondiente.
/// Bloquea el Mutex solo durante la operación y lo libera al terminar.
pub fn route_command(state: &Arc<Mutex<AppState>>, command: Command) -> Response {
    match command.cmd.as_str() {
        "PING" => Response::ok_msg("pong"),

        "ADD_SONG" => {
            let mut s = state.lock().unwrap();
            cmd_add_song(&mut s, &command.payload)
        }
        "DELETE_SONG" => {
            let mut s = state.lock().unwrap();
            cmd_delete_song(&mut s, &command.payload)
        }
        "LIST_SONGS" => {
            let s = state.lock().unwrap();
            cmd_list_songs(&s)
        }
        "SEARCH" => {
            let s = state.lock().unwrap();
            cmd_search(&s, &command.payload)
        }
        "CREATE_PLAYLIST" => {
            let mut s = state.lock().unwrap();
            cmd_create_playlist(&mut s, &command.payload)
        }
        "ADD_TO_PLAYLIST" => {
            let mut s = state.lock().unwrap();
            cmd_add_to_playlist(&mut s, &command.payload)
        }
        "REMOVE_FROM_PLAYLIST" => {
            let mut s = state.lock().unwrap();
            cmd_remove_from_playlist(&mut s, &command.payload)
        }
        "GET_PLAYLIST" => {
            let s = state.lock().unwrap();
            cmd_get_playlist(&s, &command.payload)
        }
        "PLAY" => {
            let mut s = state.lock().unwrap();
            cmd_play(&mut s, &command.payload)
        }
        "SEEK" => {
            let s = state.lock().unwrap();
            cmd_seek(&s, &command.payload)
        }
        "STOP" => {
            let mut s = state.lock().unwrap();
            cmd_stop(&mut s, &command.payload)
        }

        unknown => {
            println!("⚠️  Comando desconocido: {}", unknown);
            Response::error(&format!("Comando desconocido: {}", unknown))
        }
    }
}
