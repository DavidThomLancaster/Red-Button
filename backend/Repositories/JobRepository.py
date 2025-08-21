import sqlite3
import uuid
from typing import Optional, Dict, List
from Utils.logger import get_logger
from shared.StorageRef import StorageRef, StorageMode
from Utils.logger import get_logger
log = get_logger(__name__) 

class JobRepository:
    def __init__(self, db_path="jobs.db", conn: sqlite3.Connection = None):
        if conn:
            self.conn = conn
        else:
            self.conn = sqlite3.connect(db_path, check_same_thread=False)

        self.conn.row_factory = sqlite3.Row
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                notes TEXT,
                status TEXT,
                pdf_ref TEXT,
                pdf_mode TEXT,
                images_ref TEXT,
                images_mode TEXT,
                prompt_ref TEXT,
                prompt_mode TEXT,
                csvs_ref TEXT,
                csvs_mode TEXT,
                jsons_ref TEXT,
                jsons_mode TEXT,
                current_mapped_contacts_ref TEXT,
                schema_ref TEXT,
                schema_mode TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def insert_new_job(self, user_id: str, job_name: str, notes: Optional[str] = None) -> str:
        job_id = str(uuid.uuid4())
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO jobs (job_id, user_id, name, notes, status) VALUES (?, ?, ?, ?, ?)",
            (job_id, user_id, job_name, notes, "created")
        )
        self.conn.commit()
        log.info("just inserted new job", extra={"user_id": user_id, "job_id": job_id})
        return job_id

    def get_jobs_by_user(self, user_id: str) -> List[Dict]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM jobs WHERE user_id = ?", (user_id,))
        rows = cur.fetchall()
        return [dict(row) for row in rows] if rows else []

    def get_job_by_id(self, job_id: str) -> Optional[Dict]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    def get_owner_id(self, job_id: str) -> Optional[str]:
        cur = self.conn.cursor()
        cur.execute("SELECT user_id FROM jobs WHERE job_id = ?", (job_id,))
        row = cur.fetchone()
        return row["user_id"] if row else None

    # def update_status_pdf_saved(self, job_id: str, pdf_ref: str):
    #     cur = self.conn.cursor()
    #     print("Hi from the Job Repository in update_status_pdf_saved " + pdf_ref + " : " + job_id)
    #     cur.execute(
    #         "UPDATE jobs SET status = ?, pdf_ref = ? WHERE job_id = ?",
    #         ("pdf_saved", pdf_ref, job_id)
    #     )
    #     self.conn.commit()

    def update_status_pdf_saved(self, job_id: str, pdf_ref: StorageRef):
        cur = self.conn.cursor()
       # print("Hi from the Job Repository in update_status_pdf_saved " + pdf_ref.location + " : " + job_id)
        log.info("Updating Status PDF Saved", extra={"job_id": job_id, "pdf_location": pdf_ref.location})
        cur.execute(
            "UPDATE jobs SET status = ?, pdf_ref = ?, pdf_mode = ? WHERE job_id = ?",
            ("pdf_saved", pdf_ref.location, pdf_ref.mode.value, job_id)
        )
        self.conn.commit()

    def update_status_images_extracted(self, job_id: str, images_ref: StorageRef):
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE jobs SET status = ?, images_ref = ?, images_mode = ? WHERE job_id = ?",
            ("images_extracted", images_ref.location, images_ref.mode.value, job_id)
        )
        self.conn.commit()

    def update_status_llm_run(self, job_id: str, csvs_ref: StorageRef, prompt_ref: StorageRef):
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE jobs SET status = ?, csvs_ref = ?, csvs_mode = ?, prompt_ref = ?, prompt_mode = ? WHERE job_id = ?",
            (
                "llm_run",
                csvs_ref.location, csvs_ref.mode.value,
                prompt_ref.location, prompt_ref.mode.value,
                job_id
            )
        )
        self.conn.commit()

    def update_status_csvs_combined(self, job_id, jsons_ref: StorageRef):
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE jobs SET status = ?, jsons_ref = ?, jsons_mode = ? WHERE job_id = ?",
            ("csvs_combined", jsons_ref.location, jsons_ref.mode.value, job_id)
        )
        self.conn.commit()

    def update_status_json_normalized(self, job_id: str, normalized_json_ref: StorageRef, schema_ref: StorageRef):
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE jobs SET status = ?, jsons_ref = ?, jsons_mode = ?, schema_ref = ?, schema_mode = ? WHERE job_id = ?",
            (
                "json_normalized",
                normalized_json_ref.location, normalized_json_ref.mode.value,
                schema_ref.location, schema_ref.mode.value, 
                job_id, 
            )
        )
        self.conn.commit()

    def update_status_contacts_map(self, job_id, contacts_map_ref):
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE jobs SET status = ?, current_mapped_contacts_ref = ? WHERE job_id = ?",
            (
                "contact_map_set",
                contacts_map_ref.location, 
                job_id, 
            )
        )
        self.conn.commit()

    def get_job(self, job_id: str):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
        row = cur.fetchone()
        return row

    def delete_job(self, job_id: str, soft: bool = True) -> bool:
        cur = self.conn.cursor()
        if soft:
            cur.execute(
                "UPDATE jobs SET status = ? WHERE job_id = ?",
                ("DELETED", job_id)
            )
        else:
            cur.execute(
                "DELETE FROM jobs WHERE job_id = ?",
                (job_id,)
            )
        self.conn.commit()
        return cur.rowcount > 0

    def delete_job_hard(self, job_id: str) -> bool:
        """
        Permanently deletes the job row. Assumes any dependent rows are set up
        with ON DELETE CASCADE. Returns True if a row was deleted.
        """
        cur = self.conn.cursor()
        # Ensure FK constraints are enforced for cascades
        cur.execute("PRAGMA foreign_keys = ON")
        cur.execute("DELETE FROM jobs WHERE job_id = ?", (job_id,))
        self.conn.commit()
        return cur.rowcount > 0
    

    def get_contacts_map_ref(self, job_id: str) -> Optional[str]:
        cur = self.conn.cursor()
        cur.execute("SELECT current_mapped_contacts_ref FROM jobs WHERE job_id = ?", (job_id,))
        row = cur.fetchone()
        return row["current_mapped_contacts_ref"] if row and row["current_mapped_contacts_ref"] else None

   








