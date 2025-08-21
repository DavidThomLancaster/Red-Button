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
import pytest


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

    results = file_manager.get_normalized_json(mapped_ref)
    parsed_results = json.loads(results)

    with open(asset_dir / "expected.json", "r", encoding="utf-8") as f:
        expected_results = json.load(f)

    debug_path = Path("tests/assets/mapping/test1/debug/normalized.json")
    debug_path.parent.mkdir(parents=True, exist_ok=True)
    debug_path.write_text(results, encoding="utf-8")
    print(f"Written debug file to: {debug_path}")

    assert parsed_results == expected_results



# ---------------------------- HELPERS --------------------------
# def normalize_json(obj):
#     if isinstance(obj, dict):
#         return {k: normalize_json(v) for k, v in sorted(obj.items())}
#     elif isinstance(obj, list):
#         return sorted((normalize_json(i) for i in obj), key=lambda x: json.dumps(x, sort_keys=True))
#     else:
#         return obj


