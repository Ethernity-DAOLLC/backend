import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.base import Base
from app.api.deps import get_db
from app.core.config import settings

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_submit_contact():
    response = client.post(
        f"{settings.API_V1_STR}/contact/",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "subject": "Test Subject",
            "message": "This is a test message with enough characters"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test User"
    assert data["email"] == "test@example.com"
    assert data["is_read"] == False


def test_submit_contact_invalid_email():
    response = client.post(
        f"{settings.API_V1_STR}/contact/",
        json={
            "name": "Test",
            "email": "invalid-email",
            "subject": "Test",
            "message": "Test message"
        }
    )
    assert response.status_code == 422


def test_get_messages_requires_auth():
    response = client.get(f"{settings.API_V1_STR}/contact/messages")
    assert response.status_code == 403 


def test_get_messages_with_auth():
    client.post(
        f"{settings.API_V1_STR}/contact/",
        json={
            "name": "Test",
            "email": "test@example.com",
            "subject": "Test",
            "message": "Test message here"
        }
    )
    response = client.get(
        f"{settings.API_V1_STR}/contact/messages",
        headers={"Authorization": f"Bearer {settings.ADMIN_TOKEN}"}
    )
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_mark_as_read():
    create_response = client.post(
        f"{settings.API_V1_STR}/contact/",
        json={
            "name": "Test",
            "email": "test@example.com",
            "subject": "Test",
            "message": "Test message"
        }
    )
    contact_id = create_response.json()["id"]
    response = client.patch(
        f"{settings.API_V1_STR}/contact/messages/{contact_id}/read",
        json={"is_read": True},
        headers={"Authorization": f"Bearer {settings.ADMIN_TOKEN}"}
    )
    assert response.status_code == 200
    assert response.json()["is_read"] == True


def test_delete_message():
    create_response = client.post(
        f"{settings.API_V1_STR}/contact/",
        json={
            "name": "Test",
            "email": "test@example.com",
            "subject": "Test",
            "message": "Test message"
        }
    )
    contact_id = create_response.json()["id"]
    response = client.delete(
        f"{settings.API_V1_STR}/contact/messages/{contact_id}",
        headers={"Authorization": f"Bearer {settings.ADMIN_TOKEN}"}
    )
    assert response.status_code == 204


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] in ["healthy", "unhealthy"]


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()