from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db
from .models import User

COOKIE_NAME = "tracker_session"
ALGORITHM = "HS256"
MIN_PASSWORD_LENGTH = 12


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except ValueError:
        return False


# Used to spend the same time on unknown emails as on wrong passwords.
_DUMMY_HASH = hash_password("dummy-password-for-timing")


def check_password_strength(password: str) -> None:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters.",
        )
    if len(password.encode()) > 72:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Password is too long (max 72 bytes).")


def create_session_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "ver": user.token_version,
        "iat": now,
        "exp": now + timedelta(hours=settings.session_hours),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def client_ip(request: Request) -> str:
    return request.client.host if request.client else ""


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not signed in.")
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired. Sign in again.")
    user = db.get(User, int(payload.get("sub", 0)))
    if not user or not user.is_active or user.token_version != payload.get("ver"):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session is no longer valid.")
    return user


def get_active_user(user: User = Depends(get_current_user)) -> User:
    """A signed-in user who has already replaced their temporary password."""
    if user.must_change_password:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Change your password first.")
    return user


def require_editor(user: User = Depends(get_active_user)) -> User:
    if user.role not in ("admin", "editor"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You have read-only access.")
    return user


def require_admin(user: User = Depends(get_active_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admins only.")
    return user
