import sqlite3
from pathlib import Path

DATABASE_FILE = "todos.db"

# TODO: make the database path configurable via an env var so tests can use a temp file
def get_db_connection():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row  # This allows accessing columns by name
    return conn

# Initialize the database and create the table if it doesn't exist
with get_db_connection() as conn:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL DEFAULT 0,
            due_date TEXT
        );
        """
    )
    conn.commit()
