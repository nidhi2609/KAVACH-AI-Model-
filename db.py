"""SQLite storage (standard library only). Privacy by default: transcripts are kept only while a
call session is active, then wiped, unless the user opted in with store_text=true."""
import hashlib
import os
import re
import sqlite3
import time
from contextlib import contextmanager

DB_PATH = os.getenv("KAVACH_DB", "kavach.db")
SALT = os.getenv("KAVACH_SALT", "change-me")
STALE_SECONDS = 3600
MAX_TRANSCRIPT = 20000

SCHEMA = """
CREATE TABLE IF NOT EXISTS devices(
  id TEXT PRIMARY KEY, token_hash TEXT NOT NULL, created_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS sessions(
  id TEXT PRIMARY KEY,
  device_id TEXT NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
  started_at REAL NOT NULL, updated_at REAL NOT NULL, ended_at REAL,
  caller_hash TEXT, store_text INTEGER NOT NULL DEFAULT 0,
  transcript TEXT NOT NULL DEFAULT '', max_score INTEGER NOT NULL DEFAULT 0,
  alerted INTEGER NOT NULL DEFAULT 0, signals TEXT NOT NULL DEFAULT '[]');
CREATE TABLE IF NOT EXISTS number_reports(
  number_hash TEXT NOT NULL,
  device_id TEXT NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
  category TEXT, created_at REAL NOT NULL, PRIMARY KEY(number_hash, device_id));
CREATE INDEX IF NOT EXISTS idx_sessions_device ON sessions(device_id, started_at);
"""


@contextmanager
def get_db():
    c = sqlite3.connect(DB_PATH, timeout=10)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    try:
        yield c
        c.commit()
    finally:
        c.close()


def init():
    with get_db() as c:
        c.executescript(SCHEMA)


def hash_token(secret):
    return hashlib.sha256((secret or "").encode()).hexdigest()


def hash_number(number):
    digits = re.sub(r"\D", "", number or "")[-10:]
    if len(digits) < 7:
        return None
    return hashlib.sha256((SALT + digits).encode()).hexdigest()


def purge_stale():
    """Sessions abandoned without /end: close them and wipe the text unless opted in."""
    now = time.time()
    with get_db() as c:
        c.execute("UPDATE sessions SET ended_at=updated_at, transcript=CASE WHEN store_text=1 THEN transcript ELSE '' END "
                  "WHERE ended_at IS NULL AND updated_at < ?", (now - STALE_SECONDS,))


init()
