import os
import tempfile

_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_db.name}")
os.environ["SECRET_KEY"] = "test-secret-key-test-secret-key-0123456789"
os.environ["COOKIE_SECURE"] = "false"
os.environ["ADMIN_EMAIL"] = "admin@example.com"
os.environ["ADMIN_PASSWORD"] = "initial-admin-pass"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.seed_data import TASKS  # noqa: E402

H = {"X-Requested-With": "tracker"}
NEW_PW = "a-much-better-password"


@pytest.fixture(scope="module")
def admin():
    with TestClient(app) as c:
        r = c.post("/api/auth/login", headers=H,
                   json={"email": "admin@example.com", "password": "initial-admin-pass"})
        assert r.status_code == 200 and r.json()["must_change_password"] is True
        # Locked out of the app until the temporary password is changed.
        assert c.get("/api/tasks").status_code == 403
        r = c.post("/api/auth/change-password", headers=H,
                   json={"current_password": "initial-admin-pass", "new_password": NEW_PW})
        assert r.status_code == 200, r.text
        yield c


def test_requires_login():
    with TestClient(app) as c:
        assert c.get("/api/tasks").status_code == 401


def test_csrf_header_required(admin):
    assert admin.post("/api/tasks", json={"title": "x"}).status_code == 403


def test_seeded_plan(admin):
    tasks = admin.get("/api/tasks").json()
    assert len(tasks) == len(TASKS)
    meta = admin.get("/api/meta").json()
    assert len(meta["phases"]) == 3 and len(meta["workstreams"]) == 5
    assert all(len(p["criteria"]) == 3 for p in meta["phases"])


def test_task_update_and_history(admin):
    task = admin.get("/api/tasks").json()[0]
    r = admin.patch(f"/api/tasks/{task['id']}", headers=H, json={"status": "done"})
    assert r.status_code == 200 and r.json()["completed_at"]
    r = admin.post(f"/api/tasks/{task['id']}/comments", headers=H, json={"body": "Charter sent"})
    assert r.status_code == 201
    hist = admin.get(f"/api/tasks/{task['id']}/history").json()
    assert {h["action"] for h in hist} >= {"task_updated", "comment_added"}
    assert admin.get(f"/api/tasks?status=done").json()[0]["id"] == task["id"]


def test_viewer_is_read_only_and_deactivation_kills_session(admin):
    r = admin.post("/api/users", headers=H, json={
        "email": "viewer@example.com", "name": "Viewer", "role": "viewer",
        "temporary_password": "viewer-temp-pass"})
    assert r.status_code == 201
    uid = r.json()["id"]
    with TestClient(app) as v:
        v.post("/api/auth/login", headers=H,
               json={"email": "viewer@example.com", "password": "viewer-temp-pass"})
        v.post("/api/auth/change-password", headers=H,
               json={"current_password": "viewer-temp-pass", "new_password": NEW_PW})
        assert v.get("/api/tasks").status_code == 200
        assert v.post("/api/tasks", headers=H, json={"title": "nope"}).status_code == 403
        assert v.get("/api/audit").status_code == 403
        admin.patch(f"/api/users/{uid}", headers=H, json={"is_active": False})
        assert v.get("/api/tasks").status_code == 401


def test_lockout_after_failed_logins(admin):
    admin.post("/api/users", headers=H, json={
        "email": "lock@example.com", "name": "Lock", "role": "editor",
        "temporary_password": "lock-temp-password"})
    with TestClient(app) as c:
        for _ in range(5):
            r = c.post("/api/auth/login", headers=H,
                       json={"email": "lock@example.com", "password": "wrong-password"})
            assert r.status_code == 401
        r = c.post("/api/auth/login", headers=H,
                   json={"email": "lock@example.com", "password": "lock-temp-password"})
        assert r.status_code == 429
    actions = {a["action"] for a in admin.get("/api/audit?limit=500").json()["items"]}
    assert {"login", "login_failed", "login_blocked", "user_created"} <= actions


def test_short_password_rejected(admin):
    r = admin.post("/api/users", headers=H, json={
        "email": "short@example.com", "name": "S", "temporary_password": "short"})
    assert r.status_code == 400
