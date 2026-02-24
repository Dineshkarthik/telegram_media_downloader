"""Database helper for tracking download history."""

import logging
import os
import sqlite3
from typing import Optional

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(THIS_DIR, "downloads.sqlite3")
_db_initialized = False


def get_connection():
    """Get a connection to the SQLite database."""
    return sqlite3.connect(DB_PATH)


def init_db():
    """Initialize the SQLite database and create the history table if it doesn't exist."""
    global _db_initialized
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS download_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id TEXT NOT NULL,
                    message_id INTEGER NOT NULL,
                    file_name TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    download_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    file_path TEXT
                )
            """
            )
            # Migration check: add file_path if it doesn't exist
            cursor.execute("PRAGMA table_info(download_history)")
            columns = [c[1] for c in cursor.fetchall()]
            if "file_path" not in columns:
                cursor.execute("ALTER TABLE download_history ADD COLUMN file_path TEXT")
            if "media_type" not in columns:
                cursor.execute(
                    "ALTER TABLE download_history ADD COLUMN media_type TEXT"
                )

            # Create an index for faster queries on recent downloads
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_timestamp ON download_history(download_timestamp DESC)"
            )
            conn.commit()
        _db_initialized = True
    except Exception as e:
        logger = logging.getLogger("media_downloader")
        logger.error(f"Failed to initialize database: {e}")


def _ensure_db():
    """Lazily initialize the database on first use."""
    if not _db_initialized:
        init_db()


def record_download(
    chat_id: str,
    message_id: int,
    file_name: str,
    file_size: int,
    file_path: Optional[str] = None,
    media_type: Optional[str] = None,
):
    """Record a successful download in the history table."""
    _ensure_db()
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO download_history (chat_id, message_id, file_name, file_size, file_path, media_type)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (str(chat_id), message_id, file_name, file_size, file_path, media_type),
            )
            conn.commit()
    except Exception as e:
        logger = logging.getLogger("media_downloader")
        logger.error(f"Failed to record download history for {file_name}: {e}")


def reset_history():
    """Clear all download history."""
    _ensure_db()
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM download_history")
            conn.commit()
    except Exception as e:
        logger = logging.getLogger("media_downloader")
        logger.error(f"Failed to reset download history: {e}")


def get_recent_downloads(
    limit: int = 100,
    offset: int = 0,
    search_item: str = "",
    media_type: str = "All",
    sort_by: str = "download_timestamp",
    sort_desc: bool = True,
):
    """Retrieve the most recent downloads with optional search and sorting."""
    _ensure_db()
    try:
        with get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Map valid sort columns to prevent SQL injection
            valid_sort_cols = {
                "timestamp": "download_timestamp",
                "chat": "chat_id",
                "filename": "file_name",
                "size": "file_size",
                "media_type": "media_type",
                # Also fallbacks for safety:
                "download_timestamp": "download_timestamp",
                "chat_id": "chat_id",
                "file_name": "file_name",
                "size_mb": "file_size",
            }
            order_col = valid_sort_cols.get(sort_by, "download_timestamp")
            order_dir = "DESC" if sort_desc else "ASC"

            query = f"""
                SELECT id, chat_id, message_id, file_name, file_size, download_timestamp, file_path, media_type
                FROM download_history
                WHERE 1=1
            """
            count_query = "SELECT COUNT(*) FROM download_history WHERE 1=1"

            params = []

            if search_item:
                search_clause = " AND (file_name LIKE ? OR chat_id LIKE ?)"
                query += search_clause
                count_query += search_clause
                params.extend([f"%{search_item}%", f"%{search_item}%"])

            if media_type and media_type != "All":
                type_clause = " AND media_type = ?"
                query += type_clause
                count_query += type_clause
                params.append(media_type)

            query += f" ORDER BY {order_col} {order_dir} LIMIT ? OFFSET ?"

            # Execute main query
            cursor.execute(query, (*params, limit, offset))
            records = [dict(row) for row in cursor.fetchall()]

            # Execute count query
            cursor.execute(count_query, params)
            total_count = cursor.fetchone()[0]

            return records, total_count
    except Exception as e:
        logger = logging.getLogger("media_downloader")
        logger.error(f"Failed to fetch download history: {e}")
        return [], 0
