# SpotiCry – Protocolo de comunicación

## Formato general

El protocolo es **JSON por línea** sobre TCP. Cada mensaje es una sola línea terminada en `\n`.

**Cliente → Servidor:**
```json
{ "cmd": "NOMBRE_COMANDO", "payload": { ... } }
```

**Servidor → Cliente:**
```json
{ "status": "ok", "data": { ... } }
{ "status": "ok", "message": "texto de confirmación" }
{ "status": "error", "message": "descripción del error" }
```

`data` y `message` son mutuamente excluyentes y se omiten si no aplican.

---

## Comandos disponibles

### `PING` – Verificar conexión
```json
{ "cmd": "PING", "payload": {} }
```
**Respuesta:** `{ "status": "ok", "message": "pong" }`

---

### `ADD_SONG` – Agregar canción al catálogo
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
**Respuesta exitosa:** objeto `Song` completo con el `id` asignado.

---

### `DELETE_SONG` – Eliminar canción
```json
{ "cmd": "DELETE_SONG", "payload": { "id": 1 } }
```
No se permite eliminar una canción que esté siendo reproducida actualmente.  
**Respuesta exitosa:** `{ "status": "ok", "message": "Canción 1 eliminada correctamente" }`

---

### `LIST_SONGS` – Listar todas las canciones
```json
{ "cmd": "LIST_SONGS", "payload": {} }
```
**Respuesta exitosa:** array con todos los objetos `Song` del catálogo.

---

### `SEARCH` – Buscar canciones
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
Los tres criterios (**name**, **artist**, **genre**) son opcionales y se combinan con AND.  
Un campo vacío o ausente no aplica filtro.  
**Respuesta exitosa:** array de objetos `Song` que coinciden.

---

### `CREATE_PLAYLIST` – Crear playlist
```json
{ "cmd": "CREATE_PLAYLIST", "payload": { "name": "Mis favoritas" } }
```
**Respuesta exitosa:** objeto `Playlist` con el `id` asignado y `song_ids` vacío.

---

### `ADD_TO_PLAYLIST` – Agregar canción a playlist
```json
{
  "cmd": "ADD_TO_PLAYLIST",
  "payload": { "playlist_id": 1, "song_id": 3 }
}
```
La canción debe existir en el catálogo. No se permiten duplicados en la misma playlist.

---

### `REMOVE_FROM_PLAYLIST` – Eliminar canción de playlist
```json
{
  "cmd": "REMOVE_FROM_PLAYLIST",
  "payload": { "playlist_id": 1, "song_id": 3 }
}
```

---

### `GET_PLAYLIST` – Obtener canciones de una playlist
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
Valores de `sort_by`: `"name"` | `"artist"` | `"album"` | `"duration"`.

**Respuesta exitosa:**
```json
{
  "status": "ok",
  "data": {
    "playlist": { "id": 1, "name": "Mis favoritas", "song_ids": [3, 1] },
    "songs": [ { ...Song... }, { ...Song... } ],
    "total_duration_secs": 600
  }
}
```

---

## Estructura `Song`

```json
{
  "id": 1,
  "name": "Bohemian Rhapsody",
  "artist": "Queen",
  "album": "A Night at the Opera",
  "genre": "Rock",
  "file_path": "/music/bohemian.mp3",
  "duration_secs": 354
}
```

## Estructura `Playlist`

```json
{
  "id": 1,
  "name": "Mis favoritas",
  "song_ids": [1, 3, 5]
}
```

---

## Códigos de error comunes

| Situación | Mensaje |
|---|---|
| JSON malformado | `"JSON inválido: ..."` |
| Campo obligatorio ausente | `"Faltan campos obligatorios: name, file_path"` |
| ID no encontrado | `"Canción no encontrada"` / `"Playlist no encontrada"` |
| Eliminación en reproducción | `"No se puede eliminar: la canción está en reproducción"` |
| Canción duplicada en playlist | `"La canción ya está en la playlist"` |
| Comando desconocido | `"Comando desconocido: NOMBRE"` |
