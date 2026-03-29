from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Any

from .models import Message


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SQLiteMemoryStore:
    def __init__(self, db_path: str) -> None:
        self.db_path = str(Path(db_path))
        self._init_db()

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS cache_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    query_text TEXT NOT NULL,
                    embedding_json TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    route TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    def add_message(self, session_id: str, role: str, content: str) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
                (session_id, role, content, utc_now()),
            )

    def get_messages(self, session_id: str) -> list[Message]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT role, content, created_at FROM messages WHERE session_id = ? ORDER BY id ASC",
                (session_id,),
            ).fetchall()
        return [Message(role=row["role"], content=row["content"], created_at=row["created_at"]) for row in rows]

    def clear_session(self, session_id: str) -> None:
        with self._conn() as conn:
            conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM cache_entries WHERE session_id = ?", (session_id,))

    def add_cache_entry(
        self,
        *,
        session_id: str,
        query_text: str,
        embedding: list[float],
        answer: str,
        route: str,
    ) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO cache_entries (
                    session_id, query_text, embedding_json, answer, route, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    query_text,
                    json.dumps(embedding),
                    answer,
                    route,
                    utc_now(),
                ),
            )

    def list_cache_entries(self, session_id: str) -> list[dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT query_text, embedding_json, answer, route, created_at
                FROM cache_entries
                WHERE session_id = ?
                ORDER BY id DESC
                """,
                (session_id,),
            ).fetchall()
        return [
            {
                "query_text": row["query_text"],
                "embedding": json.loads(row["embedding_json"]),
                "answer": row["answer"],
                "route": row["route"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]
