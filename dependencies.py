from fastapi import HTTPException, status, Depends
from typing import Annotated
import jwt
from jwt.exceptions import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.orm import Session
from schemas import StatusVar, PriorityVar, SortOrder
from models import UserDB, TaskDB
from config import settings
from auth import oauth2_scheme, get_user
from database import get_db


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> UserDB:

    credentiel_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str | None = payload.get("sub")
        if username is None:
            raise credentiel_exception
    except InvalidTokenError:
        raise credentiel_exception
    user = get_user(username, db)
    if user is None:
        raise credentiel_exception
    return user


def get_user_id(user: Annotated[UserDB, Depends(get_current_user)]) -> int:

    return user.user_id


def find_task_by_id(
    task_id: int,
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[int, Depends(get_user_id)],
) -> TaskDB:
    task = db.scalar(
        select(TaskDB).where(TaskDB.task_id == task_id, TaskDB.user_id == user_id)
    )
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="task not found"
        )
    return task


def filter_tasks(
    db: Annotated[Session, Depends(get_db)],
    user_id: int,
    status: StatusVar | None = None,
    priority: PriorityVar | None = None,
) -> list[TaskDB]:
    stmt = select(TaskDB).where(TaskDB.user_id == user_id)
    if status is not None:
        stmt = stmt.where(TaskDB.status == status)
    if priority is not None:
        stmt = stmt.where(TaskDB.priority == priority)

    return db.scalars(stmt).all()


def order_reverse(order):
    return order == SortOrder.desc
