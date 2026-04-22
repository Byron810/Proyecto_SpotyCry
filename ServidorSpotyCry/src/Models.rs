// Estructuras de datos del dominio: canciones, playlists y estado global.

use serde::{Deserialize, Serialize};

/// Una canción almacenada en el servidor.
/// Los tres criterios de búsqueda son: name, artist, genre.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Song {
    pub id: u32,
    pub name: String,
    pub artist: String,
    pub album: String,
    pub genre: String,       // tercer criterio de búsqueda
    pub file_path: String,   // ruta local al archivo de audio
    pub duration_secs: u32,
}

/// Una playlist que referencia canciones por ID para no duplicar datos.
/// Las transformaciones sobre sus canciones se hacen de forma funcional.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Playlist {
    pub id: u32,
    pub name: String,
    pub song_ids: Vec<u32>,
}

/// Estado global compartido entre todos los hilos del servidor.
/// Se envuelve en Arc<Mutex<T>> en main para acceso concurrente seguro.
#[derive(Debug)]
pub struct AppState {
    pub songs: Vec<Song>,
    pub playlists: Vec<Playlist>,
    pub next_song_id: u32,
    pub next_playlist_id: u32,
    /// IDs de canciones en reproducción activa; no se pueden eliminar.
    pub playing_song_ids: Vec<u32>,
}

impl AppState {
    pub fn new() -> Self {
        AppState {
            songs: Vec::new(),
            playlists: Vec::new(),
            next_song_id: 1,
            next_playlist_id: 1,
            playing_song_ids: Vec::new(),
        }
    }
}