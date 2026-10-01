from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
from datetime import datetime


class StatusVar(str, Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"


class PriorityVar(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class TaskFieldSort(str, Enum):
    user_id = "user_id"
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
    task_id: int
    status: StatusVar = Field(default=StatusVar.todo)
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
    user_id: int
    model_config = ConfigDict(from_attributes=True)


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
    model_config = ConfigDict(from_attributes=True)
