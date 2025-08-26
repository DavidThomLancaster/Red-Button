import pytest
from Repositories.ContactRepository import ContactRepository
from shared.ParamsDTO import ParamsDTO
import sqlite3

@pytest.fixture()
def contact_repo():
    # Use a single in-memory connection so schema + data persist for the test
    conn = sqlite3.connect(":memory:")
    repo = ContactRepository(conn=conn)

    # Seed contacts
    conn.executemany(
        "INSERT INTO contacts (id, name, email, phone, service_area) VALUES (?,?,?,?,?)",
        [
            ("c1", "Company1 Plumbing", "c1@example.com", "555-0001", "84601"),
            ("c2", "Company2 Plumbing", "c2@example.com", "555-0002", "84602"),
            ("c3", "ElecCo",             "c3@example.com", "555-0003", "84601"),
            ("c4", "CompanyX Plumbing",  "c4@example.com", "555-0004", "84601"),
        ],
    )
    # Seed trades
    conn.executemany(
        "INSERT INTO contact_trades (contact_id, trade) VALUES (?,?)",
        [
            ("c1", "plumbing"),
            ("c2", "plumbing"),
            ("c3", "electrical"),
            ("c4", "plumbing"),
        ],
    )
    conn.commit()
    return repo

def test_find_contacts_by_parameters_filters(contact_repo):
    # trade + service_area + name LIKE
    params = ParamsDTO(
        trade="PlUmBiNg",      # test case-insensitivity
        name="Company1",       # LIKE match on name
        service_area="84601",
        limit=10,
        page=1,
    )
    rows = contact_repo.find_contacts_by_parameters(params)
    assert isinstance(rows, list)
    assert [r["id"] for r in rows] == ["c1"]  # only c1 matches all three filters

def test_find_contacts_by_parameters_pagination(contact_repo):
    # All plumbing contacts: c1, c2, c4 (order not guaranteed)
    params_page1 = ParamsDTO(trade="plumbing", name=None, service_area=None, limit=1, page=1)
    params_page2 = ParamsDTO(trade="plumbing", name=None, service_area=None, limit=1, page=2)

    page1 = contact_repo.find_contacts_by_parameters(params_page1)
    page2 = contact_repo.find_contacts_by_parameters(params_page2)

    # Ensure 1 item per page and no overlap
    assert len(page1) == 1
    assert len(page2) == 1
    assert page1[0]["id"] != page2[0]["id"]

def test_find_contacts_by_parameters_no_filters_returns_limited(contact_repo):
    # No filters: should return up to 'limit' contacts
    params = ParamsDTO(trade=None, name=None, service_area=None, limit=2, page=1)
    rows = contact_repo.find_contacts_by_parameters(params)
    assert len(rows) == 2
    # Sanity check: rows contain expected keys
    for r in rows:
        assert {"id", "name", "email", "phone", "service_area"}.issubset(r.keys())
