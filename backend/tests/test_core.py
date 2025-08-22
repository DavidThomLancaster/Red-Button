import tempfile
import shutil
import json
from pathlib import Path
from Core.core import Core
from FileManager.FileManager import FileManager
from shared.StorageRef import StorageRef, StorageMode
from Services.SchemaService import SchemaService
from Services.ContactService import ContactService
from Repositories.ContactRepository import ContactRepository
from Repositories.EmailRepository import EmailRepository
import pytest
import sqlite3


# ------------------------ FIXTURES ------------------------

@pytest.fixture()
def temp_dir():
    path = Path(tempfile.mkdtemp())
    yield path
    shutil.rmtree(path)

@pytest.fixture()
def file_manager(temp_dir):
    return FileManager(mode=StorageMode.LOCAL, base_dir=temp_dir)

@pytest.fixture()
def contact_repo():
    return ContactRepository(":memory:")

@pytest.fixture()
def email_repo():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return EmailRepository(conn=conn)

@pytest.fixture()
def contact_service(contact_repo):
    return ContactService(contact_repo)

@pytest.fixture()
def core(file_manager, contact_service):
    return Core(file_manager=file_manager, contact_service=contact_service)

@pytest.fixture()
def schema_service():
    return SchemaService()

# ----------------------- COMBINING CSVs TO JSON ----------------------
def test_combine_csvs_to_json(core, file_manager, temp_dir):
    # get two CSV files
    asset_dir = Path("tests/assets/combine/test1")
    csv_dir = temp_dir / "storage/user_1/job_1/csvs"
    csv_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy(asset_dir / "csv1.csv", csv_dir / "batch1.csv")
    shutil.copy(asset_dir / "csv2.csv", csv_dir / "batch2.csv")
    shutil.copy(asset_dir / "csv3.csv", csv_dir / "batch3.csv")

    # make a StorageRef for that file
    csv_ref = StorageRef(location=str(csv_dir.relative_to(temp_dir)), mode=StorageMode.LOCAL)

    combined_json_ref = core.combine_to_json("user_1", "job_1", csv_ref)

    results = file_manager.get_combined_json(combined_json_ref)
    parsed_results = json.loads(results)

    with open(asset_dir / "expected.json", "r", encoding="utf-8") as f:
        expected_results = json.load(f)

    debug_path = Path("tests/assets/combine/test1/debug/combined.json")
    debug_path.parent.mkdir(parents=True, exist_ok=True)
    debug_path.write_text(results, encoding="utf-8")
    print(f"Written debug file to: {debug_path}")

    #assert set(parsed_results.keys()).issuperset(expected_results.keys())
    assert parsed_results == expected_results
    #assert normalize_json(parsed_results) == normalize_json(expected_results)

# ------------------------- NORMALIZING JSON ------------------------
def test_normalize_json(core, file_manager, temp_dir, schema_service):
    # get the combined_json as a ref. 
    asset_dir = Path("tests/assets/normalize/test1")
    json_dir = temp_dir / "storage/user_1/job_1/json"
    json_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy(asset_dir / "combined.json", json_dir / "combined.json")
    json_ref = StorageRef(location=str(json_dir.relative_to(temp_dir)), mode=StorageMode.LOCAL)

    schema_text, _ = schema_service.get_active_schema()

    normalized_ref = core.normalize_json("user_1", "job_1", json_ref, schema_text)

    results = file_manager.get_normalized_json(normalized_ref)
    parsed_results = json.loads(results)

    with open(asset_dir / "expected.json", "r", encoding="utf-8") as f:
        expected_results = json.load(f)

    debug_path = Path("tests/assets/normalize/test1/debug/normalized.json")
    debug_path.parent.mkdir(parents=True, exist_ok=True)
    debug_path.write_text(results, encoding="utf-8")
    print(f"Written debug file to: {debug_path}")

    assert parsed_results == expected_results

