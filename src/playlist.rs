// Operaciones funcionales sobre playlists.
//
// Restricción del proyecto: paradigma funcional, sin mutabilidad.
// Cada función recibe los datos de entrada y devuelve una colección nueva;
// nunca modifica nada en el lugar.

use crate::models::Song;

/// Filtra canciones de una playlist aplicando un predicado (closure).
/// El closure recibe una &Song y decide si incluirla: |s| s.genre == "Rock"
pub fn playlist_filter<F>(songs: &[Song], ids: &[u32], predicate: F) -> Vec<Song>
where
    F: Fn(&Song) -> bool,
{
    ids.iter()
        .filter_map(|id| songs.iter().find(|s| s.id == *id)) // resolver id → Song
        .filter(|s| predicate(s))                             // aplicar criterio
        .cloned()
        .collect()
}

/// Retorna las canciones de una playlist ordenadas por un campo.
/// No modifica la fuente; produce una colección nueva ordenada.
/// Campos válidos: "name", "artist", "album", "duration".
pub fn playlist_sort_by_field(songs: &[Song], ids: &[u32], field: &str) -> Vec<Song> {
    let mut result: Vec<Song> = ids.iter()
        .filter_map(|id| songs.iter().find(|s| s.id == *id))
        .cloned()
        .collect();

    match field {
        "name"     => result.sort_by(|a, b| a.name.cmp(&b.name)),
        "artist"   => result.sort_by(|a, b| a.artist.cmp(&b.artist)),
        "album"    => result.sort_by(|a, b| a.album.cmp(&b.album)),
        "duration" => result.sort_by(|a, b| a.duration_secs.cmp(&b.duration_secs)),
        _          => {} // campo desconocido: mantener orden original
    }

    result
}

/// Calcula la duración total de las canciones de una playlist con fold.
/// fold: acumula un resultado recorriendo los elementos sin variable mutable.
pub fn playlist_total_duration(songs: &[Song], ids: &[u32]) -> u32 {
    ids.iter()
        .filter_map(|id| songs.iter().find(|s| s.id == *id))
        .fold(0u32, |acc, song| acc + song.duration_secs)
}
