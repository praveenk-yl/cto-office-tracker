from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from .. import audit
from ..auth import get_active_user, require_admin, require_editor
from ..db import get_db
from ..models import AuditLog, Comment, ExitCriterion, Phase, Task, User, Workstream, utcnow
from ..schemas import (
    AuditOut,
    CommentIn,
    CommentOut,
    CriterionOut,
    CriterionUpdate,
    MetaOut,
    TaskCreate,
    TaskOut,
    TaskUpdate,
)

router = APIRouter(prefix="/api", tags=["tasks"])

TRACKED_FIELDS = ("title", "description", "phase_id", "workstream_id", "owner_id", "status",
                  "priority", "due_date")


def _snapshot(task: Task) -> dict:
    return {f: getattr(task, f) for f in TRACKED_FIELDS}


def _validate_refs(db: Session, data: dict) -> None:
    for field, model, label in (
        ("phase_id", Phase, "phase"),
        ("workstream_id", Workstream, "workstream"),
        ("owner_id", User, "owner"),
    ):
        if data.get(field) is not None and db.get(model, data[field]) is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unknown {label}.")


def _task_out(task: Task, comment_count: int = 0) -> TaskOut:
    out = TaskOut.model_validate(task)
    out.comment_count = comment_count
    return out


@router.get("/meta", response_model=MetaOut)
def meta(_: User = Depends(get_active_user), db: Session = Depends(get_db)):
    return MetaOut(
        workstreams=db.scalars(select(Workstream).order_by(Workstream.sort)).all(),
        phases=db.scalars(select(Phase).order_by(Phase.sort)).all(),
        users=db.scalars(select(User).order_by(User.name)).all(),
    )


@router.patch("/criteria/{criterion_id}", response_model=CriterionOut)
def update_criterion(
    criterion_id: int,
    body: CriterionUpdate,
    request: Request,
    user: User = Depends(require_editor),
    db: Session = Depends(get_db),
):
    crit = db.get(ExitCriterion, criterion_id)
    if not crit:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Exit criterion not found.")
    if crit.is_met != body.is_met:
        crit.is_met = body.is_met
        audit.record(db, request, user, "criterion_updated", "criterion", crit.id,
                     {"text": crit.text, "is_met": body.is_met})
        db.commit()
    return crit


@router.get("/tasks", response_model=list[TaskOut])
def list_tasks(
    phase_id: int | None = None,
    workstream_id: int | None = None,
    status_: str | None = Query(default=None, alias="status"),
    owner_id: int | None = None,
    q: str | None = None,
    _: User = Depends(get_active_user),
    db: Session = Depends(get_db),
):
    counts = (
        select(Comment.task_id, func.count(Comment.id).label("n"))
        .group_by(Comment.task_id)
        .subquery()
    )
    stmt = (
        select(Task, func.coalesce(counts.c.n, 0))
        .outerjoin(counts, counts.c.task_id == Task.id)
        .order_by(Task.phase_id, Task.sort, Task.id)
    )
    if phase_id is not None:
        stmt = stmt.where(Task.phase_id == phase_id)
    if workstream_id is not None:
        stmt = stmt.where(Task.workstream_id == workstream_id)
    if status_:
        stmt = stmt.where(Task.status == status_)
    if owner_id is not None:
        stmt = stmt.where(Task.owner_id == (owner_id or None))
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(Task.title.ilike(like), Task.description.ilike(like)))
    return [_task_out(t, n) for t, n in db.execute(stmt).all()]


@router.post("/tasks", response_model=TaskOut, status_code=201)
def create_task(
    body: TaskCreate,
    request: Request,
    user: User = Depends(require_editor),
    db: Session = Depends(get_db),
):
    data = body.model_dump()
    _validate_refs(db, data)
    max_sort = db.scalar(select(func.max(Task.sort)).where(Task.phase_id == body.phase_id)) or 0
    task = Task(**data, sort=max_sort + 1)
    if task.status == "done":
        task.completed_at = utcnow()
    db.add(task)
    db.flush()
    audit.record(db, request, user, "task_created", "task", task.id, {"title": task.title})
    db.commit()
    return _task_out(task)


def _get_task(db: Session, task_id: int) -> Task:
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found.")
    return task


@router.get("/tasks/{task_id}", response_model=TaskOut)
def get_task(task_id: int, _: User = Depends(get_active_user), db: Session = Depends(get_db)):
    task = _get_task(db, task_id)
    return _task_out(task, len(task.comments))


@router.patch("/tasks/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    body: TaskUpdate,
    request: Request,
    user: User = Depends(require_editor),
    db: Session = Depends(get_db),
):
    task = _get_task(db, task_id)
    data = body.model_dump(exclude_unset=True)
    for required in ("title", "status", "priority"):
        if required in data and data[required] is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"{required} can't be empty.")
    _validate_refs(db, data)
    before = _snapshot(task)
    for key, value in data.items():
        setattr(task, key, value)
    if "status" in data:
        if task.status == "done" and before["status"] != "done":
            task.completed_at = utcnow()
        elif task.status != "done":
            task.completed_at = None
    changes = audit.diff(before, _snapshot(task))
    if changes:
        if "description" in changes:
            changes["description"] = {"changed": True}
        audit.record(db, request, user, "task_updated", "task", task.id, changes)
    db.commit()
    return _task_out(task, len(task.comments))


@router.delete("/tasks/{task_id}", status_code=204)
def delete_task(
    task_id: int,
    request: Request,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    task = _get_task(db, task_id)
    audit.record(db, request, user, "task_deleted", "task", task.id, _snapshot(task))
    db.delete(task)
    db.commit()


@router.get("/tasks/{task_id}/comments", response_model=list[CommentOut])
def list_comments(task_id: int, _: User = Depends(get_active_user), db: Session = Depends(get_db)):
    task = _get_task(db, task_id)
    out = []
    for c in task.comments:
        item = CommentOut.model_validate(c)
        item.user_name = c.user.name if c.user else "Unknown"
        out.append(item)
    return out


@router.post("/tasks/{task_id}/comments", response_model=CommentOut, status_code=201)
def add_comment(
    task_id: int,
    body: CommentIn,
    request: Request,
    user: User = Depends(require_editor),
    db: Session = Depends(get_db),
):
    task = _get_task(db, task_id)
    comment = Comment(task_id=task.id, user_id=user.id, body=body.body.strip())
    db.add(comment)
    db.flush()
    audit.record(db, request, user, "comment_added", "task", task.id, {"comment_id": comment.id})
    db.commit()
    out = CommentOut.model_validate(comment)
    out.user_name = user.name
    return out


@router.get("/tasks/{task_id}/history", response_model=list[AuditOut])
def task_history(task_id: int, _: User = Depends(get_active_user), db: Session = Depends(get_db)):
    _get_task(db, task_id)
    rows = db.scalars(
        select(AuditLog)
        .where(AuditLog.entity_type == "task", AuditLog.entity_id == task_id)
        .order_by(AuditLog.at.desc(), AuditLog.id.desc())
    ).all()
    # The per-task history is visible to everyone, so leave out IP addresses.
    return [AuditOut.model_validate(r).model_copy(update={"ip": ""}) for r in rows]

