import sqlite3
import os
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "runs.db"

def get_db_connection() -> sqlite3.Connection:
    os.makedirs(DB_PATH.parent, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL,
                original_path TEXT,
                migrated_path TEXT,
                error TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                run_id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                generated_at TEXT NOT NULL,
                FOREIGN KEY(run_id) REFERENCES runs(id)
            )
        """)
        
        conn.commit()
    finally:
        conn.close()

def create_run(run_id: str, created_at: str, status: str):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO runs (id, created_at, status) VALUES (?, ?, ?)",
            (run_id, created_at, status)
        )
        conn.commit()
    finally:
        conn.close()

from typing import Optional

def update_run_status(run_id: str, status: str, error: Optional[str] = None):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE runs SET status = ?, error = ? WHERE id = ?",
            (status, error, run_id)
        )
        conn.commit()
    finally:
        conn.close()

def get_run(run_id: str) -> Optional[dict]:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, created_at, status, error FROM runs WHERE id = ?", (run_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        conn.close()

def save_report(run_id: str, data: str, generated_at: str):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO reports (run_id, data, generated_at) VALUES (?, ?, ?)",
            (run_id, data, generated_at)
        )
        conn.commit()
    finally:
        conn.close()

def get_report(run_id: str) -> Optional[dict]:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT run_id, data, generated_at FROM reports WHERE run_id = ?", (run_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        conn.close()

