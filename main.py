# WorkBoard API project
# WB-001: Creating and viewing tasks
# WB-002 — Update and Delete Tasks
# WB-003: Task Filtering
# WB-004: Task Sorting and Pagination
# WB-005 Dependency Injection
# WB-006 — Authentication with OAuth2 and JWT

import math

from fastapi import FastAPI, HTTPException, status, Query, Depends
from pydantic import BaseModel, Field
from enum import Enum
import itertools
from datetime import UTC, datetime, timezone, timedelta
from typing import Annotated
from pwdlib import PasswordHash
import jwt
from jwt.exceptions import InvalidTokenError
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

app = FastAPI()
tasks_db = []
SECRET_KEY = "my-super-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

users_db = {}

_id_counter = itertools.count(1)


def next_id() -> int:
    return next(_id_counter)


class StatusVar(str, Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"


class PriorityVar(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class TaskFieldSort(str, Enum):
    id = "id"
    status = "status"
    created_at = "created_at"
    title = "title"
    priority = "priority"


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


class TasksIn(BaseModel):
    title: str = Field(min_length=3, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    priority: PriorityVar = Field(default=PriorityVar.medium)


class TasksOut(TasksIn):
    id: int
    status: StatusVar = Field(default=StatusVar.todo)
    created_at: datetime


class UpdateData(BaseModel):

    title: str | None = Field(default=None, min_length=3, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    priority: PriorityVar | None = None
    status: StatusVar | None = None


class PageSortTask(BaseModel):
    items: list[TasksOut]
    page: int
    page_size: int
    total: int
    total_pages: int


class Token(BaseModel):
    access_token: str
    token_type: str


class User(BaseModel):
    username: str


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    username: str


def find_task_by_id(task_id: int) -> TasksOut | None:
    for task in tasks_db:
        if task.id == task_id:

            return task
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task not found")


def filter_tasks(status: StatusVar | None = None, priority: PriorityVar | None = None):
    result = []
    if not status and not priority:
        result = tasks_db
    for item in tasks_db:
        if item.status == status and priority is None:
            result.append(item)
        if item.priority == priority and status is None:
            result.append(item)
        if item.status == status and item.priority == priority:
            result.append(item)

    return result


def order_reverse(order):
    return order == SortOrder.desc


def get_user(username):
    user = users_db.get(username)
    return user


def authenticate_user(username, password):
    user = get_user(username)
    if not user:
        return None
    correct_password = password_hash.verify(password, user["hashed_password"])
    if not correct_password:
        return None

    return user


def create_token(username):
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": username, "exp": expire}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return token


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):

    credentiel_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if not payload:
            raise credentiel_exception
        username = payload.get("sub")
        if username is None:
            raise credentiel_exception
    except InvalidTokenError:
        raise credentiel_exception
    user = get_user(username)
    if user is None:
        raise credentiel_exception
    return User(username=user["username"])


@app.get("/health", status_code=status.HTTP_200_OK)
async def get_health():
    return {"status": "ok"}


@app.post("/tasks", status_code=201)
async def create_tasks(
    current_user: Annotated[User, Depends(get_current_user)], task_in: TasksIn
) -> TasksOut:
    task = TasksOut(
        **task_in.model_dump(),
        id=next_id(),
        created_at=datetime.now(timezone.utc),
        status="todo"
    )
    tasks_db.append(task)
    return task


@app.get("/tasks")
async def get_tasks(
    current_user: Annotated[User, Depends(get_current_user)],
    status: StatusVar | None = None,
    priority: PriorityVar | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    sort_by: TaskFieldSort = Query(TaskFieldSort.id),
    order: SortOrder = Query(SortOrder.asc),
) -> PageSortTask:

    filtered_tasks = filter_tasks(status, priority)
    priority_rank = {"low": 1, "medium": 2, "high": 3}
    status_rank = {"todo": 1, "in_progress": 2, "done": 3}

    if sort_by == TaskFieldSort.priority:

        sorted_tasks = sorted(
            filtered_tasks,
            key=lambda task: priority_rank[getattr(task, sort_by.value)],
            reverse=order_reverse(order),
        )

    elif sort_by == TaskFieldSort.status:
        sorted_tasks = sorted(
            filtered_tasks,
            key=lambda task: status_rank[getattr(task, sort_by.value)],
            reverse=order_reverse(order),
        )

    else:
        sorted_tasks = sorted(
            filtered_tasks,
            key=lambda task: getattr(task, sort_by.value),
            reverse=order_reverse(order),
        )

    total = len(sorted_tasks)
    total_pages = math.ceil(total / page_size)

    start = (page - 1) * page_size
    end = page * page_size

    result = sorted_tasks[start:end]
    return {
        "items": result,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
    }


@app.get("/tasks/{task_id}", status_code=status.HTTP_200_OK)
async def get_tasks_by_id(
    current_user: Annotated[User, Depends(get_current_user)],
    task: Annotated[TasksOut, Depends(find_task_by_id)],
):

    return task


@app.patch("/tasks/{task_id}", status_code=status.HTTP_200_OK)
async def update_tasks(
    task: Annotated[TasksOut, Depends(find_task_by_id)],
    data: UpdateData,
    current_user: Annotated[User, Depends(get_current_user)],
):
    stored_data = task.model_dump()
    updated_data = data.model_dump(exclude_unset=True)

    for key in updated_data:
        if updated_data[key] != stored_data[key]:
            setattr(task, key, updated_data[key])
    return task


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    current_user: Annotated[User, Depends(get_current_user)],
    task: Annotated[TasksOut, Depends(find_task_by_id)],
):
    tasks_db.remove(task)


@app.post("/token", response_model=Token)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):

    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=("password or username are incorrect"),
        )

    access_token = create_token(user["username"])
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/register", status_code=status.HTTP_201_CREATED)
async def registre(form_data: UserCreate) -> UserOut:
    user = get_user(form_data.username)
    if user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="username already registered"
        )
    users_db[form_data.username] = {
        "username": form_data.username,
        "hashed_password": password_hash.hash(form_data.password),
    }

    return {"username": form_data.username}
