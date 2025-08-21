import os
import json
from pathlib import Path
import tempfile
import shutil
import sys

import pytest
from FileManager.FileManager import FileManager
from Core.core import Core
from shared.StorageRef import StorageRef, StorageMode




def test_combine_to_json_creates_json():
    #Setup a temporary directory for fake CSVs
    temp_dir = Path(tempfile.mkdtemp())
    csv_dir = temp_dir / "csvs"
    csv_dir.mkdir(parents=True)

    # Create fake CSVs
    csv1 = csv_dir / "batch1.csv"
    csv2 = csv_dir / "batch2.csv"
    with open(csv1, "w", encoding="utf-8") as f:
        f.write("trade,pages,note\nElectrical,1,Install lights\nPlumbing,2,Install sink\n")
    with open(csv2, "w", encoding="utf-8") as f:
        f.write("trade,pages,note\nElectrical,3,Add outlets\n")

    # Init FileManager + Core
    fm = FileManager(mode=StorageMode.LOCAL, base_dir=temp_dir)
    core = Core(file_manager=fm)

    # Create a fake StorageRef pointing to CSV dir
    csvs_ref = StorageRef(location=str(csv_dir.relative_to(temp_dir)), mode=StorageMode.LOCAL)

    # Run combine_to_json
    json_ref = core.combine_to_json("user1", "job1", csvs_ref)

    # Assert JSON file exists and contains expected data
    json_file_path = Path(fm.base_dir) / json_ref.location / "combined.json"
    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    print("\n\n\n" + json.dumps(data, indent=2) + "\n\n\n")

    assert "Electrical" in data
    assert "Plumbing" in data
    assert data["Electrical"][0]["note"] == "Install lights"

    # Cleanup temp directory
    shutil.rmtree(temp_dir)
    # #pass

def test_hello_world():
    print ("\n\n\nhi!\n\n\n")
    assert 1 == 1


