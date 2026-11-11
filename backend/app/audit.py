import json

from fastapi import Request
from sqlalchemy.orm import Session

from .auth import client_ip
from .models import AuditLog, User


def record(
    db: Session,
    request: Request | None,
    user: User | None,
    action: str,
    entity_type: str = "",
    entity_id: int | None = None,
    details: dict | None = None,
    user_email: str | None = None,
) -> None:
    """Add an audit entry to the session. The caller commits it with its own change."""
    db.add(
        AuditLog(
            user_id=user.id if user else None,
            user_email=user_email if user_email is not None else (user.email if user else ""),
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=json.dumps(details or {}, default=str),
            ip=client_ip(request) if request else "",
        )
    )


def diff(before: dict, after: dict) -> dict:
    return {k: {"from": before.get(k), "to": v} for k, v in after.items() if before.get(k) != v}
