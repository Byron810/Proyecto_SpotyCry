# SpotiCry – Plan de desarrollo

**Entrega:** miércoles 28 de abril de 2026 antes de las 10:00 pm

---

## Estado actual

| Módulo | Estado |
|---|---|
| Servidor TCP con hilos por cliente | ✅ Completo |
| Estructuras de datos (Song, Playlist, AppState) | ✅ Completo |
| Protocolo JSON (Command / Response) | ✅ Completo |
| Comandos: ADD_SONG, DELETE_SONG, LIST_SONGS | ✅ Completo |
| Búsqueda por 3 criterios (SEARCH) | ✅ Completo |
| Gestión de playlists (crear, agregar, eliminar, obtener) | ✅ Completo |
| Operaciones funcionales (filter, sort, fold) | ✅ Completo |
| Streaming de audio | ❌ Pendiente |
| CLI de administración en el servidor | ❌ Pendiente |
| Cliente con interfaz gráfica | ❌ Pendiente |
| Buffer local + adelantar/retroceder | ❌ Pendiente |

---

## Partes pendientes

---

### Parte 2 – Streaming de audio (Servidor Rust)

El servidor debe leer el archivo de audio y enviar sus bytes al cliente para que este los reproduzca localmente.

**Qué implementar:**

- Nuevo comando `PLAY_SONG` que recibe un `song_id`
- El servidor abre el archivo indicado en `file_path` de la canción
- Envía los bytes del archivo en chunks al cliente (ej. 4 KB por chunk)
- Marca la canción como "en reproducción" en `playing_song_ids`
- Nuevo comando `STOP_SONG` para liberar la reproducción y permitir eliminación

**Protocolo sugerido:**
```
Cliente → { "cmd": "PLAY_SONG", "payload": { "song_id": 1 } }
Servidor → { "status": "ok", "data": { "total_bytes": 3456789 } }
Servidor → [bytes en crudo, chunk a chunk]
Servidor → { "status": "ok", "message": "stream_end" }
```

**Archivos a crear/modificar:**
- `src/audio.rs` — lógica de lectura y envío de chunks
- `src/handlers.rs` — agregar `cmd_play_song`, `cmd_stop_song`, actualizar routing

**Consideraciones:**
- El Mutex no puede estar bloqueado mientras se envían los bytes (bloquearía a otros clientes)
- Separar la fase de "autorizar reproducción" (con lock) de la fase de "enviar bytes" (sin lock)

---

### Parte 3 – CLI de administración del servidor

El enunciado requiere una **interfaz de texto en el servidor** para administrar canciones sin necesidad de un cliente externo.

**Qué implementar:**

- Hilo separado que lee comandos desde `stdin` mientras el servidor atiende clientes
- Comandos disponibles desde la consola del servidor:
  - `add <ruta>` — agregar canción desde archivo local
  - `delete <id>` — eliminar canción
  - `list` — listar canciones
  - `help` — mostrar comandos disponibles

**Archivos a crear/modificar:**
- `src/admin.rs` — loop de lectura de stdin y procesamiento de comandos
- `src/main.rs` — lanzar el hilo de admin con `thread::spawn` antes del loop principal

---

### Parte 4 – Cliente con interfaz gráfica

El enunciado permite escritorio, web o mobile. **Recomendado: Python con tkinter** (ya hay un `Cliente.py` base) o una app web simple con HTML + JavaScript.

**Qué implementar:**

#### 4a. Conexión y protocolo
- Actualizar `Cliente.py` para usar el protocolo JSON actual (líneas `\n`)
- Funciones base: `send_command(cmd, payload)` y `receive_response()`

#### 4b. Pantalla principal
- Lista de canciones del catálogo (llamar `LIST_SONGS`)
- Barra de búsqueda con 3 criterios: nombre, artista, género (llamar `SEARCH`)
- Botones: Agregar canción, Eliminar canción

#### 4c. Reproductor
- Recibir bytes del servidor (stream de audio)
- **Buffer local**: almacenar toda la canción en memoria antes de reproducir
- Controles: Play, Pause, Adelantar (seek forward), Retroceder (seek backward)
- El adelantar/retroceder aplica solo a la canción actual en el buffer local
- Librería sugerida: `pygame` para reproducir audio desde bytes en memoria

#### 4d. Playlists
- Panel para crear playlists (llamar `CREATE_PLAYLIST`)
- Agregar canciones buscadas a una o varias playlists (llamar `ADD_TO_PLAYLIST`)
- Ver canciones de una playlist con filtro y ordenamiento (llamar `GET_PLAYLIST`)

**Archivos a crear:**
- `Cliente/main.py` o `Cliente/app.py` — punto de entrada de la GUI
- `Cliente/connection.py` — manejo del socket TCP
- `Cliente/player.py` — buffer local y reproducción de audio

---

### Parte 5 – Persistencia (opcional pero recomendado)

Actualmente el estado se pierde al reiniciar el servidor. Para el proyecto no es obligatorio, pero facilita las pruebas.

**Opción simple:** serializar `AppState` a JSON en un archivo al recibir cambios y cargarlo al iniciar.

**Archivos a crear:**
- `src/persistence.rs` — `save_state(state)` y `load_state() -> AppState`

---

## Orden de trabajo sugerido

| Prioridad | Tarea | Motivo |
|---|---|---|
| 1 | Parte 2: Streaming de audio | Sin esto el cliente no puede reproducir nada |
| 2 | Parte 4a y 4b: Cliente base + búsqueda | Permite probar el servidor visualmente |
| 3 | Parte 4c: Reproductor con buffer | Requiere que el streaming funcione |
| 4 | Parte 3: CLI de admin del servidor | Independiente, se puede hacer en paralelo |
| 5 | Parte 4d: Playlists en el cliente | Ya están implementadas en el servidor |
| 6 | Parte 5: Persistencia | Mejora la experiencia pero no es obligatorio |

---

## Requisitos del enunciado y dónde se cumplen

| Requisito | Dónde |
|---|---|
| Búsqueda mínimo 3 criterios (servidor) | `handlers.rs` → `cmd_search` |
| Agregar/eliminar canciones | `handlers.rs` → `cmd_add_song`, `cmd_delete_song` |
| No eliminar si está en reproducción | `handlers.rs` → verificación en `cmd_delete_song` |
| Reproducción: inicio y fin local, envío de bytes | **Parte 2** |
| Playlists: crear, agregar, eliminar, filtrar, transformar | `handlers.rs` + `playlist.rs` |
| Funcional: sin mutabilidad, map/filter/fold, closures | `playlist.rs` |
| TCP-IP con sockets | `main.rs` |
| Múltiples clientes en paralelo | `main.rs` → `thread::spawn` + `Arc<Mutex>` |
| Interfaz de texto en el servidor | **Parte 3** |
| Cliente con GUI | **Parte 4** |
| Buffer local + adelantar/retroceder | **Parte 4c** |
| Búsqueda mínimo 3 criterios (cliente) | **Parte 4b** |
