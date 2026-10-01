import math
from fastapi import status, Query, Depends, APIRouter

from enum import Enum
from datetime import datetime, timezone
from typing import Annotated
from database import Session, get_db
from dependencies import get_current_user, get_user_id
from models import TaskDB, UserDB
from schemas import (
    TasksIn,
    TasksOut,
    StatusVar,
    PriorityVar,
    TaskFieldSort,
    SortOrder,
    PageSortTask,
    UpdateData,
)
from dependencies import filter_tasks, order_reverse, find_task_by_id

router = APIRouter()


@router.post("/tasks", status_code=201)
async def create_tasks(
    current_user: Annotated[str, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[int, Depends(get_user_id)],
    task_in: TasksIn,
) -> TasksOut:
    task = TaskDB(
        **task_in.model_dump(),
        status=StatusVar.todo,
        created_at=datetime.now(timezone.utc),
        user_id=user_id
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/tasks")
async def get_tasks(
    current_user: Annotated[str, Depends(get_current_user)],
    user_id: Annotated[int, Depends(get_user_id)],
    db: Annotated[Session, Depends(get_db)],
    status: StatusVar | None = None,
    priority: PriorityVar | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    sort_by: TaskFieldSort = Query(TaskFieldSort.user_id),
    order: SortOrder = Query(SortOrder.asc),
) -> PageSortTask:

    filtered_tasks = filter_tasks(db, user_id, status, priority)
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


@router.get("/tasks/{task_id}", status_code=status.HTTP_200_OK)
async def get_tasks_by_id(
    current_user: Annotated[str, Depends(get_current_user)],
    task: Annotated[TaskDB, Depends(find_task_by_id)],
) -> TasksOut:

    return task


@router.patch("/tasks/{task_id}", status_code=status.HTTP_200_OK)
async def update_tasks(
    task: Annotated[TaskDB, Depends(find_task_by_id)],
    data: UpdateData,
    current_user: Annotated[str, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> TasksOut:
    update = data.model_dump(exclude_unset=True)
    for key, value in update.items():
        setattr(task, key, value)

    db.commit()
    db.refresh(task)
    return task


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    current_user: Annotated[UserDB, Depends(get_current_user)],
    task: Annotated[TaskDB, Depends(find_task_by_id)],
    db: Annotated[Session, Depends(get_db)],
):
    db.delete(task)
    db.commit()
