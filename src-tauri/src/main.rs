#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use serde::{Deserialize, Serialize};
use tauri::command;

const API_KEY: &str = "4273d517-cdc4-48ce-9544-954103110bd6";
const API_URL: &str = "https://user-api.predictionone.sony.biz/v1/groups/i5bm94my1c8f99w2/classifiers/1v7ew1izwq4xso6u/inference";

#[derive(Debug, Deserialize)]
struct StudentInput {
    StudyHours: f64,
    Attendance: f64,
    Resources: f64,
    Motivation: f64,
    Internet: f64,
    Gender: f64,
    Age: f64,
    Discussions: f64,
    AssignmentCompletion: f64,
    EduTech: f64,
}

#[derive(Debug, Serialize)]
struct DiagnosisResponse {
    final_grade: i32,
    probabilities: ProbabilityResponse,
}

#[derive(Debug, Serialize)]
struct ProbabilityResponse {
    rank0: f64,
    rank1: f64,
    rank2: f64,
    rank3: f64,
}

#[command]
fn diagnose_student(input: StudentInput) -> Result<DiagnosisResponse, String> {
    let input_data = vec![
        ("StudyHours", vec![input.StudyHours]),
        ("Attendance", vec![input.Attendance]),
        ("Resources", vec![input.Resources]),
        ("Motivation", vec![input.Motivation]),
        ("Internet", vec![input.Internet]),
        ("Gender", vec![input.Gender]),
        ("Age", vec![input.Age]),
        ("Discussions", vec![input.Discussions]),
        ("AssignmentCompletion", vec![input.AssignmentCompletion]),
        ("EduTech", vec![input.EduTech]),
    ];

    let csv_rows = vec![
        input_data.iter().map(|(key, _)| key.to_string()).collect::<Vec<_>>(),
        input_data
            .iter()
            .map(|(_, values)| values[0].to_string())
            .collect::<Vec<_>>(),
    ];

    let csv_content = csv_rows
        .iter()
        .map(|row| row.join(","))
        .collect::<Vec<_>>()
        .join("\n");

    let encoded = base64::encode(csv_content);

    let client = reqwest::blocking::Client::new();
    let response = client
        .post(API_URL)
        .header("x-api-key", API_KEY)
        .header("content-type", "application/json; charset=utf-8")
        .json(&serde_json::json!({
            "inputs": [
                { "name": "pr", "type": "csv", "data": encoded },
                { "name": "ar", "type": "boolean", "data": false },
                { "name": "ad", "type": "boolean", "data": true },
                { "name": "nc", "type": "boolean", "data": false }
            ]
        }))
        .send()
        .map_err(|e| format!("API request failed: {e}"))?;

    if !response.status().is_success() {
        return Err(format!("Prediction API error: {}", response.status()));
    }

    let json: serde_json::Value = response.json().map_err(|e| format!("Failed to parse API response: {e}"))?;
    let output = json["outputs"]
        .as_array()
        .and_then(|outputs| outputs.iter().find(|item| item["name"] == "prediction_valid.csv"))
        .ok_or_else(|| "prediction_valid.csv is missing".to_string())?;

    let decoded = base64::decode(output["data"].as_str().ok_or_else(|| "missing csv data".to_string())?)
        .map_err(|e| format!("base64 decode error: {e}"))?;
    let csv_text = String::from_utf8(decoded).map_err(|e| format!("utf8 decode error: {e}"))?;
    let lines: Vec<&str> = csv_text.trim().split('\n').collect();
    let values: Vec<&str> = lines[1].split(',').collect();

    let final_grade = values[1].parse::<i32>().map_err(|e| format!("final_grade parse error: {e}"))?;
    let probabilities = ProbabilityResponse {
        rank0: values[2].parse::<f64>().map_err(|e| format!("rank0 parse error: {e}"))? * 100.0,
        rank1: values[3].parse::<f64>().map_err(|e| format!("rank1 parse error: {e}"))? * 100.0,
        rank2: values[4].parse::<f64>().map_err(|e| format!("rank2 parse error: {e}"))? * 100.0,
        rank3: values[5].parse::<f64>().map_err(|e| format!("rank3 parse error: {e}"))? * 100.0,
    };

    Ok(DiagnosisResponse {
        final_grade,
        probabilities,
    })
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![diagnose_student])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
