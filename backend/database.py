"""Async SQLite database setup and table creation."""

import aiosqlite
from pathlib import Path
from config import settings


async def get_db() -> aiosqlite.Connection:
    """Get an async database connection."""
    db_path = Path(settings.database_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    db = await aiosqlite.connect(str(db_path))
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db


async def init_db():
    """Create tables if they don't exist."""
    db = await get_db()
    try:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                email       TEXT    NOT NULL UNIQUE COLLATE NOCASE,
                name        TEXT    NOT NULL,
                password_hash TEXT  NOT NULL,
                role        TEXT    NOT NULL DEFAULT 'viewer',
                is_active   INTEGER NOT NULL DEFAULT 1,
                created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
                updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id             INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                refresh_token_hash  TEXT    NOT NULL,
                expires_at          TEXT    NOT NULL,
                created_at          TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS app_settings (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
            CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);

            -- Default app settings
            INSERT OR IGNORE INTO app_settings (key, value) VALUES ('allow_signup', 'false');
        """)
        await db.commit()
    finally:
        await db.close()


async def has_users() -> bool:
    """Check if any users exist (for initial setup flow)."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT COUNT(*) as count FROM users")
        row = await cursor.fetchone()
        return row[0] > 0  # type: ignore
    finally:
        await db.close()


async def get_app_setting(key: str, default: str = "") -> str:
    """Get an app setting by key."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT value FROM app_settings WHERE key = ?", (key,)
        )
        row = await cursor.fetchone()
        return row[0] if row else default  # type: ignore
    finally:
        await db.close()


async def set_app_setting(key: str, value: str):
    """Set an app setting (upsert)."""
    db = await get_db()
    try:
        await db.execute(
            "INSERT OR REPLACE INTO app_settings (key, value) VALUES (?, ?)",
            (key, value),
        )
        await db.commit()
    finally:
        await db.close()

