"""SQLite Storage Service for document deduplication, chat session management, and conversation history."""
import json
import logging
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class SQLiteStore:
    """Manages SQLite database for document deduplication, chat sessions, and message persistence."""

    def __init__(self, db_path: str = "./data/documind.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Create and return a database connection with row factory enabled."""
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self) -> None:
        """Initialize database tables and indexes."""
        with self._get_connection() as conn:
            # 1. Document hashes for byte-for-byte deduplication
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS document_hashes (
                    file_hash TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_doc_hashes_doc_id ON document_hashes(document_id);"
            )

            # 2. Chat sessions (topics)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    session_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )

            # 3. Chat messages (conversation history)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_messages (
                    message_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    citations_json TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE
                );
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id, created_at);"
            )
            conn.commit()
        logger.info("SQLite store initialized at '%s'", self.db_path)

    # --------------------------------------------------------------------------
    # Document Hash Deduplication Operations
    # --------------------------------------------------------------------------

    def register_document_hash(self, file_hash: str, document_id: str, filename: str) -> None:
        """Register SHA-256 hash of an uploaded document to detect future duplicate uploads."""
        now = datetime.utcnow().isoformat()
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO document_hashes (file_hash, document_id, filename, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (file_hash, document_id, filename, now),
            )
            conn.commit()

    def get_document_by_hash(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """Look up existing document metadata record by exact byte-for-byte file hash."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT file_hash, document_id, filename, created_at FROM document_hashes WHERE file_hash = ?",
                (file_hash,),
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def delete_hash_by_document_id(self, document_id: str) -> None:
        """Remove hash mapping when a document is deleted."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM document_hashes WHERE document_id = ?", (document_id,))
            conn.commit()

    # --------------------------------------------------------------------------
    # Chat Session / Topic Operations
    # --------------------------------------------------------------------------

    def create_session(self, title: str = "New Chat", session_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new chat session topic."""
        s_id = session_id or str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO chat_sessions (session_id, title, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (s_id, title.strip() or "New Chat", now, now),
            )
            conn.commit()
        return {
            "session_id": s_id,
            "title": title.strip() or "New Chat",
            "created_at": now,
            "updated_at": now,
            "message_count": 0,
        }

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all chat sessions ordered by latest activity with message counts."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT s.session_id, s.title, s.created_at, s.updated_at,
                       COUNT(m.message_id) AS message_count
                FROM chat_sessions s
                LEFT JOIN chat_messages m ON s.session_id = m.session_id
                GROUP BY s.session_id
                ORDER BY s.updated_at DESC
                """
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a single chat session by ID."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT s.session_id, s.title, s.created_at, s.updated_at,
                       COUNT(m.message_id) AS message_count
                FROM chat_sessions s
                LEFT JOIN chat_messages m ON s.session_id = m.session_id
                WHERE s.session_id = ?
                GROUP BY s.session_id
                """,
                (session_id,),
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def update_session_title(self, session_id: str, title: str) -> bool:
        """Update session topic title."""
        now = datetime.utcnow().isoformat()
        with self._get_connection() as conn:
            cursor = conn.execute(
                "UPDATE chat_sessions SET title = ?, updated_at = ? WHERE session_id = ?",
                (title.strip(), now, session_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_session(self, session_id: str) -> bool:
        """Delete a chat session and all cascading messages."""
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM chat_sessions WHERE session_id = ?", (session_id,))
            conn.commit()
            return cursor.rowcount > 0

    # --------------------------------------------------------------------------
    # Chat Message & Context Operations
    # --------------------------------------------------------------------------

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        citations: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Add a message to a session and touch session updated_at."""
        message_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        citations_str = json.dumps(citations) if citations else None

        with self._get_connection() as conn:
            # Ensure session exists; if not, create it automatically
            cursor = conn.execute("SELECT session_id FROM chat_sessions WHERE session_id = ?", (session_id,))
            if not cursor.fetchone():
                title = content[:40].strip() or "New Chat"
                conn.execute(
                    "INSERT INTO chat_sessions (session_id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                    (session_id, title, now, now),
                )

            conn.execute(
                """
                INSERT INTO chat_messages (message_id, session_id, role, content, citations_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (message_id, session_id, role, content, citations_str, now),
            )
            # Update session's updated_at
            conn.execute("UPDATE chat_sessions SET updated_at = ? WHERE session_id = ?", (now, session_id))
            conn.commit()

        return {
            "message_id": message_id,
            "session_id": session_id,
            "role": role,
            "content": content,
            "citations": citations or [],
            "created_at": now,
        }

    def get_session_messages(self, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve historical messages for a session ordered chronologically."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT message_id, session_id, role, content, citations_json, created_at
                FROM chat_messages
                WHERE session_id = ?
                ORDER BY created_at ASC
                LIMIT ?
                """,
                (session_id, limit),
            )
            messages = []
            for row in cursor.fetchall():
                d = dict(row)
                raw_citations = d.pop("citations_json", None)
                d["citations"] = json.loads(raw_citations) if raw_citations else []
                messages.append(d)
            return messages

    def get_recent_context(self, session_id: str, max_turns: int = 5) -> List[Dict[str, str]]:
        """Retrieve recent dialogue turns (role, content) for prompt context."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT role, content
                FROM chat_messages
                WHERE session_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (session_id, max_turns * 2),
            )
            rows = cursor.fetchall()
            # Reverse to chronological order
            return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]
