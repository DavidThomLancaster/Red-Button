import sqlite3
import uuid
from typing import Optional, Dict

from Utils.logger import get_logger
log = get_logger(__name__)

# TODO - We need to eventually close the connection when we do the professional version of this!

class UserRepository:
    def __init__(self, db_path="users.db", conn: sqlite3.Connection = None):
        if conn:
            self.conn = conn
        else:
            self.conn = sqlite3.connect(db_path, check_same_thread=False)

        self.conn.row_factory = sqlite3.Row
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def find_by_email(self, email: str) -> Optional[Dict]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cur.fetchone()
        return dict(row) if row else None

    def create_user(self, email: str, password_hash: str) -> str:
        user_id = str(uuid.uuid4())
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO users (user_id, email, password_hash) VALUES (?, ?, ?)",
            (user_id, email, password_hash)
        )
        self.conn.commit()
        log.info("Created User!", extra={"user_id": user_id, "email": email})
        return user_id
