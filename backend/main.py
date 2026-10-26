import base64
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

API_KEY = "df4d195d-dfa9-4e10-b515-77e15096d492"
API_URL = "https://user-api.predictionone.sony.biz/v1/groups/qejw062trt0qwwav/classifiers/quipaioomqira6hd/inference"

app = FastAPI(title="Student Grade Diagnosis API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 全デバイスからアクセス可能にする（開発用）
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== ルーム管理（サーバーメモリ） =====
rooms_store: Dict[str, dict] = {}


# ----- Pydantic モデル -----

class ParticipantModel(BaseModel):
    id: str
    name: str
    isAdmin: bool
    score: Optional[int] = None
    riskScore: Optional[float] = None
    prob3: Optional[float] = None
    rank: Optional[int] = None


class RoomModel(BaseModel):
    id: str
    name: str
    code: str
    ownerId: str
    createdAt: int
    participants: List[ParticipantModel]
    status: str = "waiting"


class JoinRoomRequest(BaseModel):
    id: str
    name: str


class LeaveRoomRequest(BaseModel):
    user_id: str


class UpdateScoreRequest(BaseModel):
    user_id: str
    score: int
    riskScore: float
    prob3: float


# ----- ルーム管理エンドポイント -----

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/rooms", response_model=RoomModel)
def create_room(room: RoomModel) -> RoomModel:
    rooms_store[room.id] = room.model_dump()
    return room


@app.get("/rooms", response_model=List[RoomModel])
def get_rooms() -> List[dict]:
    return list(rooms_store.values())


@app.get("/rooms/by-code/{code}", response_model=RoomModel)
def get_room_by_code(code: str) -> dict:
    for room in rooms_store.values():
        if room["code"] == code.upper():
            return room
    raise HTTPException(status_code=404, detail="Room not found")


@app.get("/rooms/{room_id}", response_model=RoomModel)
def get_room(room_id: str) -> dict:
    if room_id not in rooms_store:
        raise HTTPException(status_code=404, detail="Room not found")
    return rooms_store[room_id]


@app.post("/rooms/{room_id}/join", response_model=RoomModel)
def join_room(room_id: str, req: JoinRoomRequest) -> dict:
    if room_id not in rooms_store:
        raise HTTPException(status_code=404, detail="Room not found")
    room = rooms_store[room_id]
    already = any(p["id"] == req.id for p in room["participants"])
    if not already:
        room["participants"].append({
            "id": req.id,
            "name": req.name,
            "isAdmin": False,
            "score": None,
            "riskScore": None,
            "prob3": None,
            "rank": None,
        })
    return room


@app.post("/rooms/{room_id}/leave", response_model=RoomModel)
def leave_room(room_id: str, req: LeaveRoomRequest) -> dict:
    if room_id not in rooms_store:
        raise HTTPException(status_code=404, detail="Room not found")
    room = rooms_store[room_id]
    room["participants"] = [p for p in room["participants"] if p["id"] != req.user_id]
    return room


@app.put("/rooms/{room_id}/score", response_model=RoomModel)
def update_score(room_id: str, req: UpdateScoreRequest) -> dict:
    if room_id not in rooms_store:
        raise HTTPException(status_code=404, detail="Room not found")
    room = rooms_store[room_id]
    for p in room["participants"]:
        if p["id"] == req.user_id:
            p["score"] = req.score
            p["riskScore"] = req.riskScore
            p["prob3"] = req.prob3
            break
    return room


# ----- AI 診断エンドポイント -----

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
