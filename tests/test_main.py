from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from main import app, Base, get_db
import pytest

TEST_DATA_URL = "sqlite://"

test_engine = create_engine(
    TEST_DATA_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(bind=test_engine)

Base.metadata.create_all(test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture
def token():
    response = client.post(
        "/register", json={"username": "ahmed_test", "password": "password123"}
    )
    response = client.post(
        "/token",
        data={"username": "ahmed_test", "password": "password123"},
    )
    return response.json()["access_token"]


def test_health():
    response = client.get("/health")
    assert response.status_code == 200


def test_tasks():
    respnse = client.post("/tasks")
    assert respnse.status_code == 401


def test_registre_user():
    response = client.post(
        "/register", json={"username": "ahmed_test", "password": "password123"}
    )
    assert response.status_code == 201
    assert response.json()["username"] == "ahmed_test"


def test_token_fixture(token):
    assert token is not None


def test_create_task(token):
    response = client.post(
        "/tasks",
        json={
            "title": "Learn pytest",
            "description": "Practice API testing",
            "priority": "high",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    assert response.json()["title"] == "Learn pytest"


def test_get_task_by_id(token):
    create_response = client.post(
        "/tasks",
        json={
            "title": "Learn pytest",
            "description": "Practice API testing",
            "priority": "high",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    task_id = create_response.json()["id"]

    response = client.get(
        f"/tasks/{task_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == task_id
