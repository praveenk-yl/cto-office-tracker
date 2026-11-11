import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .config import settings
from .db import Base, SessionLocal, engine
from .routers import audit_log, auth, tasks, users
from .seed import ensure_admin, seed_plan

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("tracker")

UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.secret_key == "change-me":
        log.warning("SECRET_KEY is the default value. Set a long random SECRET_KEY in production.")
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        ensure_admin(db)
        if settings.seed_on_start:
            seed_plan(db)
    yield


app = FastAPI(
    title="CTO Office Tracker",
    lifespan=lifespan,
    docs_url=None,  # no public API explorer
    redoc_url=None,
    openapi_url=None,
)


@app.middleware("http")
async def security_middleware(request: Request, call_next):
    # CSRF defence on top of the SameSite=Strict cookie: browsers won't send this custom
    # header cross-site without a CORS preflight, and we allow no cross-origin requests.
    if request.method in UNSAFE_METHODS and request.headers.get("x-requested-with") != "tracker":
        return JSONResponse({"detail": "Missing X-Requested-With header."}, status_code=403)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/api/health")
def health():
    return {"ok": True}


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(tasks.router)
app.include_router(audit_log.router)
