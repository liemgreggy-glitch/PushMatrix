"""Tests for the accounts API."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database.connection import Base, get_db
from main import app

# Import all models so that Base.metadata contains all tables (including proxies, etc.)
import models.account  # noqa: F401
import models.proxy  # noqa: F401
import models.task  # noqa: F401
import models.message_log  # noqa: F401
import models.statistics  # noqa: F401

# Use a single in-memory SQLite database shared across all connections
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test and drop them after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client(setup_database):
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ==================== GET /api/accounts/ ====================

def test_get_accounts_empty(client):
    """Empty database returns empty list."""
    response = client.get("/api/accounts/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_get_accounts_with_pagination(client):
    """Pagination parameters are respected."""
    # Create two accounts first
    client.post("/api/accounts/", json={"phone": "+10000000001"})
    client.post("/api/accounts/", json={"phone": "+10000000002"})

    response = client.get("/api/accounts/?skip=0&limit=1")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 1


def test_get_accounts_search(client):
    """Search by phone number works."""
    client.post("/api/accounts/", json={"phone": "+1999888777", "username": "alice"})
    client.post("/api/accounts/", json={"phone": "+1111111111", "username": "bob"})

    response = client.get("/api/accounts/?search=alice")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["username"] == "alice"


def test_get_accounts_status_filter(client):
    """Status filter works."""
    client.post("/api/accounts/", json={"phone": "+10000000001"})
    response = client.get("/api/accounts/?status=offline")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1

    response2 = client.get("/api/accounts/?status=online")
    assert response2.status_code == 200
    assert response2.json()["total"] == 0


# ==================== POST /api/accounts/ ====================

def test_create_account(client):
    """Creating an account returns the new account data."""
    response = client.post(
        "/api/accounts/",
        json={"phone": "+1234567890", "username": "testuser", "first_name": "Test"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["phone"] == "+1234567890"
    assert data["username"] == "testuser"
    assert "id" in data


def test_create_account_duplicate_phone(client):
    """Duplicate phone returns 400."""
    client.post("/api/accounts/", json={"phone": "+1234567890"})
    response = client.post("/api/accounts/", json={"phone": "+1234567890"})
    assert response.status_code == 400


# ==================== GET /api/accounts/{id} ====================

def test_get_account(client):
    """Get a single account by ID."""
    created = client.post("/api/accounts/", json={"phone": "+1234567890"}).json()
    response = client.get(f"/api/accounts/{created['id']}")
    assert response.status_code == 200
    assert response.json()["phone"] == "+1234567890"


def test_get_account_not_found(client):
    """Non-existent account returns 404."""
    response = client.get("/api/accounts/9999")
    assert response.status_code == 404


# ==================== PUT /api/accounts/{id} ====================

def test_update_account(client):
    """Updating an account changes the specified fields."""
    created = client.post(
        "/api/accounts/", json={"phone": "+1234567890"}
    ).json()
    response = client.put(
        f"/api/accounts/{created['id']}",
        json={"username": "newname", "tags": ["vip"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "newname"
    assert "vip" in data["tags"]


# ==================== DELETE /api/accounts/{id} ====================

def test_delete_account(client):
    """Deleting an account removes it from the database."""
    created = client.post("/api/accounts/", json={"phone": "+1234567890"}).json()
    response = client.delete(f"/api/accounts/{created['id']}")
    assert response.status_code == 200
    assert response.json()["success"] is True

    # Confirm it is gone
    get_response = client.get(f"/api/accounts/{created['id']}")
    assert get_response.status_code == 404


# ==================== POST /api/accounts/import/session ====================

def test_import_session(client):
    """Importing a session string creates an account."""
    response = client.post(
        "/api/accounts/import/session",
        json={"session_string": "test_session_string", "phone": "+9876543210"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["account"]["phone"] == "+9876543210"


def test_import_session_duplicate(client):
    """Importing a duplicate phone returns success=False."""
    client.post(
        "/api/accounts/import/session",
        json={"session_string": "session1", "phone": "+9876543210"},
    )
    response = client.post(
        "/api/accounts/import/session",
        json={"session_string": "session2", "phone": "+9876543210"},
    )
    assert response.status_code == 200
    assert response.json()["success"] is False


# ==================== POST /api/accounts/bulk-action ====================

def test_bulk_action_delete(client):
    """Bulk delete removes all specified accounts."""
    a1 = client.post("/api/accounts/", json={"phone": "+1111111111"}).json()
    a2 = client.post("/api/accounts/", json={"phone": "+2222222222"}).json()

    response = client.post(
        "/api/accounts/bulk-action",
        json={"action_type": "delete", "account_ids": [a1["id"], a2["id"]]},
    )
    assert response.status_code == 200
    assert response.json()["success"] == 2

    assert client.get("/api/accounts/").json()["total"] == 0


def test_bulk_action_activate(client):
    """Bulk activate sets status to online."""
    acc = client.post("/api/accounts/", json={"phone": "+1111111111"}).json()
    client.post(
        "/api/accounts/bulk-action",
        json={"action_type": "activate", "account_ids": [acc["id"]]},
    )
    updated = client.get(f"/api/accounts/{acc['id']}").json()
    assert updated["status"] == "online"


# ==================== GET /api/accounts/export ====================

def test_export_json(client):
    """Export returns JSON data."""
    client.post("/api/accounts/", json={"phone": "+1234567890"})
    response = client.get("/api/accounts/export?format=json")
    assert response.status_code == 200
    data = response.json()
    assert data["format"] == "json"
    assert data["count"] == 1


def test_export_csv(client):
    """Export returns CSV data."""
    client.post("/api/accounts/", json={"phone": "+1234567890"})
    response = client.get("/api/accounts/export?format=csv")
    assert response.status_code == 200
    assert response.json()["format"] == "csv"
