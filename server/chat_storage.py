from typing import List, Dict, Any
from datetime import datetime
import json

from db import get_connection


def _now_iso() -> str:
    """Return current UTC time as ISO string."""
    return datetime.utcnow().isoformat()


# ====== sessions ======
def get_next_session_id() -> int:
    """
    يرجّع session_id جديد (max + 1) بناءً على جدول messages.
    لو ما فيش جلسات، يرجع 1.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COALESCE(MAX(session_id), 0) + 1 AS next_id FROM messages")
        row = cur.fetchone()
        return row["next_id"]
    finally:
        conn.close()


def list_sessions() -> List[Dict[str, Any]]:
    """
    يرجّع قائمة الجلسات الموجودة من جدول messages.
    كل عنصر: {session_id, started_at, updated_at}
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                session_id,
                MIN(created_at) AS started_at,
                MAX(created_at) AS updated_at
            FROM messages
            GROUP BY session_id
            ORDER BY updated_at DESC
            """
        )
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ====== messages ======
def load_messages(session_id: int) -> List[Dict[str, str]]:
    """
    يرجّع رسائل جلسة معيّنة بالشكل:
    [{ "role": "user" | "assistant", "content": "..." }, ...]
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT role, content
            FROM messages
            WHERE session_id = ?
            ORDER BY id
            """,
            (session_id,),
        )
        rows = cur.fetchall()
        return [{"role": r["role"], "content": r["content"]} for r in rows]
    finally:
        conn.close()


def save_message(session_id: int, role: str, content: str) -> None:
    """
    يحفظ رسالة في جدول messages.
    يفترض إن جدول messages فيه الأعمدة:
        id INTEGER PK,
        session_id INTEGER,
        role TEXT,
        content TEXT,
        created_at TEXT NOT NULL
    """
    conn = get_connection()
    try:
        cur = conn.cursor()

        created_at = _now_iso()

        cur.execute(
            """
            INSERT INTO messages (session_id, role, content, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (session_id, role, content, created_at),
        )
        conn.commit()
    finally:
        conn.close()


# ====== tool_calls ======
def log_tool_call(
    session_id: int,
    name: str,
    args: dict,
    result: Any,
) -> None:
    """
    يسجّل استدعاء tool في جدول tool_calls.
    يفترض إن جدول tool_calls فيه الأعمدة:
        id INTEGER PK,
        session_id INTEGER,
        name TEXT,
        args_json TEXT,
        result_json TEXT,
        created_at TEXT NOT NULL
    """
    conn = get_connection()
    try:
        cur = conn.cursor()

        created_at = _now_iso()

        cur.execute(
            """
            INSERT INTO tool_calls (session_id, name, args_json, result_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                session_id,
                name,
                json.dumps(args, ensure_ascii=False),
                json.dumps(result, ensure_ascii=False),
                created_at,
            ),
        )
        conn.commit()
    finally:
        conn.close()
