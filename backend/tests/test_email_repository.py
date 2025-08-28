import sqlite3
from datetime import datetime
import uuid
import pytest

#  Adjust this import to your project layout if needed
from Repositories.EmailRepository import EmailRepository
from shared.DTOs import EmailBatchRecord

@pytest.fixture
def conn():
    # In-memory DB for a clean test each run
    return sqlite3.connect(":memory:")

def seed_batches(conn, job_id: str):
    """
    Inserts two batches for job_id and one for another job to verify filtering.
    """
    repo = EmailRepository(conn)  # ensures schema
    # Insert sample rows with fixed timestamps so ordering is deterministic
    rows = [
        (
            str(uuid.uuid4()), job_id, "contacts/ref1.json", "v1", None,
            "2025-08-26 12:00:00", "generated"
        ),
        (
            str(uuid.uuid4()), job_id, "contacts/ref2.json", "v2", None,
            "2025-08-27 15:30:00", "generated"
        ),
        # Different job (should not appear)
        (
            str(uuid.uuid4()), "OTHER_JOB", "contacts/other.json", "v1", None,
            "2025-08-25 09:00:00", "generated"
        ),
    ]
    conn.executemany("""
      INSERT INTO email_batches
        (batch_id, job_id, contacts_map_ref, template_version, template_ref, created_at, status)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    """, rows)
    conn.commit()
    return repo  # reuse the same repo/conn

def test_get_all_batches_for_job_prints(conn, capsys):
    job_id = "JOB_123"
    repo = seed_batches(conn, job_id)

    batches = repo.get_all_batches_for_job(job_id)

    # Basic assertions so the test is meaningful
    assert isinstance(batches, list)
    assert len(batches) == 2
    assert all(isinstance(b, EmailBatchRecord) for b in batches)

    # Ensure ordering is DESC by created_at (newest first)
    assert batches[0].template_version == "v2"
    assert batches[1].template_version == "v1"

    # Pretty print for human inspection (use -s to show)
    print("\nEmail batches for job:", job_id)
    for b in batches:
        print(
            f"- id={b.id} | job_id={b.job_id} | template_version={b.template_version} | "
            f"created_at={b.created_at.isoformat()} | page_spec={b.page_spec} | page_count={b.page_count}"
        )

    # If you want to assert against the printed output too:
    captured = capsys.readouterr()
    assert "Email batches for job: JOB_123" in captured.out
    assert "template_version=v2" in captured.out
