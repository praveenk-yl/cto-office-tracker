from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import audit
from ..auth import (
    _DUMMY_HASH,
    COOKIE_NAME,
    check_password_strength,
    create_session_token,
    get_current_user,
    hash_password,
    verify_password,
)
from ..config import settings
from ..db import get_db
from ..models import User, utcnow
from ..schemas import ChangePasswordIn, LoginIn, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])

GENERIC_LOGIN_ERROR = "Wrong email or password."


def _set_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=settings.session_hours * 3600,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        path="/api",
    )


@router.post("/login", response_model=UserOut)
def login(body: LoginIn, request: Request, response: Response, db: Session = Depends(get_db)):
    email = body.email.lower()
    user = db.scalar(select(User).where(func.lower(User.email) == email))
    now = utcnow()

    if user is None:
        verify_password(body.password, _DUMMY_HASH)
        audit.record(db, request, None, "login_failed", "user", details={"reason": "unknown_email"},
                     user_email=email)
        db.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, GENERIC_LOGIN_ERROR)

    if user.locked_until and user.locked_until > now:
        audit.record(db, request, user, "login_blocked", "user", user.id, {"reason": "locked"})
        db.commit()
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Too many failed attempts. Try again later or ask an admin.",
        )

    if not verify_password(body.password, user.password_hash) or not user.is_active:
        user.failed_logins += 1
        details = {"reason": "inactive" if user.is_active is False else "bad_password"}
        if user.failed_logins >= settings.max_failed_logins:
            user.locked_until = now + timedelta(minutes=settings.lockout_minutes)
            user.failed_logins = 0
            details["locked"] = True
        audit.record(db, request, user, "login_failed", "user", user.id, details)
        db.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, GENERIC_LOGIN_ERROR)

    user.failed_logins = 0
    user.locked_until = None
    user.last_login_at = now
    audit.record(db, request, user, "login", "user", user.id)
    db.commit()
    _set_cookie(response, create_session_token(user))
    return user


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    response.delete_cookie(COOKIE_NAME, path="/api")
    try:
        user = get_current_user(request, db)
    except HTTPException:
        return response
    audit.record(db, request, user, "logout", "user", user.id)
    db.commit()
    return response


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/change-password", response_model=UserOut)
def change_password(
    body: ChangePasswordIn,
    request: Request,
    response: Response,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Current password is wrong.")
    if body.new_password == body.current_password:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Choose a new password.")
    check_password_strength(body.new_password)
    user = db.merge(user)
    user.password_hash = hash_password(body.new_password)
    user.must_change_password = False
    user.token_version += 1  # signs out every other session
    audit.record(db, request, user, "password_changed", "user", user.id)
    db.commit()
    _set_cookie(response, create_session_token(user))
    return user
