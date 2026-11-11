from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base

ROLES = ("admin", "editor", "viewer")
STATUSES = ("not_started", "in_progress", "blocked", "done")
PRIORITIES = ("high", "medium", "low")


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(20), default="viewer")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=True)
    # Bumped on password change or deactivation so existing sessions stop working.
    token_version: Mapped[int] = mapped_column(Integer, default=0)
    failed_logins: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Workstream(Base):
    __tablename__ = "workstreams"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(40), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text, default="")
    sort: Mapped[int] = mapped_column(Integer, default=0)


class Phase(Base):
    __tablename__ = "phases"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(40), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    subtitle: Mapped[str] = mapped_column(String(255), default="")
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    sort: Mapped[int] = mapped_column(Integer, default=0)

    criteria: Mapped[list["ExitCriterion"]] = relationship(
        back_populates="phase", order_by="ExitCriterion.sort", cascade="all, delete-orphan"
    )


class ExitCriterion(Base):
    __tablename__ = "exit_criteria"

    id: Mapped[int] = mapped_column(primary_key=True)
    phase_id: Mapped[int] = mapped_column(ForeignKey("phases.id", ondelete="CASCADE"))
    text: Mapped[str] = mapped_column(String(255))
    is_met: Mapped[bool] = mapped_column(Boolean, default=False)
    sort: Mapped[int] = mapped_column(Integer, default=0)

    phase: Mapped[Phase] = relationship(back_populates="criteria")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text, default="")
    phase_id: Mapped[int | None] = mapped_column(ForeignKey("phases.id"), nullable=True, index=True)
    workstream_id: Mapped[int | None] = mapped_column(
        ForeignKey("workstreams.id"), nullable=True, index=True
    )
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="not_started", index=True)
    priority: Mapped[str] = mapped_column(String(10), default="medium")
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    sort: Mapped[int] = mapped_column(Integer, default=0)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    comments: Mapped[list["Comment"]] = relationship(
        back_populates="task", order_by="Comment.created_at", cascade="all, delete-orphan"
    )


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    task: Mapped[Task] = relationship(back_populates="comments")
    user: Mapped[User | None] = relationship()


class AuditLog(Base):
    """Append-only record of logins and every change. Never updated or deleted by the app."""

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    user_email: Mapped[str] = mapped_column(String(255), default="")
    action: Mapped[str] = mapped_column(String(60), index=True)
    entity_type: Mapped[str] = mapped_column(String(40), default="", index=True)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    details: Mapped[str] = mapped_column(Text, default="")
    ip: Mapped[str] = mapped_column(String(64), default="")
