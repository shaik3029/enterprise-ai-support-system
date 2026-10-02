import os
import sqlite3
import uuid
from datetime import datetime

from database.db_manager import DB_PATH

VOICE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "support_audio")
)

def init_voice_support():
    os.makedirs(VOICE_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS support_voice_requests (
            request_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            stored_filename TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'READY',
            created_at TEXT NOT NULL,
            transcript TEXT,
            analysis TEXT,
            analyzed_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_voice_request(user_id: str, original_filename: str, file_bytes: bytes):
    extension = os.path.splitext(original_filename or "")[1].lower()
    if extension not in {".wav", ".mp3", ".m4a", ".webm"}:
        raise ValueError("Unsupported audio format. Allowed: WAV, MP3, M4A, WEBM.")

    safe_name = f"{uuid.uuid4().hex}{extension}"
    file_path = os.path.join(VOICE_DIR, safe_name)

    with open(file_path, "wb") as buffer:
        buffer.write(file_bytes)

    created_at = datetime.utcnow().isoformat()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO support_voice_requests
        (user_id, original_filename, stored_filename, status, created_at)
        VALUES (?, ?, ?, 'READY', ?)
    """, (user_id, original_filename, safe_name, created_at))
    request_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {
        "request_id": request_id,
        "user_id": user_id,
        "filename": original_filename,
        "status": "READY",
        "created_at": created_at,
        "file_path": file_path,
    }

def get_voice_requests():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT request_id, user_id, original_filename, status,
               created_at, analyzed_at
        FROM support_voice_requests
        ORDER BY request_id DESC
    """).fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_user_voice_requests(user_id: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT request_id, user_id, original_filename, status,
               created_at, analyzed_at
        FROM support_voice_requests
        WHERE user_id = ?
        ORDER BY request_id DESC
    """, (user_id,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_voice_request(request_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM support_voice_requests WHERE request_id = ?",
        (request_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None

def mark_voice_analyzed(request_id: int, transcript: str, analysis: str):
    analyzed_at = datetime.utcnow().isoformat()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE support_voice_requests
        SET status = 'ANALYZED', transcript = ?, analysis = ?, analyzed_at = ?
        WHERE request_id = ?
    """, (transcript, analysis, analyzed_at, request_id))
    updated = cursor.rowcount
    conn.commit()
    conn.close()
    return updated

def get_voice_file_path(request_id: int):
    request = get_voice_request(request_id)
    if not request:
        return None
    path = os.path.join(VOICE_DIR, request["stored_filename"])
    return path if os.path.exists(path) else None
