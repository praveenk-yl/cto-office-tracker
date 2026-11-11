from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

Role = Literal["admin", "editor", "viewer"]
Status = Literal["not_started", "in_progress", "blocked", "done"]
Priority = Literal["high", "medium", "low"]


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---- auth / users ----
class LoginIn(BaseModel):
    email: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=200)


class ChangePasswordIn(BaseModel):
    current_password: str = Field(max_length=200)
    new_password: str = Field(max_length=200)


class UserOut(ORM):
    id: int
    email: str
    name: str
    role: Role
    is_active: bool
    must_change_password: bool
    last_login_at: datetime | None
    created_at: datetime


class UserBrief(ORM):
    id: int
    name: str
    is_active: bool


class UserCreate(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=120)
    role: Role = "viewer"
    temporary_password: str = Field(max_length=200)


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    role: Role | None = None
    is_active: bool | None = None
    temporary_password: str | None = Field(default=None, max_length=200)


# ---- plan structure ----
class WorkstreamOut(ORM):
    id: int
    key: str
    name: str
    description: str


class CriterionOut(ORM):
    id: int
    text: str
    is_met: bool


class PhaseOut(ORM):
    id: int
    key: str
    name: str
    subtitle: str
    end_date: date | None
    criteria: list[CriterionOut]


class CriterionUpdate(BaseModel):
    is_met: bool


class MetaOut(BaseModel):
    workstreams: list[WorkstreamOut]
    phases: list[PhaseOut]
    users: list[UserBrief]


# ---- tasks ----
class TaskBase(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str = Field(default="", max_length=20000)
    phase_id: int | None = None
    workstream_id: int | None = None
    owner_id: int | None = None
    status: Status = "not_started"
    priority: Priority = "medium"
    due_date: date | None = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=20000)
    phase_id: int | None = None
    workstream_id: int | None = None
    owner_id: int | None = None
    status: Status | None = None
    priority: Priority | None = None
    due_date: date | None = None


class TaskOut(ORM):
    id: int
    title: str
    description: str
    phase_id: int | None
    workstream_id: int | None
    owner_id: int | None
    status: Status
    priority: Priority
    due_date: date | None
    sort: int
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    comment_count: int = 0


class CommentIn(BaseModel):
    body: str = Field(min_length=1, max_length=5000)


class CommentOut(ORM):
    id: int
    body: str
    created_at: datetime
    user_id: int | None
    user_name: str = ""


class AuditOut(ORM):
    id: int
    at: datetime
    user_email: str
    action: str
    entity_type: str
    entity_id: int | None
    details: str
    ip: str


class AuditPage(BaseModel):
    items: list[AuditOut]
    total: int
