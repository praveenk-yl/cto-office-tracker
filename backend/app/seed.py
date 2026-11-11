import logging
from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .auth import hash_password
from .config import settings
from .models import ExitCriterion, Phase, Task, User, Workstream
from .seed_data import PHASES, TASKS, WORKSTREAMS

log = logging.getLogger("tracker.seed")


def ensure_admin(db: Session) -> None:
    if db.scalar(select(func.count(User.id))):
        return
    if len(settings.admin_password) < 12:
        log.warning("No users exist and ADMIN_PASSWORD is unset or under 12 characters; "
                    "set it to create the first admin.")
        return
    db.add(User(
        email=settings.admin_email.lower(),
        name=settings.admin_name,
        role="admin",
        password_hash=hash_password(settings.admin_password),
        must_change_password=True,
    ))
    db.commit()
    log.info("Created first admin %s (must change password on first login).", settings.admin_email)


def seed_plan(db: Session) -> None:
    if db.scalar(select(func.count(Phase.id))):
        return
    ws = {}
    for i, (key, name, desc) in enumerate(WORKSTREAMS):
        ws[key] = Workstream(key=key, name=name, description=desc, sort=i)
        db.add(ws[key])
    phases = {}
    for i, (key, name, subtitle, days, criteria) in enumerate(PHASES):
        phase = Phase(key=key, name=name, subtitle=subtitle, sort=i,
                      end_date=settings.program_start_date + timedelta(days=days - 1))
        phase.criteria = [ExitCriterion(text=t, sort=j) for j, t in enumerate(criteria)]
        phases[key] = phase
        db.add(phase)
    db.flush()
    for i, (phase_key, ws_key, priority, title, desc) in enumerate(TASKS):
        db.add(Task(
            title=title, description=desc, priority=priority, sort=i,
            phase_id=phases[phase_key].id, workstream_id=ws[ws_key].id,
            due_date=phases[phase_key].end_date,
        ))
    db.commit()
    log.info("Seeded %d workstreams, %d phases, %d tasks.", len(ws), len(phases), len(TASKS))
