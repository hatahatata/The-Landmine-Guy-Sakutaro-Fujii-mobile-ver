import base64
import json
import re
import secrets
import sqlite3
import time
from pathlib import Path
from threading import Lock
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
ROOMS_DB = Path(__file__).with_name("rooms.db")
rooms_lock = Lock()
CODE_PATTERN = re.compile(r"^[ABCDEFGHJKLMNPQRSTUVWXYZ23456789]{6}$")


def db_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(ROOMS_DB, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def init_rooms_db() -> None:
    with db_connection() as connection:
        connection.execute("""CREATE TABLE IF NOT EXISTS rooms (
            id TEXT PRIMARY KEY, code TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
            owner_id TEXT NOT NULL, created_at INTEGER NOT NULL, status TEXT NOT NULL,
            participants_json TEXT NOT NULL
        )""")


init_rooms_db()


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


class CreateRoomRequest(BaseModel):
    name: str
    ownerId: str
    ownerName: str


# ----- ルーム管理エンドポイント -----

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/rooms", response_model=RoomModel)
def create_room(req: CreateRoomRequest) -> RoomModel:
    name = req.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Room name is required")
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    with rooms_lock, db_connection() as connection:
        for _ in range(10):
            code = "".join(secrets.choice(chars) for _ in range(6))
            if connection.execute("SELECT 1 FROM rooms WHERE code = ?", (code,)).fetchone() is None:
                break
        else:
            raise HTTPException(status_code=503, detail="Could not allocate an invitation code")
        room = RoomModel(
            id=secrets.token_hex(16), name=name, code=code, ownerId=req.ownerId,
            createdAt=int(time.time() * 1000),
            participants=[ParticipantModel(id=req.ownerId, name=req.ownerName, isAdmin=True)],
            status="waiting",
        )
        connection.execute(
            "INSERT INTO rooms VALUES (?, ?, ?, ?, ?, ?, ?)",
            (room.id, room.code, room.name, room.ownerId, room.createdAt, room.status,
             json.dumps([participant.model_dump() for participant in room.participants])),
        )
    return room


def row_to_room(row: sqlite3.Row) -> RoomModel:
    return RoomModel(
        id=row["id"], name=row["name"], code=row["code"], ownerId=row["owner_id"],
        createdAt=row["created_at"], status=row["status"],
        participants=json.loads(row["participants_json"]),
    )


def find_room(room_id: str) -> RoomModel:
    with db_connection() as connection:
        row = connection.execute("SELECT * FROM rooms WHERE id = ?", (room_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Room not found")
    return row_to_room(row)


def save_room(room: RoomModel) -> RoomModel:
    with rooms_lock, db_connection() as connection:
        connection.execute(
            "UPDATE rooms SET status = ?, participants_json = ? WHERE id = ?",
            (room.status, json.dumps([participant.model_dump() for participant in room.participants]), room.id),
        )
    return room


@app.get("/rooms", response_model=List[RoomModel])
def get_rooms() -> List[dict]:
    with db_connection() as connection:
        return [row_to_room(row) for row in connection.execute("SELECT * FROM rooms ORDER BY created_at DESC")]


@app.get("/rooms/by-code/{code}", response_model=RoomModel)
def get_room_by_code(code: str) -> dict:
    normalized = code.strip().upper()
    if not CODE_PATTERN.fullmatch(normalized):
        raise HTTPException(status_code=422, detail="Invalid invitation code format")
    with db_connection() as connection:
        row = connection.execute("SELECT * FROM rooms WHERE code = ?", (normalized,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Room not found")
    return row_to_room(row)


@app.get("/rooms/{room_id}", response_model=RoomModel)
def get_room(room_id: str) -> dict:
    return find_room(room_id)


@app.post("/rooms/{room_id}/join", response_model=RoomModel)
def join_room(room_id: str, req: JoinRoomRequest) -> dict:
    room = find_room(room_id)
    if room.status != "waiting":
        raise HTTPException(status_code=409, detail="Room is no longer accepting participants")
    already = any(p.id == req.id for p in room.participants)
    if not already:
        room.participants.append(ParticipantModel(id=req.id, name=req.name, isAdmin=False))
    return save_room(room)


@app.post("/rooms/{room_id}/leave", response_model=RoomModel)
def leave_room(room_id: str, req: LeaveRoomRequest) -> dict:
    room = find_room(room_id)
    room.participants = [p for p in room.participants if p.id != req.user_id]
    return save_room(room)


@app.post("/rooms/{room_id}/start", response_model=RoomModel)
def start_room(room_id: str) -> RoomModel:
    room = find_room(room_id)
    if room.status != "waiting":
        raise HTTPException(status_code=409, detail="Room has already started")
    room.status = "diagnosis"
    for participant in room.participants:
        participant.score = None
        participant.riskScore = None
        participant.prob3 = None
        participant.rank = None
    return save_room(room)


@app.put("/rooms/{room_id}/score", response_model=RoomModel)
def update_score(room_id: str, req: UpdateScoreRequest) -> dict:
    room = find_room(room_id)
    for p in room.participants:
        if p.id == req.user_id:
            p.score = req.score
            p.riskScore = req.riskScore
            p.prob3 = req.prob3
            break
    else:
        raise HTTPException(status_code=403, detail="User is not a room participant")
    if room.participants and all(p.score is not None for p in room.participants):
        room.status = "completed"
    return save_room(room)


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
