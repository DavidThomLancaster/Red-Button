import sqlite3, uuid
from typing import List, Dict, Optional
from shared.DTOs import EmailBatchRecord, EmailHeaderRecord, EmailStatus
from datetime import datetime

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
    
    # TODO Slice 8 - implement get_all_batches_for_job => List[EmailHeaderRecord]
    def get_email_headers_from_batch(self, batch_id: str) -> List[EmailHeaderRecord]:
        rows = self.conn.execute(
            """
            SELECT
            q.id                           AS email_id,
            q.batch_id                     AS batch_id,
            q.job_id                       AS job_id,
            q.contact_id                   AS contact_id,
            COALESCE(c.name, '')           AS contact_name,
            COALESCE(q.to_email, c.email, '') AS contact_email,
            q.subject                      AS subject,
            q.status                       AS status_raw,
            COALESCE(q.sent_at, CURRENT_TIMESTAMP) AS last_updated
            FROM email_queue q
            LEFT JOIN contacts c ON c.id = q.contact_id
            WHERE q.batch_id = ?
            ORDER BY contact_name, contact_email
            """,
            (batch_id,),
        ).fetchall()

        status_map = {
            "draft": EmailStatus.draft,
            "ready": EmailStatus.ready,
            "queued": EmailStatus.ready,
            "sending": EmailStatus.ready,
            "mock_sent": EmailStatus.mock_sent,
            "sent": EmailStatus.mock_sent,
            "failed": EmailStatus.failed,
        }

        headers: List[EmailHeaderRecord] = []
        for r in rows:
            # row unpacking by alias
            email_id, batch_id, job_id, contact_id, contact_name, contact_email, subject, status_raw, lu_raw = r

            # parse timestamp
            if isinstance(lu_raw, str):
                try:
                    last_updated = datetime.fromisoformat(lu_raw)
                except ValueError:
                    try:
                        last_updated = datetime.strptime(lu_raw.split('.')[0], "%Y-%m-%d %H:%M:%S")
                    except Exception:
                        last_updated = datetime.utcnow()
            else:
                last_updated = lu_raw or datetime.utcnow()

            status = status_map.get(status_raw, EmailStatus.draft)

            headers.append(
                EmailHeaderRecord(
                    id=email_id,
                    batch_id=batch_id,
                    job_id=job_id,
                    contact_id=contact_id,
                    contact_name=contact_name or contact_email or "",
                    contact_email=contact_email or "",
                    trade=None,   # you dropped c.trades from SELECT; fill in later if you need it
                    subject=subject,
                    status=status,
                    last_updated=last_updated,
                )
            )
        return headers
    
    # TODO Slice 8 - implement get_all_batches_for_job => List[EmailHeaderRecord]
    def get_all_batches_for_job(self, job_id: str) -> List[EmailBatchRecord]:
        """
        Returns all batches for a job as domain objects.
        Note: page_spec/page_count are None since the current table doesn't store them.
        """
        rows = self.conn.execute(
            """
            SELECT
              batch_id,
              job_id,
              template_version,
              created_at
            FROM email_batches
            WHERE job_id = ?
            ORDER BY datetime(created_at) DESC
            """,
            (job_id,),
        ).fetchall()

        batches: List[EmailBatchRecord] = []
        for r in rows:
            created_raw = r[3]
            if isinstance(created_raw, str):
                try:
                    created_at = datetime.fromisoformat(created_raw)
                except ValueError:
                    try:
                        created_at = datetime.strptime(created_raw.split('.')[0], "%Y-%m-%d %H:%M:%S")
                    except Exception:
                        created_at = datetime.utcnow()
            else:
                created_at = created_raw or datetime.utcnow()

            batches.append(
                EmailBatchRecord(
                    id=r[0],  # map batch_id -> id
                    job_id=r[1],
                    template_version=r[2],
                    created_at=created_at,
                    page_spec=None,
                    page_count=None,
                )
            )
        return batches
