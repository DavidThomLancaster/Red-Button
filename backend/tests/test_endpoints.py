# import pytest
# from fastapi.testclient import TestClient
# from main import app
# from Repositories.UserRepository import UserRepository
# from Repositories.JobRepository import JobRepository

# from router import handlers  # wherever get_user_repo/get_job_repo live

import pytest
from fastapi.testclient import TestClient
from main import app
from router import handlers

from Services.UserService import UserService
from Services.JobService import JobService
from Services.PromptService import PromptService
from Repositories.UserRepository import UserRepository
from Repositories.JobRepository import JobRepository
from Repositories.PromptRepository import PromptRepository
from FileManager.FileManager import FileManager
from Core.core import Core
import shutil

# @pytest.fixture(autouse=True)
# def override_repos():
#     user_repo = UserRepository(":memory:")
#     job_repo = JobRepository(":memory:")

#     app.dependency_overrides[handlers.get_user_repo] = lambda: user_repo
#     app.dependency_overrides[handlers.get_job_repo] = lambda: job_repo

#     yield # this does the teardown stuff
#     app.dependency_overrides.clear()



@pytest.fixture(autouse=True)
def override_services(tmp_path):
    user_repo = UserRepository(":memory:")
    job_repo = JobRepository(":memory:")
    prompt_repo = PromptRepository(":memory:")
    file_manager = FileManager(tmp_path)  # use pytest tmp_path

    prompt_service = PromptService(prompt_repo)
    user_service = UserService(user_repo)
    core = Core(file_manager)

    job_service = JobService(job_repo, file_manager, core, prompt_service)

    app.dependency_overrides[handlers.get_user_service] = lambda: user_service
    app.dependency_overrides[handlers.get_job_service] = lambda: job_service

    yield
    app.dependency_overrides.clear()
    shutil.rmtree(tmp_path, ignore_errors=True)




client = TestClient(app)


def test_register_success():
    r = client.post("/register", json={"email": "alice3@example.com", "password": "secret"})
    assert r.status_code == 200
    body = r.json()
    assert "user_id" in body
    assert body["message"] == "User created successfully"


def test_register_duplicate_email():
    email = "bob2@example.com"
    password = "secret"

    r1 = client.post("/register", json={"email": email, "password": password})
    assert r1.status_code == 200

    r2 = client.post("/register", json={"email": email, "password": password})
    assert r2.status_code in (400, 409, 422)


def test_register_missing_password():
    r = client.post("/register", json={"email": "charli2@example.com"})
    assert r.status_code == 422


def test_login_success():
    email = "diana2@example.com"
    password = "secret"

    client.post("/register", json={"email": email, "password": password})
    r2 = client.post("/login", json={"email": email, "password": password})
    assert r2.status_code == 200
    body = r2.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_wrong_password():
    email = "eve2@example.com"
    password = "secret"

    client.post("/register", json={"email": email, "password": password})
    r = client.post("/login", json={"email": email, "password": "wrongpass"})
    assert r.status_code in (401, 500)


def test_create_and_get_job():
    email = "frank23@example.com"
    password = "secret"

    client.post("/register", json={"email": email, "password": password})
    r = client.post("/login", json={"email": email, "password": password})
    token = r.json()["access_token"]

    r2 = client.post(
        "/create_job",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Test Job", "notes": "Check DB"}
    )
    assert r2.status_code == 200
    job_id = r2.json()["job_id"]

    r3 = client.get("/get_job", headers={"Authorization": f"Bearer {token}"})
    assert r3.status_code == 200
    jobs = r3.json()["jobs"]
    assert any(job["job_id"] == job_id for job in jobs)
