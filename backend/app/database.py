import os
import sqlite3
from backend.app.config import DB_PATH

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS monitors (
        id TEXT PRIMARY KEY,
        name TEXT,
        url TEXT,
        method TEXT DEFAULT 'GET',
        interval_seconds INTEGER DEFAULT 60,
        expected_status INTEGER DEFAULT 200,
        status TEXT DEFAULT 'UP',
        uptime_pct REAL DEFAULT 100.0,
        avg_latency_ms REAL DEFAULT 0.0,
        created_at TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS probe_logs (
        id TEXT PRIMARY KEY,
        monitor_id TEXT,
        status_code INTEGER,
        latency_ms REAL,
        is_up INTEGER,
        error_msg TEXT,
        checked_at TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS incidents (
        id TEXT PRIMARY KEY,
        monitor_id TEXT,
        title TEXT,
        cause TEXT,
        started_at TEXT,
        resolved_at TEXT,
        duration_seconds INTEGER
    );
    """)

    conn.commit()
    conn.close()

init_db()
