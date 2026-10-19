use std::path::Path;
use tauri::AppHandle;
use crate::engine::invoke_engine;

#[tauri::command]
pub async fn inspect_file(
    file_path: String,
    sheet_name: Option<String>,
    header_row: Option<i64>,
) -> Result<serde_json::Value, String> {
    let p = Path::new(&file_path);
    if !p.exists() {
        return Err(format!("File does not exist: {}", file_path));
    }

    let params = serde_json::json!({
        "file_path": file_path,
        "sheet_name": sheet_name,
        "header_row": header_row,
    });

    // Run synchronous child process on a blocking thread pool
    tokio_blocking(move || invoke_engine("inspect", params, None)).await
}

#[tauri::command]
pub async fn map_columns(
    file_a: String,
    file_b: String,
    sheet_a: Option<String>,
    sheet_b: Option<String>,
    header_row_a: Option<i64>,
    header_row_b: Option<i64>,
    app: AppHandle,
) -> Result<serde_json::Value, String> {
    if !Path::new(&file_a).exists() {
        return Err(format!("Dataset A file does not exist: {}", file_a));
    }
    if !Path::new(&file_b).exists() {
        return Err(format!("Dataset B file does not exist: {}", file_b));
    }

    let params = serde_json::json!({
        "file_a": file_a,
        "file_b": file_b,
        "sheet_a": sheet_a,
        "sheet_b": sheet_b,
        "header_row_a": header_row_a,
        "header_row_b": header_row_b,
    });

    let app_clone = app.clone();
    tokio_blocking(move || invoke_engine("map_columns", params, Some(&app_clone))).await
}

#[tauri::command]
pub async fn run_reconciliation(
    payload: serde_json::Value,
    app: AppHandle,
) -> Result<serde_json::Value, String> {
    let file_a = payload.get("file_a").and_then(|v| v.as_str()).unwrap_or("");
    let file_b = payload.get("file_b").and_then(|v| v.as_str()).unwrap_or("");

    if file_a.is_empty() || !Path::new(file_a).exists() {
        return Err(format!("Dataset A file does not exist or not specified: {}", file_a));
    }
    if file_b.is_empty() || !Path::new(file_b).exists() {
        return Err(format!("Dataset B file does not exist or not specified: {}", file_b));
    }

    let app_clone = app.clone();
    tokio_blocking(move || invoke_engine("reconcile", payload, Some(&app_clone))).await
}

#[tauri::command]
pub fn pick_file(title: Option<String>, default_path: Option<String>) -> Result<Option<String>, String> {
    let mut dialog = rfd::FileDialog::new()
        .set_title(title.as_deref().unwrap_or("Select dataset file"))
        .add_filter(
            "Tabular data (*.csv, *.tsv, *.xlsx, *.json)",
            &["csv", "tsv", "xlsx", "json"],
        );

    if let Some(ref dp) = default_path {
        dialog = dialog.set_directory(dp);
    }

    let result = dialog.pick_file();
    Ok(result.map(|p| p.to_string_lossy().to_string()))
}

#[tauri::command]
pub fn pick_directory(default_path: Option<String>) -> Result<Option<String>, String> {
    let mut dialog = rfd::FileDialog::new()
        .set_title("Select export folder");

    if let Some(ref dp) = default_path {
        dialog = dialog.set_directory(dp);
    }

    let result = dialog.pick_folder();
    Ok(result.map(|p| p.to_string_lossy().to_string()))
}

#[tauri::command]
pub async fn export_reconciliation(
    payload: serde_json::Value,
    app: AppHandle,
) -> Result<serde_json::Value, String> {
    let output_path = payload
        .get("output_path")
        .and_then(|v| v.as_str())
        .unwrap_or("");

    if output_path.is_empty() {
        return Err("Export failed: output_path was not provided".to_string());
    }

    let app_clone = app.clone();
    tokio_blocking(move || invoke_engine("export_excel", payload, Some(&app_clone))).await
}

async fn tokio_blocking<F, T>(f: F) -> Result<T, String>
where
    F: FnOnce() -> Result<T, String> + Send + 'static,
    T: Send + 'static,
{
    tauri::async_runtime::spawn_blocking(f)
        .await
        .map_err(|e| format!("Task execution failed: {}", e))?
}
