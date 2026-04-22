// Módulo de streaming de audio
// Lee archivos MP3 y los convierte en chunks de bytes para enviar al cliente

use std::fs::File;
use std::io::{BufReader, Read, Seek, SeekFrom};
use std::path::Path;

/// Lee un archivo de audio y retorna un chunk de bytes desde una posición específica.
///
/// # Argumentos
/// * `file_path` - Ruta al archivo de audio
/// * `offset` - Byte desde donde empezar a leer
/// * `chunk_size` - Tamaño del chunk en bytes (por defecto 8192)
///
/// # Retorno
/// * `Ok(Vec<u8>)` - Chunk de bytes leídos
/// * `Err(String)` - Mensaje de error
pub fn read_audio_chunk(file_path: &str, offset: u64, chunk_size: usize) -> Result<Vec<u8>, String> {
    let path = Path::new(file_path);

    if !path.exists() {
        return Err(format!("Archivo no encontrado: {}", file_path));
    }

    let file = File::open(path).map_err(|e| format!("Error abriendo archivo: {}", e))?;
    let mut reader = BufReader::new(file);

    // Posicionar en el offset solicitado
    if offset > 0 {
        reader.seek(SeekFrom::Start(offset)).map_err(|e| format!("Error en seek: {}", e))?;
    }

    // Leer el chunk
    let mut buffer = vec![0u8; chunk_size];
    let bytes_read = reader.read(&mut buffer).map_err(|e| format!("Error leyendo archivo: {}", e))?;

    // Truncar al tamaño real leído
    buffer.truncate(bytes_read);

    Ok(buffer)
}

/// Obtiene el tamaño total del archivo de audio en bytes.
pub fn get_file_size(file_path: &str) -> Result<u64, String> {
    let path = Path::new(file_path);

    if !path.exists() {
        return Err(format!("Archivo no encontrado: {}", file_path));
    }

    let metadata = std::fs::metadata(path).map_err(|e| format!("Error leyendo metadata: {}", e))?;
    Ok(metadata.len())
}

/// Verifica si un archivo es un formato de audio soportado.
pub fn is_supported_audio(file_path: &str) -> bool {
    let path = Path::new(file_path);
    match path.extension().and_then(|ext| ext.to_str()) {
        Some("mp3") => true,
        Some("wav") => true,
        Some("flac") => true,
        Some("ogg") => true,
        _ => false,
    }
}
