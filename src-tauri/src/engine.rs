use std::io::{BufRead, BufReader, Write};
use std::path::PathBuf;
use std::process::{Command, Stdio};
use tauri::Emitter;

#[cfg(windows)]
use std::os::windows::process::CommandExt;

/// Finds the appropriate Python executable for the reconciliation engine.
pub fn find_python_path() -> Result<PathBuf, String> {
    // 1. Check explicit environment override
    if let Ok(env_path) = std::env::var("RECONCILE_PYTHON") {
        let p = PathBuf::from(env_path);
        if p.exists() {
            return Ok(p);
        }
    }

    // 2. Check workspace virtualenv relative to current exe or known roots
    let candidates = [
        "D:\\RECONSILE\\engine\\.venv\\Scripts\\python.exe",
        "engine\\.venv\\Scripts\\python.exe",
        "..\\engine\\.venv\\Scripts\\python.exe",
        "engine\\.venv\\bin\\python",
        "..\\engine\\.venv\\bin\\python",
    ];

    for candidate in &candidates {
        let p = PathBuf::from(candidate);
        if p.exists() {
            return Ok(p);
        }
    }

    // 3. Fallback: Check if python is on PATH
    if let Ok(path) = which_python() {
        return Ok(path);
    }

    Err("Could not locate Python environment. Please ensure engine/.venv exists or set RECONCILE_PYTHON.".to_string())
}

fn which_python() -> Result<PathBuf, String> {
    #[cfg(windows)]
    let check_cmd = "where.exe";
    #[cfg(not(windows))]
    let check_cmd = "which";

    let output = Command::new(check_cmd)
        .arg("python")
        .output()
        .map_err(|e| format!("Failed to search PATH for python: {}", e))?;

    if output.status.success() {
        let text = String::from_utf8_lossy(&output.stdout);
        if let Some(first_line) = text.lines().next() {
            let p = PathBuf::from(first_line.trim());
            if p.exists() {
                return Ok(p);
            }
        }
    }

    Err("Python not found on PATH".to_string())
}

/// Finds the root directory of the engine package.
pub fn find_engine_dir() -> Result<PathBuf, String> {
    let candidates = [
        "D:\\RECONSILE\\engine",
        "engine",
        "..\\engine",
    ];

    for candidate in &candidates {
        let p = PathBuf::from(candidate);
        if p.exists() && p.join("reconcile").exists() {
            return Ok(p);
        }
    }

    Err("Could not find engine package directory".to_string())
}

