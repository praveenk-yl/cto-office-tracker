# CTO Office Tracker

Tracks the tasks in the Yantralive CTO office plan: the 30/60/90-day roadmap, its exit
criteria, and the five workstreams (inventory and governance, security, IP protection and data
theft, architecture and scale, vendors/policy/people).

- **Frontend:** React 18 + Vite (no UI framework, two runtime dependencies)
- **Backend:** FastAPI + SQLAlchemy
- **Database:** MySQL 8 (MariaDB also works)

## What it does

- **Dashboard:** overall progress, blocked/overdue/unowned counts, progress and exit-criteria
  checklist for each phase, progress per workstream, and a "needs attention" list.
- **Tasks:** all tasks grouped by phase, with filters (phase, workstream, status, owner, search),
  quick status changes, and a side panel to edit owner, priority, due date and notes, comment,
  and see the task's change history.
- **Users (admin):** add people, set roles, reset passwords, deactivate leavers.
- **Audit log (admin):** every sign-in, failed sign-in and change, with user, time and IP.

On first start an empty database is seeded with 38 tasks from the plan, each phase's exit
criteria, and due dates at the end of each phase (counted from `PROGRAM_START_DATE`).

## Security

Built with the plan's data-theft concerns in mind:

- No self sign-up. An admin creates each account with a temporary password, which must be
  changed at first sign-in (minimum 12 characters, bcrypt hashed).
- Roles: **admin** (everything), **editor** (edit tasks, comment), **viewer** (read only).
  Enforced in the API, not just hidden in the UI.
- Sessions are an `HttpOnly`, `Secure`, `SameSite=Strict` cookie that expires after 8 hours.
  Mutating requests also need an `X-Requested-With` header (CSRF defence).
- Deactivating a user, changing their role or resetting their password signs them out
  everywhere immediately.
- 5 failed sign-ins lock the account for 15 minutes. Login errors don't reveal whether an email
  exists.
- Append-only audit log of logins and every change.
- No public API docs (`/docs` is off), security headers and a strict CSP via nginx.

Recommended when you deploy it: serve it only over HTTPS and only on the office network or VPN,
like the main app (see the plan, "Specific to your setup").

## Run it with Docker

```bash
cp .env.example .env      # fill in passwords, SECRET_KEY and ADMIN_EMAIL/ADMIN_PASSWORD
docker compose up -d --build
```

Open http://localhost:8080 (or `WEB_PORT`) and sign in with `ADMIN_EMAIL` / `ADMIN_PASSWORD`.
For plain-http local testing set `COOKIE_SECURE=false`, otherwise the browser drops the cookie.

If you put a load balancer (e.g. AWS ALB) in front of nginx, change
`proxy_set_header X-Forwarded-For` in `frontend/nginx.conf` so the audit log records the real
client IP instead of the load balancer's.

## Local development

```bash
# Database
mysql -e "CREATE DATABASE tracker CHARACTER SET utf8mb4;
          CREATE USER 'tracker'@'localhost' IDENTIFIED BY 'tracker';
          GRANT ALL ON tracker.* TO 'tracker'@'localhost';"

# Backend (http://localhost:8000)
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
DATABASE_URL=mysql+pymysql://tracker:tracker@localhost:3306/tracker \
SECRET_KEY=dev-only-secret COOKIE_SECURE=false \
ADMIN_EMAIL=you@yantralive.com ADMIN_PASSWORD=choose-a-temp-pass \
.venv/bin/uvicorn app.main:app --reload

# Frontend (http://localhost:5173, proxies /api to the backend)
cd frontend
npm install && npm run dev
```

Tests (use SQLite by default; set `DATABASE_URL` to run them on MySQL):

```bash
cd backend && .venv/bin/pip install pytest httpx && .venv/bin/python -m pytest
```

## Notes

- Tables are created on startup with SQLAlchemy `create_all`. If the schema starts changing
  often, add Alembic migrations.
- To change the seeded plan, edit `backend/app/seed_data.py`. Seeding only runs on an empty
  database.
