import hashlib
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


def hash_password(value: str) -> str:
    return hashlib.sha256(value.strip().encode("utf-8")).hexdigest()


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                password_hash TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS profiles (
                user_email TEXT NOT NULL,
                name TEXT NOT NULL,
                payload TEXT NOT NULL,
                PRIMARY KEY (user_email, name)
            )
            """
        )
        conn.commit()


def load_profiles(user_email: str | None = None) -> dict:
    init_db()
    with get_connection() as conn:
        if user_email:
            rows = conn.execute(
                "SELECT name, payload FROM profiles WHERE user_email = ?",
                (user_email,),
            ).fetchall()
        else:
            rows = conn.execute("SELECT name, payload FROM profiles").fetchall()
    return {row["name"]: json.loads(row["payload"]) for row in rows}


def save_profiles(profiles: dict, user_email: str | None = None) -> None:
    init_db()
    with get_connection() as conn:
        if user_email is None:
            for name, profile in profiles.items():
                conn.execute(
                    "INSERT INTO profiles(user_email, name, payload) VALUES(?, ?, ?) "
                    "ON CONFLICT(user_email, name) DO UPDATE SET payload = excluded.payload",
                    (profile.get("user_email") or "", name, json.dumps(profile, ensure_ascii=False, indent=2)),
                )
        else:
            for name, profile in profiles.items():
                if profile.get("user_email") != user_email:
                    continue
                conn.execute(
                    "INSERT INTO profiles(user_email, name, payload) VALUES(?, ?, ?) "
                    "ON CONFLICT(user_email, name) DO UPDATE SET payload = excluded.payload",
                    (user_email, name, json.dumps(profile, ensure_ascii=False, indent=2)),
                )
        conn.commit()


def get_user_by_email(email: str) -> dict | None:
    init_db()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT email, name, password_hash FROM users WHERE email = ?",
            (email.lower().strip(),),
        ).fetchone()
    if row is None:
        return None
    return {"email": row["email"], "name": row["name"], "password_hash": row["password_hash"]}


def create_user(email: str, name: str, password: str) -> dict:
    init_db()
    email = email.lower().strip()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO users(email, name, password_hash) VALUES (?, ?, ?)",
            (email, name.strip(), hash_password(password)),
        )
        conn.commit()
    return {"email": email, "name": name.strip()}


def verify_user(email: str, password: str) -> dict | None:
    user = get_user_by_email(email)
    if user is None:
        return None
    if user["password_hash"] != hash_password(password):
        return None
    return {"email": user["email"], "name": user["name"]}
