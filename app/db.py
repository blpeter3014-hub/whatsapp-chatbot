"""Persistencia del historial en PostgreSQL.

Si DATABASE_URL no está definida, se usa memoria (se pierde al reiniciar).
Así puedes probar el bot antes de instalar PostgreSQL.
"""
import os
from collections import defaultdict

import psycopg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

_memory_history: dict[str, list[dict]] = defaultdict(list)
_memory_seen: set[str] = set()

SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
    id            BIGSERIAL PRIMARY KEY,
    wa_message_id TEXT UNIQUE,
    wa_id         TEXT NOT NULL,
    role          TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content       TEXT NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_messages_wa_id_created
    ON messages (wa_id, created_at DESC);
"""


def using_postgres() -> bool:
    return bool(DATABASE_URL)


def init_db() -> None:
    if not using_postgres():
        print("[db] DATABASE_URL no definida: usando memoria temporal.")
        return
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute(SCHEMA)
    print("[db] PostgreSQL listo.")


def already_processed(wa_message_id: str) -> bool:
    """Meta puede reenviar el mismo webhook; evitamos responder dos veces."""
    if not using_postgres():
        if wa_message_id in _memory_seen:
            return True
        _memory_seen.add(wa_message_id)
        return False
    with psycopg.connect(DATABASE_URL) as conn:
        row = conn.execute(
            "SELECT 1 FROM messages WHERE wa_message_id = %s", (wa_message_id,)
        ).fetchone()
    return row is not None


def save_message(
    wa_id: str, role: str, content: str, wa_message_id: str | None = None
) -> None:
    if not using_postgres():
        _memory_history[wa_id].append({"role": role, "content": content})
        return
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute(
            """
            INSERT INTO messages (wa_message_id, wa_id, role, content)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (wa_message_id) DO NOTHING
            """,
            (wa_message_id, wa_id, role, content),
        )


def get_history(wa_id: str, limit: int = 10) -> list[dict]:
    """Últimos `limit` mensajes en orden cronológico (pocos tokens = más rápido)."""
    if not using_postgres():
        return _memory_history[wa_id][-limit:]
    with psycopg.connect(DATABASE_URL) as conn:
        rows = conn.execute(
            """
            SELECT role, content FROM (
                SELECT role, content, created_at, id
                FROM messages WHERE wa_id = %s
                ORDER BY created_at DESC, id DESC LIMIT %s
            ) t ORDER BY created_at ASC, id ASC
            """,
            (wa_id, limit),
        ).fetchall()
    return [{"role": r, "content": c} for r, c in rows]
