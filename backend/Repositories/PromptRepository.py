# repositories/prompt_repository.py
import sqlite3
import uuid
from typing import List, Dict, Optional

class PromptRepository:
    def __init__(self, db_path="prompts.db", conn: sqlite3.Connection = None):
        if conn:
            self.conn = conn
        else:
            self.conn = sqlite3.connect(db_path, check_same_thread=False)

        self.conn.row_factory = sqlite3.Row
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS prompts (
                prompt_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                content TEXT NOT NULL,
                version INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 0
            )
        ''')
        self.conn.commit()

    def create_prompt(self, name: str, content: str, version: int = 1, is_active: bool = False) -> str:
        prompt_id = str(uuid.uuid4())
        self.conn.execute('''
            INSERT INTO prompts (prompt_id, name, content, version, is_active)
            VALUES (?, ?, ?, ?, ?)
        ''', (prompt_id, name, content, version, is_active))
        self.conn.commit()
        return prompt_id

    def get_active_prompt(self) -> Optional[Dict]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM prompts WHERE is_active = 1 LIMIT 1")
        row = cur.fetchone()
        return dict(row) if row else None

    def list_prompts(self) -> List[Dict]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM prompts ORDER BY created_at DESC")
        return [dict(row) for row in cur.fetchall()]

    def set_active_prompt(self, prompt_id: str):
        # Clear all actives
        self.conn.execute("UPDATE prompts SET is_active = 0")
        # Set new active
        self.conn.execute("UPDATE prompts SET is_active = 1 WHERE prompt_id = ?", (prompt_id,))
        self.conn.commit()

    def get_prompt_by_id(self, prompt_id: str) -> Optional[Dict]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM prompts WHERE prompt_id = ?", (prompt_id,))
        row = cur.fetchone()
        return dict(row) if row else None
