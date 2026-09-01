import json
import sqlite3
from pathlib import Path

from app.config import DATABASE_PATH


def _ensure_db_dir() -> None:
    Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    _ensure_db_dir()
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS profiles (
                name TEXT PRIMARY KEY,
                payload TEXT NOT NULL
            )
            """
        )
        conn.commit()


def load_profiles() -> dict:
    init_db()
    with get_connection() as conn:
        rows = conn.execute("SELECT name, payload FROM profiles").fetchall()
    return {row["name"]: json.loads(row["payload"]) for row in rows}


def save_profiles(profiles: dict) -> None:
    init_db()
    with get_connection() as conn:
        for name, profile in profiles.items():
            conn.execute(
                "INSERT INTO profiles(name, payload) VALUES(?, ?) "
                "ON CONFLICT(name) DO UPDATE SET payload = excluded.payload",
                (name, json.dumps(profile, ensure_ascii=False, indent=2)),
            )
        conn.commit()
