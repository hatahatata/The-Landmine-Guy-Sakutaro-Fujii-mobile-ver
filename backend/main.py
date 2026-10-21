import base64
from typing import Any

import pandas as pd
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

API_KEY = "4273d517-cdc4-48ce-9544-954103110bd6"
API_URL = "https://user-api.predictionone.sony.biz/v1/groups/i5bm94my1c8f99w2/classifiers/1v7ew1izwq4xso6u/inference"

app = FastAPI(title="Student Grade Diagnosis API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class StudentInput(BaseModel):
    StudyHours: float
    Attendance: float
    Resources: float
    Motivation: float
    Internet: float
    Gender: float
    Age: float
    Discussions: float
    AssignmentCompletion: float
    EduTech: float

class ProbabilityResult(BaseModel):
    rank0: float
    rank1: float
    rank2: float
    rank3: float

class DiagnosisResult(BaseModel):
    final_grade: int
    probabilities: ProbabilityResult

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

@app.post("/predict", response_model=DiagnosisResult)
def predict(input: StudentInput) -> DiagnosisResult:
    input_data = {
        "StudyHours": [input.StudyHours],
        "Attendance": [input.Attendance],
        "Resources": [input.Resources],
        "Motivation": [input.Motivation],
        "Internet": [input.Internet],
        "Gender": [input.Gender],
        "Age": [input.Age],
        "Discussions": [input.Discussions],
        "AssignmentCompletion": [input.AssignmentCompletion],
        "EduTech": [input.EduTech],
    }

    df = pd.DataFrame(input_data)
    csv_str = df.to_csv(index=False)
    encoded_data = base64.b64encode(csv_str.encode("utf-8")).decode("ascii")

    headers = {
        "x-api-key": API_KEY,
        "content-type": "application/json; charset=utf-8",
    }
    body = {
        "inputs": [
            {"name": "pr", "type": "csv", "data": encoded_data},
            {"name": "ar", "type": "boolean", "data": False},
            {"name": "ad", "type": "boolean", "data": True},
            {"name": "nc", "type": "boolean", "data": False},
        ]
    }

    response = requests.post(API_URL, headers=headers, json=body, timeout=30)
    response.raise_for_status()

    response_json = response.json()
    output = next(
        (item for item in response_json.get("outputs", []) if item.get("name") == "prediction_valid.csv"),
        None,
    )
    if output is None:
        raise ValueError("prediction_valid.csv not found")

    decoded_csv = base64.b64decode(output["data"]).decode("utf-8")
    result_data = decoded_csv.strip().split("\n")[1].split(",")

    final_grade = int(result_data[1])
    prob_0 = float(result_data[2]) * 100
    prob_1 = float(result_data[3]) * 100
    prob_2 = float(result_data[4]) * 100
    prob_3 = float(result_data[5]) * 100

    return DiagnosisResult(
        final_grade=final_grade,
        probabilities=ProbabilityResult(
            rank0=prob_0,
            rank1=prob_1,
            rank2=prob_2,
            rank3=prob_3,
        ),
    )
