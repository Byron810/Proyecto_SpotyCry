// Tipos que definen el protocolo de comunicación cliente-servidor.
//
// Formato de mensaje (una línea JSON terminada en '\n'):
//   Cliente → Servidor: { "cmd": "NOMBRE", "payload": { ... } }
//   Servidor → Cliente: { "status": "ok"|"error", "data": ..., "message": ... }

use serde::{Deserialize, Serialize};
use serde_json::Value;

/// Comando entrante del cliente.
#[derive(Debug, Deserialize)]
pub struct Command {
    pub cmd: String,
    #[serde(default)]
    pub payload: Value, // datos específicos según el comando; vacío si no aplica
}

/// Respuesta estándar del servidor al cliente.
#[derive(Debug, Serialize)]
pub struct Response {
    pub status: &'static str,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub data: Option<Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub message: Option<String>,
}

impl Response {
    /// Éxito con datos adjuntos (ej: objeto Song o lista de canciones).
    pub fn ok(data: Value) -> Self {
        Response { status: "ok", data: Some(data), message: None }
    }

    /// Éxito con solo un mensaje de confirmación.
    pub fn ok_msg(msg: &str) -> Self {
        Response { status: "ok", data: None, message: Some(msg.to_string()) }
    }

    /// Error con descripción del problema.
    pub fn error(msg: &str) -> Self {
        Response { status: "error", data: None, message: Some(msg.to_string()) }
    }
}