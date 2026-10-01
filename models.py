from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from database import Base
from datetime import datetime
from schemas import StatusVar, PriorityVar


class UserDB(Base):

    __tablename__ = "users"
    user_id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(nullable=False)
    tasks: Mapped[list["TaskDB"]] = relationship(back_populates="user")


class TaskDB(Base):
    __tablename__ = "tasks"
    task_id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str | None] = mapped_column(nullable=True)
    priority: Mapped[PriorityVar] = mapped_column(nullable=False)
    status: Mapped[StatusVar] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    user: Mapped[UserDB] = relationship(back_populates="tasks")