# # TODO - In production, handle connection pooling & proper closing
# # TODO - Build part that has updating job folder path and stuff. View Squence diagram for details

# class JobRepository:
#     def __init__(self, db_path="jobs.db", conn: sqlite3.Connection = None):
#         if conn:
#             self.conn = conn
#         else:
#             self.conn = sqlite3.connect(db_path, check_same_thread=False)

#         self.conn.row_factory = sqlite3.Row  # enables dict-like access
#         self.conn.execute('''
#             CREATE TABLE IF NOT EXISTS jobs (
#                 job_id TEXT PRIMARY KEY,
#                 user_id TEXT NOT NULL,
#                 name TEXT NOT NULL,
#                 notes TEXT,
#                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#             )
#         ''')
#         self.conn.commit()

#     def insert_new_job(self, user_id: str, job_name: str, notes: Optional[str] = None) -> str:
#         job_id = str(uuid.uuid4())
#         cur = self.conn.cursor()
#         cur.execute(
#             "INSERT INTO jobs (job_id, user_id, name, notes) VALUES (?, ?, ?, ?)",
#             (job_id, user_id, job_name, notes)
#         )
#         self.conn.commit()
#         return job_id

#     def get_jobs_by_user(self, user_id: str) -> List[Dict]:
#         cur = self.conn.cursor()
#         cur.execute("SELECT * FROM jobs WHERE user_id = ?", (user_id,))
#         rows = cur.fetchall()
#         return [dict(row) for row in rows] if rows else []

#     def get_job_by_id(self, job_id: str) -> Optional[Dict]:
#         cur = self.conn.cursor()
#         cur.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
#         row = cur.fetchone()
#         return dict(row) if row else None
    
#     def get_owner_id(job_id):
#         cur = self.conn.cursor()
#         cur.execute("SELECT user_id FROM jobs WHERE job_id = ?", (job_id,))
#         row = cur.fetchone()
#         return row["user_id"] if row else None


#     # Maybe we make an enum.py in core to inform this... maybe not. 
#     def update_status(job_id, images_extracted, image_output_dir):
#         pass
#         # TODO...

#     def update_status(job_id, pdf_saved, image_output_dir):
#         pass
#         # TODO...

#     def update_status(job_id, prompt_loaded, image_output_dir):
#         pass
#         # TODO...

#     def update_status_pdf_saved(self, job_id: str, pdf_ref: str):
#         cur = self.conn.cursor()
#         cur.execute(
#             "UPDATE jobs SET status = ?, pdf_ref = ? WHERE job_id = ?",
#             ("pdf_saved", pdf_ref, job_id)
#         )
#         self.conn.commit()