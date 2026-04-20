# SpotiCry – Parte 1: Estructuras de Datos y Protocolo de Comunicación

## 1. Descripción general

El servidor de SpotiCry está escrito en **Rust** y se comunica con los clientes usando **TCP/IP con sockets**. El protocolo de mensajes es **JSON por línea**: cada mensaje del cliente y cada respuesta del servidor es una línea de texto JSON terminada en `\n`.

La concurrencia se maneja con el modelo **un hilo por cliente** (`thread::spawn`). El estado compartido (canciones y playlists) se protege con `Arc<Mutex<AppState>>`.

---

## 2. Estructuras de datos

### `Song` – Canción

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | `u32` | Identificador único autoincremental |
| `name` | `String` | Nombre de la canción |
| `artist` | `String` | Artista o banda |
| `album` | `String` | Álbum al que pertenece |
| `genre` | `String` | Género musical |
| `file_path` | `String` | Ruta local al archivo de audio |
| `duration_secs` | `u32` | Duración en segundos |

Los tres criterios de búsqueda son: **name**, **artist** y **genre**.

### `Playlist` – Lista de reproducción

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | `u32` | Identificador único autoincremental |
| `name` | `String` | Nombre de la playlist |
| `song_ids` | `Vec<u32>` | IDs de las canciones que contiene |

Se almacenan solo los IDs (no copias de las canciones) para evitar duplicar datos en memoria.

### `AppState` – Estado del servidor

Estado global compartido entre todos los hilos:

- `songs`: catálogo completo de canciones
- `playlists`: playlists existentes
- `next_song_id` / `next_playlist_id`: contadores para IDs
- `playing_song_ids`: canciones actualmente en reproducción (no se pueden eliminar)

---

## 3. Protocolo de comunicación

### Formato general

**Comando (cliente → servidor):**
```json
{ "cmd": "NOMBRE_COMANDO", "payload": { ... } }
```

**Respuesta (servidor → cliente):**
```json
{ "status": "ok", "data": { ... } }
{ "status": "ok", "message": "texto" }
{ "status": "error", "message": "descripción del error" }
```

Cada mensaje ocupa exactamente una línea (terminada en `\n`).

---

### Comandos disponibles

#### `PING` – Verificar conexión
```json
{ "cmd": "PING", "payload": {} }
```
Respuesta: `{ "status": "ok", "message": "pong" }`

---

#### `ADD_SONG` – Agregar canción
```json
{
  "cmd": "ADD_SONG",
  "payload": {
    "name": "Bohemian Rhapsody",
    "artist": "Queen",
    "album": "A Night at the Opera",
    "genre": "Rock",
    "file_path": "/music/bohemian.mp3",
    "duration_secs": 354
  }
}
```
Campos obligatorios: `name`, `file_path`.  
Respuesta: objeto `Song` con el `id` asignado.

---

#### `DELETE_SONG` – Eliminar canción
```json
{ "cmd": "DELETE_SONG", "payload": { "id": 1 } }
```
No se permite eliminar si la canción está en reproducción activa.

---

#### `LIST_SONGS` – Listar todas las canciones
```json
{ "cmd": "LIST_SONGS", "payload": {} }
```
Respuesta: array con todas las canciones del catálogo.

---

#### `SEARCH` – Buscar canciones
```json
{
  "cmd": "SEARCH",
  "payload": {
    "name": "bohemian",
    "artist": "",
    "genre": "rock"
  }
}
```
Los tres criterios son opcionales y se combinan con **AND**. Un campo vacío no filtra.  
Los tres criterios técnicamente diferentes son: coincidencia por **nombre**, por **artista** y por **género**.

---

#### `CREATE_PLAYLIST` – Crear playlist
```json
{ "cmd": "CREATE_PLAYLIST", "payload": { "name": "Mis favoritas" } }
```
Respuesta: objeto `Playlist` con el `id` asignado.

---

#### `ADD_TO_PLAYLIST` – Agregar canción a playlist
```json
{ "cmd": "ADD_TO_PLAYLIST", "payload": { "playlist_id": 1, "song_id": 3 } }
```

---

#### `REMOVE_FROM_PLAYLIST` – Eliminar canción de playlist
```json
{ "cmd": "REMOVE_FROM_PLAYLIST", "payload": { "playlist_id": 1, "song_id": 3 } }
```

---

#### `GET_PLAYLIST` – Obtener canciones de una playlist
```json
{
  "cmd": "GET_PLAYLIST",
  "payload": {
    "playlist_id": 1,
    "filter_genre": "rock",
    "sort_by": "name"
  }
}
```
`filter_genre` y `sort_by` son opcionales.  
`sort_by` acepta: `"name"`, `"artist"`, `"album"`, `"duration"`.  
Respuesta incluye las canciones filtradas/ordenadas y la duración total.

---

## 4. Paradigma funcional en playlists

El proyecto exige que las operaciones sobre playlists usen **programación funcional**: sin mutabilidad, con `map`, `filter` y `fold`.

### `playlist_filter` – Filtrar con closure
```rust
// Closure |s| define el predicado; retorna colección nueva
playlist_filter(&songs, &ids, |s| s.genre == "Rock")
```

### `playlist_sort_by_field` – Ordenar sin mutar la fuente
```rust
// Retorna Vec<Song> ordenado; los datos originales no cambian
playlist_sort_by_field(&songs, &ids, "name")
```

### `playlist_total_duration` – Acumular con fold
```rust
// fold acumula la suma sin necesitar variable mutable externa
ids.iter().fold(0u32, |acc, song| acc + song.duration_secs)
```

---

## 5. Concurrencia

| Mecanismo | Propósito |
|---|---|
| `TcpListener` | Acepta conexiones entrantes |
| `thread::spawn` | Crea un hilo por cada cliente conectado |
| `Arc<T>` | Comparte el puntero al estado entre hilos sin copiar datos |
| `Mutex<T>` | Garantiza acceso exclusivo al estado en cada operación |

El `Mutex` se bloquea solo durante la duración del comando (lock → operación → unlock automático), minimizando la contención entre hilos.

---

