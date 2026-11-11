from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import audit
from ..auth import check_password_strength, hash_password, require_admin
from ..db import get_db
from ..models import User
from ..schemas import UserCreate, UserOut, UserUpdate

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=list[UserOut])
def list_users(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return db.scalars(select(User).order_by(User.is_active.desc(), User.name)).all()


@router.post("", response_model=UserOut, status_code=201)
def create_user(
    body: UserCreate,
    request: Request,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    email = body.email.lower()
    if db.scalar(select(User).where(func.lower(User.email) == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "A user with that email already exists.")
    check_password_strength(body.temporary_password)
    user = User(
        email=email,
        name=body.name.strip(),
        role=body.role,
        password_hash=hash_password(body.temporary_password),
        must_change_password=True,
    )
    db.add(user)
    db.flush()
    audit.record(db, request, admin, "user_created", "user", user.id,
                 {"email": email, "role": body.role})
    db.commit()
    return user


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    body: UserUpdate,
    request: Request,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found.")
    if user.id == admin.id and (body.is_active is False or (body.role and body.role != "admin")):
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "You can't remove your own admin access or deactivate yourself.")

    before = {"name": user.name, "role": user.role, "is_active": user.is_active}
    changes = body.model_dump(exclude_unset=True, exclude={"temporary_password"})
    for key, value in changes.items():
        if value is not None:
            setattr(user, key, value)

    details = audit.diff(before, {k: getattr(user, k) for k in before})
    revoke = False
    if body.temporary_password:
        check_password_strength(body.temporary_password)
        user.password_hash = hash_password(body.temporary_password)
        user.must_change_password = True
        user.failed_logins = 0
        user.locked_until = None
        details["password_reset"] = True
        revoke = True
    if "role" in details or details.get("is_active", {}).get("to") is False:
        revoke = True
    if revoke:
        user.token_version += 1  # signs the user out everywhere

    if details:
        action = "user_deactivated" if details.get("is_active", {}).get("to") is False else "user_updated"
        audit.record(db, request, admin, action, "user", user.id, details)
    db.commit()
    return user
