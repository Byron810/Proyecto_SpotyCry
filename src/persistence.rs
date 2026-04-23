// Persistencia del estado del servidor en disco (JSON).
// Se guarda automáticamente tras cada operación que muta el catálogo.

use std::fs;
use std::sync::MutexGuard;

use crate::models::AppState;

const STATE_FILE: &str = "spoticry_state.json";

/// Serializa el estado actual a `spoticry_state.json`.
/// Se llama mientras el lock está tomado; la escritura es rápida (archivo pequeño).
pub fn save_state(state: &MutexGuard<AppState>) {
    match serde_json::to_string_pretty(&**state) {
        Ok(json) => {
            if let Err(e) = fs::write(STATE_FILE, &json) {
                eprintln!("⚠️  No se pudo guardar el estado: {}", e);
            }
        }
        Err(e) => eprintln!("⚠️  Error serializando estado: {}", e),
    }
}

/// Carga el estado desde `spoticry_state.json`.
/// Si el archivo no existe o está corrupto, retorna un AppState vacío.
pub fn load_state() -> AppState {
    match fs::read_to_string(STATE_FILE) {
        Ok(json) => match serde_json::from_str::<AppState>(&json) {
            Ok(state) => {
                println!(
                    "📂 Estado restaurado: {} canción(es), {} playlist(s)",
                    state.songs.len(),
                    state.playlists.len()
                );
                state
            }
            Err(e) => {
                eprintln!("⚠️  Estado corrupto ({}). Iniciando vacío.", e);
                AppState::new()
            }
        },
        Err(_) => {
            println!("📂 Sin estado previo — iniciando catálogo vacío.");
            AppState::new()
        }
    }
}
