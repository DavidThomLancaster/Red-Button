import sqlite3, uuid
from typing import List, Dict, Optional

class EmailRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.ensure_schema()

    def ensure_schema(self):
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS email_batches (
          batch_id TEXT PRIMARY KEY,
          job_id   TEXT NOT NULL,
          contacts_map_ref TEXT NOT NULL,
          template_version TEXT,
          template_ref TEXT,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          status TEXT DEFAULT 'generated' -- generated|queued|sending|completed|superseded
          -- FOREIGN KEY (job_id) REFERENCES jobs(job_id)  -- add later if you want strict FKs
        );

        CREATE TABLE IF NOT EXISTS email_queue (
          id TEXT PRIMARY KEY,
          batch_id   TEXT NOT NULL,
          job_id     TEXT NOT NULL,
          contact_id TEXT NOT NULL,
          to_email   TEXT NOT NULL,
          subject    TEXT NOT NULL,
          body       TEXT NOT NULL,
          status     TEXT NOT NULL DEFAULT 'draft', -- draft|queued|sending|sent|failed
          attempts   INTEGER NOT NULL DEFAULT 0,
          last_error TEXT,
          sent_at    TIMESTAMP,
          dedupe_key TEXT UNIQUE
          -- FOREIGN KEY (batch_id) REFERENCES email_batches(batch_id),
          -- FOREIGN KEY (job_id)   REFERENCES jobs(job_id)
        );

        CREATE INDEX IF NOT EXISTS idx_email_queue_status ON email_queue(status);
        CREATE INDEX IF NOT EXISTS idx_email_queue_batch  ON email_queue(batch_id);
        """)
        self.conn.commit()

    def create_batch(self, job_id: str, contacts_map_ref: str,
                     template_version: str, template_ref: Optional[str]) -> str:
        batch_id = str(uuid.uuid4())
        self.conn.execute("""
          INSERT INTO email_batches (batch_id, job_id, contacts_map_ref, template_version, template_ref)
          VALUES (?, ?, ?, ?, ?)
        """, (batch_id, job_id, contacts_map_ref, template_version, template_ref))
        self.conn.commit()
        return batch_id

    def bulk_insert_queue(self, rows: List[Dict]):
        self.conn.executemany("""
          INSERT INTO email_queue
            (id, batch_id, job_id, contact_id, to_email, subject, body, status, dedupe_key)
          VALUES
            (:id, :batch_id, :job_id, :contact_id, :to_email, :subject, :body, :status, :dedupe_key)
        """, rows)
        self.conn.commit()

    def mark_job_last_batch(self, job_id: str, batch_id: str):
        self.conn.execute("""
          ALTER TABLE jobs ADD COLUMN last_email_batch_id TEXT
        """)
        self.conn.execute("""
          ALTER TABLE jobs ADD COLUMN last_email_batch_created_at TIMESTAMP
        """)
        # Ignore errors if columns already exist
        self.conn.commit()
        self.conn.execute("""
          UPDATE jobs
          SET last_email_batch_id = ?, last_email_batch_created_at = CURRENT_TIMESTAMP
          WHERE job_id = ?
        """, (batch_id, job_id))
        self.conn.commit()

    def create_email(self, batch_id: str, job_id: str, contact_id: str,
                     to_email: str, subject: str, body: str,
                     status: str = "draft") -> str:
        """
        Insert a single email into the email_queue.
        Returns the generated email id.
        """
        email_id = str(uuid.uuid4())
        dedupe_key = str(uuid.uuid4())#f"{batch_id}:{contact_id}:{subject}" eventually, I'll have to fix this. TODO

        self.conn.execute("""
          INSERT INTO email_queue
            (id, batch_id, job_id, contact_id, to_email, subject, body, status, dedupe_key)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (email_id, batch_id, job_id, contact_id, to_email, subject, body, status, dedupe_key))

        self.conn.commit()
        return email_id
