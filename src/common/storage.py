"""
SQLite storage for job queue and chat memory.
"""

import aiosqlite
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
from enum import Enum

from .config import config


class JobStatus(str, Enum):
    """Job processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SQLiteStorage:
    """SQLite storage manager for jobs and chat memory."""
    
    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_path = config.data_dir / "app.db"
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self):
        """Initialize database tables."""
        async with aiosqlite.connect(self.db_path) as db:
            # Jobs table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doc_id TEXT UNIQUE NOT NULL,
                    file_path TEXT NOT NULL,
                    language TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    error_message TEXT,
                    metadata TEXT
                )
            """)
            
            # Chat sessions table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)
            
            # Chat messages table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id)
                )
            """)
            
            # Create indexes
            await db.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_jobs_doc_id ON jobs(doc_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id)")
            
            await db.commit()
    
    # Job management methods
    async def add_job(self, doc_id: str, file_path: str, language: str, metadata: Optional[Dict] = None) -> int:
        """Add a new job to the queue."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO jobs (doc_id, file_path, language, status, metadata)
                VALUES (?, ?, ?, ?, ?)
                """,
                (doc_id, file_path, language, JobStatus.PENDING, json.dumps(metadata or {}))
            )
            await db.commit()
            return cursor.lastrowid
    
    async def get_pending_jobs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get pending jobs from the queue."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM jobs WHERE status = ? ORDER BY created_at LIMIT ?",
                (JobStatus.PENDING, limit)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def update_job_status(self, doc_id: str, status: JobStatus, error_message: Optional[str] = None):
        """Update job status."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE jobs 
                SET status = ?, error_message = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE doc_id = ?
                """,
                (status, error_message, doc_id)
            )
            await db.commit()
    
    async def get_job(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a job by doc_id."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM jobs WHERE doc_id = ?", (doc_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    
    # Chat memory methods
    async def create_session(self, session_id: str, metadata: Optional[Dict] = None):
        """Create a new chat session."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR IGNORE INTO chat_sessions (session_id, metadata) VALUES (?, ?)",
                (session_id, json.dumps(metadata or {}))
            )
            await db.commit()
    
    async def add_message(self, session_id: str, role: str, content: str, metadata: Optional[Dict] = None):
        """Add a message to a chat session."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO chat_messages (session_id, role, content, metadata)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, role, content, json.dumps(metadata or {}))
            )
            await db.commit()
    
    async def get_session_messages(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get messages for a chat session."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            query = "SELECT * FROM chat_messages WHERE session_id = ? ORDER BY created_at"
            if limit:
                query += f" LIMIT {limit}"
            async with db.execute(query, (session_id,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def get_recent_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent chat sessions."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM chat_sessions ORDER BY created_at DESC LIMIT ?",
                (limit,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def clear_session(self, session_id: str):
        """Clear all messages from a session."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "DELETE FROM chat_messages WHERE session_id = ?",
                (session_id,)
            )
            await db.commit()


# Global storage instance
storage = SQLiteStorage()

