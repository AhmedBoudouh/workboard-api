# WorkBoard API project
# Requirement WB-001: Creating and viewing tasks

import math

from fastapi import FastAPI, HTTPException, status, Query
from pydantic import BaseModel, Field
from enum import Enum
import itertools
from datetime import UTC, datetime, timezone
from typing import Annotated

app = FastAPI()
tasks_db = []

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

    title: str = Field(default=None, min_length=3, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    priority: PriorityVar | None = None
    status: StatusVar | None = None


class PageSortTask(BaseModel):
    items: list[TasksOut]
    page: int
    page_size: int
    total: int
    total_pages: int


def find_task_by_id(task_id) -> TasksOut | None:
    for task in tasks_db:
        if task.id == task_id:
            return task


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


@app.get("/health", status_code=status.HTTP_200_OK)
async def get_health():
    return {"status": "ok"}


@app.post("/tasks", status_code=201)
async def create_tasks(task_in: TasksIn) -> TasksOut:
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
async def get_tasks_by_id(task_id: int):
    task = find_task_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="task not found"
        )
    return task


##WB-002 — Update and Delete Tasks
@app.patch("/tasks/{task_id}", status_code=status.HTTP_200_OK)
async def update_tasks(task_id: int, data: UpdateData):
    task = find_task_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="task not found"
        )

    stored_data = task.model_dump()
    updated_data = data.model_dump(exclude_unset=True)

    for key in updated_data:
        if updated_data[key] != stored_data[key]:
            setattr(task, key, updated_data[key])
    return task


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int):
    task = find_task_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    tasks_db.remove(task)
