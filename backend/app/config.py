import os

PORT = int(os.getenv("UPTIMEX_PORT", "8000"))
DB_PATH = os.getenv("UPTIMEX_DB_PATH", "backend/data/uptimex.db")
