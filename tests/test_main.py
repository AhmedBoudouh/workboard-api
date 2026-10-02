### Required tests ###
# health
#     ✓ health returns 200

# auth/register
#     ✓ register user
#     ✓ duplicate username → 409
#     ✓ invalid username/password validation

# auth/token
#     ✓ valid login
#     ✓ wrong password → 401
#     ✓ wrong username → 401

# tasks authentication
#     ✓ GET /tasks without token → 401
#     ✓ POST /tasks without token → 401

# create task
#     ✓ create valid task
#     ✓ defaults are correct
#     ✓ invalid title → 422

# read tasks
#     ✓ list own tasks
#     ✓ get task by id
#     ✓ missing task → 404

# update
#     ✓ partial update
#     ✓ missing task → 404

# delete
#     ✓ delete own task
#     ✓ deleted task → 404

# ownership
#     ✓ user A cannot GET user B task

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app
from database import get_db, Base
import pytest
from config import settings

test_engine = create_engine(settings.TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(bind=test_engine)
client = TestClient(app)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture()
def clean_db():

    Base.metadata.drop_all(test_engine)

    Base.metadata.create_all(test_engine)
    yield
    Base.metadata.drop_all(test_engine)


@pytest.fixture()
def token(clean_db):
    response = client.post(
        "/register", json={"username": "user_test1", "password": "password123"}
    )

    response = client.post(
        "/token", data={"username": "user_test1", "password": "password123"}
    )

    return response.json()["access_token"]


@pytest.fixture()
def token2(clean_db):
    response = client.post(
        "/register", json={"username": "user_test2", "password": "password123"}
    )

    response = client.post(
        "/token", data={"username": "user_test2", "password": "password123"}
    )

    return response.json()["access_token"]


@pytest.fixture()
def get_id_task(token):
    response = client.post(
        "/tasks",
        json={
            "title": "Learn python",
            "description": "learn backend",
            "priority": "low",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    return response.json()["task_id"]


def test_health():
    response = client.get("/health")

    assert response.status_code == 200


def test_register(clean_db):
    response = client.post(
        "/register", json={"username": "user_test1", "password": "password123"}
    )
    assert response.status_code == 201
    assert response.json() == {"username": "user_test1"}


def test_duplicat_register(clean_db):
    response1 = client.post(
        "/register", json={"username": "user_test1", "password": "password123"}
    )
    assert response1.status_code == 201
    response2 = client.post(
        "/register", json={"username": "user_test1", "password": "password123"}
    )
    assert response2.status_code == 409
    assert response2.json()["detail"] == "username already registered"


def test_invalid_username(clean_db):
    response = client.post(
        "/register", json={"username": "a", "password": "password123"}
    )
    assert response.status_code == 422


def test_invalid_password(clean_db):
    response = client.post(
        "/register", json={"username": "user_test", "password": "1234567"}
    )
    assert response.status_code == 422


def test_token(token):
    assert token is not None


def test_wrong_wp(clean_db):
    response = client.post(
        "/register", json={"username": "user_test1", "password": "password123"}
    )

    response = client.post(
        "/token", data={"username": "user_test1", "password": "password12"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "password or username are incorrect"


def test_wrong_username(clean_db):
    response = client.post(
        "/register", json={"username": "user_test1", "password": "password123"}
    )

    response = client.post(
        "/token", data={"username": "user", "password": "password123"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "password or username are incorrect"


def test_get_tasks_without_token():
    response = client.get("/tasks")
    assert response.status_code == 401


def test_post_tasks_without_token():
    response = client.post(
        "/tasks",
        json={
            "title": "Learn python",
            "description": "learn backend",
            "priority": "low",
        },
    )
    assert response.status_code == 401


def test_create_task(token):
    response = client.post(
        "/tasks",
        json={
            "title": "Learn python",
            "description": "learn backend",
            "priority": "low",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    assert response.json()["title"] == "Learn python"
    assert response.json()["description"] == "learn backend"
    assert response.json()["priority"] == "low"
    assert response.json()["status"] == "todo"


def test_create_task_default_values(token):
    response = client.post(
        "/tasks",
        json={
            "title": "Learn python",
            "description": "learn backend",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.json()["status"] == "todo"
    assert response.json()["priority"] == "medium"


def test_create_task_invalide_title(token):
    response = client.post(
        "/tasks",
        json={
            "title": "L",
            "description": "learn backend",
            "priority": "low",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422


def test_get_tasks(token):
    response1 = client.post(
        "/tasks",
        json={
            "title": "Learn python",
            "description": "learn backend",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    response2 = client.post(
        "/tasks",
        json={
            "title": "Learn Java",
            "description": "learn front-end",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    response = client.get(
        "/tasks",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["total"] == 2


def test_get_task_by_id(get_id_task, token):
    response = client.get(
        f"/tasks/{get_id_task}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.json()["title"] == "Learn python"


def test_missing_task(token):
    task_id = 1
    response = client.get(
        f"/tasks/{task_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "task not found"


def test_patch_task(get_id_task, token):
    response = client.patch(
        f"/tasks/{get_id_task}",
        json={
            "title": "Learn Java",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.json()["title"] == "Learn Java"
    assert response.json()["description"] == "learn backend"
    assert response.json()["priority"] == "low"


def test_patch_missing_task(token):
    task_id = 1
    response = client.patch(
        f"/tasks/{task_id}",
        json={
            "title": "Learn Java",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "task not found"


def test_delete_task(get_id_task, token):
    response = client.delete(
        f"/tasks/{get_id_task}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 204


def test_delete_missing_task(token):
    task_id = 1
    response = client.delete(
        f"/tasks/{task_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "task not found"


def test_get_task_by_wrong_user(get_id_task, token2):
    response = client.get(
        f"/tasks/{get_id_task}",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "task not found"


def test_patch_task_wrong_user(get_id_task, token2):
    response = client.patch(
        f"/tasks/{get_id_task}",
        json={
            "title": "Learn Java",
        },
        headers={"Authorization": f"Bearer {token2}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "task not found"


def test_delete_task_wrong_user(get_id_task, token2):
    response = client.delete(
        f"/tasks/{get_id_task}",
        headers={"Authorization": f"Bearer {token2}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "task not found"
