from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..auth import require_admin
from ..db import get_db
from ..models import AuditLog, User
from ..schemas import AuditPage

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("", response_model=AuditPage)
def list_audit(
    action: str | None = None,
    user_email: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    stmt = select(AuditLog)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if user_email:
        stmt = stmt.where(AuditLog.user_email.ilike(f"%{user_email}%"))
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(
        stmt.order_by(AuditLog.at.desc(), AuditLog.id.desc()).limit(limit).offset(offset)
    ).all()
    return AuditPage(items=items, total=total or 0)