# ----------------------- CREATING MAP -----------------------------
def test_create_map(core, file_manager, temp_dir):
    asset_dir = Path("tests/assets/mapping/test1")
    json_dir = temp_dir / "storage/user_1/job_1/json"
    json_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy(asset_dir / "normalized.json", json_dir / "normalized.json")
    json_ref = StorageRef(location=str(json_dir.relative_to(temp_dir)), mode=StorageMode.LOCAL)

    mapped_ref = core.map_contacts(json_ref)

    results = file_manager.load_json(mapped_ref)
    parsed_results = results # json.loads(results)

    with open(asset_dir / "expected.json", "r", encoding="utf-8") as f:
        expected_results = json.load(f)

    debug_path = Path("tests/assets/mapping/test1/debug/normalized.json")
    debug_path.parent.mkdir(parents=True, exist_ok=True)
    debug_path.write_text(str(results), encoding="utf-8")
    print(f"Written debug file to: {debug_path}")

    assert parsed_results == expected_results


def test_generate_emails(core, email_repo, file_manager, contact_repo, temp_dir):
    # 1) Seed contacts DB
    contact_repo.conn.execute(
        "INSERT INTO contacts (id, name, email, phone, service_area) VALUES (?,?,?,?,?)",
        ("c1", "Alice Plumber", "alice@example.com", "555-1111", "Denver"),
    )
    contact_repo.conn.execute(
        "INSERT INTO contacts (id, name, email, phone, service_area) VALUES (?,?,?,?,?)",
        ("c2", "Bob Plumber", "bob@example.com", "555-2222", "Denver"),
    )
    contact_repo.conn.execute(
        "INSERT INTO contact_trades (contact_id, trade) VALUES (?,?)", ("c1", "Plumbing")
    )
    contact_repo.conn.execute(
        "INSERT INTO contact_trades (contact_id, trade) VALUES (?,?)", ("c2", "Plumbing")
    )
    contact_repo.conn.commit()

    # 2) Prepare a contacts_map file
    contacts_map = {
        "Plumbing": [
            {
                "note": "Involves multiple pipe installations such as suction and discharge lines",
                "pages": ["7"],
                "contacts": ["c1", "c2"],  # explicitly mapped for deterministic test
            }
        ],
        "metadata": {
            "processing_steps": ["normalized", "contacts_mapped"],
            "job": {"user_id": "user_1", "job_id": "job_1"},
        },
    }

    json_dir = temp_dir / "storage/user_1/job_1/json"
    json_dir.mkdir(parents=True, exist_ok=True)
    (json_dir / "normalized.json").write_text(json.dumps(contacts_map), encoding="utf-8")

    # StorageRef pointing to the *folder*; FileManager will pick normalized.json inside
    contacts_map_ref = StorageRef(
        location=str(json_dir.relative_to(temp_dir)),
        mode=StorageMode.LOCAL,
    )

    # 3) Template
    template = file_manager.get_email_template("v1")

    # 4) Call core.generate_emails
    out = core.generate_emails(
        job_id="job_1",
        template=template,
        email_repo=email_repo,
        contacts_map_ref=contacts_map_ref,
        auto_fill_when_missing=False,   # we explicitly set contacts above
    )

    # 5) Assertions on result and DB side-effects
    assert "batch_id" in out and out["batch_id"]
    assert out["count"] == 2  # two contacts mapped above

    # Verify rows landed in email_queue
    cur = email_repo.conn.cursor()
    cur.execute(
        "SELECT job_id, batch_id, contact_id, to_email, subject, body, status FROM email_queue WHERE batch_id = ? ORDER BY to_email",
        (out["batch_id"],),
    )
    rows = cur.fetchall()
    assert len(rows) == 2

    # Light content checks
    subjects = [r["subject"] for r in rows]
    bodies = [r["body"] for r in rows]
    assert all("Plumbing" in s for s in subjects)
    assert any("pages 7" in b or "pages: 7" in b or "pages 7." in b for b in bodies)
    assert any("Alice" in b for b in bodies)
    assert any("Bob" in b for b in bodies)

    # Status should be draft
    assert set(r["status"] for r in rows) == {"draft"}





# ---------------------------- HELPERS --------------------------
# def normalize_json(obj):
#     if isinstance(obj, dict):
#         return {k: normalize_json(v) for k, v in sorted(obj.items())}
#     elif isinstance(obj, list):
#         return sorted((normalize_json(i) for i in obj), key=lambda x: json.dumps(x, sort_keys=True))
#     else:
#         return obj


