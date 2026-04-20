# SpotiCry – Arquitectura del servidor

## Descripción general

SpotiCry es una aplicación de reproducción de música con arquitectura **cliente-servidor**. El servidor está escrito en **Rust** y se comunica con los clientes mediante **TCP/IP con sockets**. El protocolo de mensajes es JSON por línea: cada mensaje ocupa exactamente una línea terminada en `\n`.

---

## Estructura de módulos

```
ServidorSpotyCry/src/
├── main.rs        Punto de entrada. Inicia el listener TCP y crea un hilo por cliente.
├── models.rs      Estructuras de datos: Song, Playlist, AppState.
├── protocol.rs    Tipos del protocolo de comunicación: Command y Response.
├── playlist.rs    Operaciones funcionales sobre playlists (filter, sort, fold).
└── handlers.rs    Handlers de cada comando y función de routing.
```

### `main.rs`
Responsabilidad única: iniciar el servidor y delegar cada conexión a un hilo. Contiene `handle_client`, que lee líneas JSON del socket, las pasa a `route_command` y escribe la respuesta de vuelta.

### `models.rs`
Define las tres estructuras de dominio:

| Struct | Descripción |
|---|---|
| `Song` | Canción con id, name, artist, album, genre, file_path, duration_secs |
| `Playlist` | Lista de reproducción con id, name y un `Vec<u32>` de IDs de canciones |
| `AppState` | Estado global: catálogo de canciones, playlists, contadores de ID y lista de canciones en reproducción |

### `protocol.rs`
Define `Command` (deserializado desde el cliente) y `Response` (serializado hacia el cliente). `Response` tiene tres constructores: `ok(data)`, `ok_msg(msg)` y `error(msg)`.

### `playlist.rs`
Operaciones inmutables sobre playlists, implementadas con paradigma funcional:
- `playlist_filter` — filtra con un closure predicado
- `playlist_sort_by_field` — ordena por campo, retorna colección nueva
- `playlist_total_duration` — acumula duración con `fold`

### `handlers.rs`
Un handler por comando (`cmd_add_song`, `cmd_search`, etc.) y la función `route_command` que despacha según el campo `cmd` del mensaje.

---

## Concurrencia

```
TcpListener
    │
    ├── cliente A → thread::spawn → handle_client(stream, Arc::clone(&state))
    ├── cliente B → thread::spawn → handle_client(stream, Arc::clone(&state))
    └── cliente N → thread::spawn → handle_client(stream, Arc::clone(&state))
                                          │
                                    Arc<Mutex<AppState>>
                                    (lock solo durante cada operación)
```

| Mecanismo | Propósito |
|---|---|
| `thread::spawn` | Un hilo independiente por cliente conectado |
| `Arc<T>` | Comparte el puntero al estado entre hilos sin copiar datos |
| `Mutex<T>` | Garantiza acceso exclusivo al estado; se bloquea y libera automáticamente |

El `Mutex` se bloquea solo durante la duración del handler (una operación atómica), por lo que los clientes no se bloquean entre sí en condiciones normales.

---

## Flujo de un mensaje

```
Cliente                         Servidor
  │                                │
  │── {"cmd":"SEARCH", ...}\n ────►│
  │                         parse JSON → Command
  │                         route_command(state, cmd)
  │                         lock Mutex → cmd_search → unlock
  │                         serialize Response → JSON
  │◄── {"status":"ok","data":[...]}\n ─│
```

---

## Dependencias externas

| Crate | Versión | Uso |
|---|---|---|
| `serde` | 1.x | Derivar Serialize/Deserialize en los structs |
| `serde_json` | 1.x | Parsear y serializar JSON; tipo `Value` para payloads dinámicos |

Todo lo demás (TCP, hilos, Mutex) usa la biblioteca estándar de Rust (`std`).