/// Executes a command via the Python engine CLI IPC protocol (JSON-over-stdin).
/// Emits progress events to the Tauri front-end if an AppHandle is provided.
pub fn invoke_engine(
    command_name: &str,
    params: serde_json::Value,
    app_handle: Option<&tauri::AppHandle>,
) -> Result<serde_json::Value, String> {
    let python_path = find_python_path()?;
    let engine_dir = find_engine_dir()?;

    let request = serde_json::json!({
        "command": command_name,
        "params": params
    });

    let input_bytes = serde_json::to_vec(&request)
        .map_err(|e| format!("Failed to serialize engine request: {}", e))?;

    let mut cmd = Command::new(&python_path);
    cmd.args(["-m", "reconcile.cli", "ipc"])
        .current_dir(&engine_dir)
        .env("PYTHONPATH", &engine_dir)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());

    // On Windows, suppress the CMD prompt window
    #[cfg(windows)]
    cmd.creation_flags(0x08000000); // CREATE_NO_WINDOW

    let mut child = cmd
        .spawn()
        .map_err(|e| format!("Failed to spawn Python process ({:?}): {}", python_path, e))?;

    // Write JSON payload to stdin, then close stdin
    if let Some(mut stdin) = child.stdin.take() {
        stdin
            .write_all(&input_bytes)
            .map_err(|e| format!("Failed to write to Python stdin: {}", e))?;
        stdin
            .flush()
            .map_err(|e| format!("Failed to flush Python stdin: {}", e))?;
        // stdin is dropped here, closing the pipe so sys.stdin.read() completes in Python
    }

    let stdout = child
        .stdout
        .take()
        .ok_or_else(|| "Failed to capture Python stdout".to_string())?;

    let reader = BufReader::new(stdout);
    let mut final_result: Option<Result<serde_json::Value, String>> = None;

    for line_res in reader.lines() {
        let line = match line_res {
            Ok(l) => l,
            Err(_) => break,
        };

        let trimmed = line.trim();
        if trimmed.is_empty() {
            continue;
        }

        // Try parsing NDJSON line
        if let Ok(parsed) = serde_json::from_str::<serde_json::Value>(trimmed) {
            let msg_type = parsed.get("type").and_then(|t| t.as_str()).unwrap_or("");
            if msg_type == "progress" {
                if let Some(app) = app_handle {
                    let _ = app.emit("engine-progress", &parsed);
                }
            } else if msg_type == "result" {
                let success = parsed.get("success").and_then(|s| s.as_bool()).unwrap_or(false);
                if success {
                    let data = parsed.get("data").cloned().unwrap_or(serde_json::Value::Null);
                    final_result = Some(Ok(data));
                } else {
                    let err = parsed
                        .get("error")
                        .and_then(|e| e.as_str())
                        .unwrap_or("Unknown engine error")
                        .to_string();
                    final_result = Some(Err(err));
                }
            }
        }
    }

    // Wait for process exit
    let status = child
        .wait()
        .map_err(|e| format!("Failed to wait for Python child process: {}", e))?;

    if let Some(res) = final_result {
        return res;
    }

    // If no result line was parsed, check stderr
    let mut stderr_msg = String::new();
    if let Some(mut stderr) = child.stderr.take() {
        use std::io::Read;
        let _ = stderr.read_to_string(&mut stderr_msg);
    }

    Err(format!(
        "Engine process exited with status {}. Stderr: {}",
        status,
        stderr_msg.trim()
    ))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_find_python_path() {
        let py = find_python_path();
        assert!(py.is_ok(), "Failed to locate Python: {:?}", py.err());
        let p = py.unwrap();
        assert!(p.exists());
    }

    #[test]
    fn test_inspect_file_ipc() {
        let temp_dir = std::env::temp_dir();
        let temp_path = temp_dir.join("test_reconcile_ipc_inspect.csv");
        std::fs::write(&temp_path, "Invoice_ID,Client_Name,Total_Amount\nINV-001,Acme Corp,1500.50\n").unwrap();

        let params = serde_json::json!({
            "file_path": temp_path.to_string_lossy().to_string()
        });

        let res = invoke_engine("inspect", params, None);
        let _ = std::fs::remove_file(&temp_path);

        assert!(res.is_ok(), "Engine inspection failed: {:?}", res.err());
        let data = res.unwrap();
        assert_eq!(data["total_rows"], 1);
        assert_eq!(data["columns"].as_array().map(|a| a.len()), Some(3));
    }

    #[test]
    fn test_map_columns_and_reconcile_ipc() {
        let temp_dir = std::env::temp_dir();
        let path_a = temp_dir.join("test_e2e_ledger_a.csv");
        let path_b = temp_dir.join("test_e2e_bank_b.csv");

        std::fs::write(
            &path_a,
            "id,company,amount,date\nINV-100,Acme Corp,1000.00,2024-01-10\nINV-101,Beta LLC,500.00,2024-01-11\nINV-102,Gamma Inc,250.00,2024-01-12\n"
        ).unwrap();

        std::fs::write(
            &path_b,
            "invoice_no,partner,paid_amount,trans_date\nINV-100,Acme Corp,1000.00,2024-01-10\nINV-101,Beta LLC,450.00,2024-01-11\nINV-999,Delta Ltd,300.00,2024-01-15\n"
        ).unwrap();

        // 1. Test map_columns
        let map_params = serde_json::json!({
            "file_a": path_a.to_string_lossy().to_string(),
            "file_b": path_b.to_string_lossy().to_string(),
        });

        let map_res = invoke_engine("map_columns", map_params, None);
        assert!(map_res.is_ok(), "map_columns failed: {:?}", map_res.err());
        let map_data = map_res.unwrap();
        let mappings = map_data["mappings"].as_array().expect("Expected mappings array");
        assert!(!mappings.is_empty());

        // 2. Test reconcile
        let rec_params = serde_json::json!({
            "file_a": path_a.to_string_lossy().to_string(),
            "file_b": path_b.to_string_lossy().to_string(),
            "mappings": mappings,
            "rules": {
                "amount_tolerance": 0.01,
                "date_tolerance_days": 7
            }
        });

        let rec_res = invoke_engine("reconcile", rec_params, None);
        assert!(rec_res.is_ok(), "reconcile failed: {:?}", rec_res.err());
        let rec_data = rec_res.unwrap();
        let summary = &rec_data["summary"];
        assert_eq!(summary["matched_count"], 1);
        assert_eq!(summary["discrepancies_count"], 1);
        assert_eq!(summary["missing_in_b_count"], 1);
        assert_eq!(summary["missing_in_a_count"], 1);

        let matched_rec = rec_data["records"]
            .as_array()
            .expect("records array")
            .iter()
            .find(|r| r["status"] == "matched")
            .expect("at least one matched record");
        let matched_id = matched_rec["id"].as_str().expect("record id");

        // 3. Test user override handling
        let override_params = serde_json::json!({
            "file_a": path_a.to_string_lossy().to_string(),
            "file_b": path_b.to_string_lossy().to_string(),
            "mappings": mappings,
            "overrides": {
                matched_id: { "action": "unmatched" }
            }
        });

        let ovr_res = invoke_engine("reconcile", override_params, None);
        assert!(ovr_res.is_ok(), "reconcile with override failed: {:?}", ovr_res.err());
        let ovr_data = ovr_res.unwrap();
        let ovr_summary = &ovr_data["summary"];
        assert_eq!(ovr_summary["matched_count"], 0); // was 1, now detached to missing
        assert_eq!(ovr_summary["missing_in_b_count"], 2);
        assert_eq!(ovr_summary["missing_in_a_count"], 2);

        let _ = std::fs::remove_file(&path_a);
        let _ = std::fs::remove_file(&path_b);
    }

    #[test]
    fn test_export_excel_ipc() {
        let temp_dir = std::env::temp_dir();
        let export_path = temp_dir.join("test_reconcile_export.xlsx");

        let export_params = serde_json::json!({
            "output_path": export_path.to_string_lossy().to_string(),
            "scope": "all",
            "summary": {
                "matched_count": 5,
                "discrepancies_count": 2,
                "total_records": 7,
                "total_variance": -150.0
            },
            "records": [
                {
                    "id": "rec_1",
                    "status": "matched",
                    "status_label": "Matched",
                    "reference": "INV-101",
                    "entity": "Acme Corp",
                    "amount_a": 1000.0,
                    "amount_b": 1000.0,
                    "amount_diff": 0.0,
                    "differences": []
                },
                {
                    "id": "rec_2",
                    "status": "discrepancy",
                    "status_label": "Discrepancy",
                    "reference": "INV-102",
                    "entity": "Beta LLC",
                    "amount_a": 500.0,
                    "amount_b": 350.0,
                    "amount_diff": -150.0,
                    "differences": [{"description": "Variance of 150"}]
                }
            ],
            "meta_a": { "file_name": "ledger.csv", "total_rows": 2 },
            "meta_b": { "file_name": "statement.csv", "total_rows": 2 }
        });

        let res = invoke_engine("export_excel", export_params, None);
        assert!(res.is_ok(), "export_excel IPC failed: {:?}", res.err());
        let data = res.unwrap();

        let saved_path_str = data["saved_path"].as_str().expect("saved_path string");
        let saved_path = std::path::Path::new(saved_path_str);
        assert!(saved_path.exists(), "Exported file does not exist on disk");

        let bytes = std::fs::read(saved_path).expect("Read exported file bytes");
        assert!(bytes.len() > 1000, "Exported file is too small");
        // Verify ZIP header ('PK') for valid xlsx
        assert_eq!(&bytes[0..2], b"PK", "File does not begin with valid PK signature");

        let _ = std::fs::remove_file(saved_path);
    }

    #[test]
    fn test_reconcile_with_generalized_config_ipc() {
        let temp_dir = std::env::temp_dir();
        let path_a = temp_dir.join("test_e2e_gst_a.csv");
        let path_b = temp_dir.join("test_e2e_gst_b.csv");

        std::fs::write(
            &path_a,
            "type,doc_num,taxable,cgst,sgst,cost_center\n\
             INV,101,10000.00,900.00,900.00,West\n\
             INV,102,5000.00,450.00,450.00,East\n"
        ).unwrap();

        std::fs::write(
            &path_b,
            "doc_type,inv_num,tax_val,tax_cgst,tax_sgst\n\
             INV,101,10000.00,900.00,900.00\n\
             INV,102,5000.00,450.00,458.00\n"
        ).unwrap();

        let rec_params = serde_json::json!({
            "file_a": path_a.to_string_lossy().to_string(),
            "file_b": path_b.to_string_lossy().to_string(),
            "config": {
                "keys": [
                    { "col_a": "type", "col_b": "doc_type" },
                    { "col_a": "doc_num", "col_b": "inv_num" }
                ],
                "metrics": [
                    { "name": "Taxable", "col_a": "taxable", "col_b": "tax_val", "tolerance": 0.01 },
                    { "name": "CGST", "col_a": "cgst", "col_b": "tax_cgst", "tolerance": 1.0 },
                    { "name": "SGST", "col_a": "sgst", "col_b": "tax_sgst", "tolerance": 1.0 }
                ],
                "group_by_col": "cost_center",
                "primary_metric_name": "Taxable"
            }
        });

        let rec_res = invoke_engine("reconcile", rec_params, None);
        assert!(rec_res.is_ok(), "reconcile with generalized config failed: {:?}", rec_res.err());
        let rec_data = rec_res.unwrap();

        let summary = &rec_data["summary"];
        assert_eq!(summary["matched_count"], 1);
        assert_eq!(summary["discrepancies_count"], 1);

        // Verify multi-metric variances survive the IPC boundary
        let metric_vars = &summary["metric_variances"];
        assert!(metric_vars.get("Taxable").is_some());
        assert!(metric_vars.get("CGST").is_some());
        assert!(metric_vars.get("SGST").is_some());
        assert_eq!(metric_vars["SGST"]["discrepancy_count"], 1);
        assert_eq!(metric_vars["SGST"]["gross_variance"], 8.0);

        // Verify records have composite keys, field diffs, and metrics
        let records = rec_data["records"].as_array().expect("records array");
        assert_eq!(records.len(), 2);

        let r102 = records.iter().find(|r| {
            r["reference"].as_str().map(|s| s.contains("102")).unwrap_or(false)
        }).expect("record 102");
        assert_eq!(r102["status"], "discrepancy");
        assert_eq!(r102["differences"][0]["field"], "SGST");
        assert_eq!(r102["differences"][0]["delta"], 8.0);
        assert_eq!(r102["metrics_a"]["SGST"], 450.0);
        assert_eq!(r102["metrics_b"]["SGST"], 458.0);

        // Verify dynamic grouping survives IPC boundary
        let grouped = &rec_data["grouped_records"];
        assert!(grouped.get("West").is_some());
        assert!(grouped.get("East").is_some());

        let _ = std::fs::remove_file(&path_a);
        let _ = std::fs::remove_file(&path_b);
    }
}

