from datetime import date

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # mysql+pymysql://user:password@host:3306/dbname
    database_url: str = "mysql+pymysql://tracker:tracker@localhost:3306/tracker"

    # Must be a long random string in production (e.g. `openssl rand -hex 32`).
    secret_key: str = "change-me"
    session_hours: int = 8
    # Set to false only for local http development.
    cookie_secure: bool = True

    # First admin account, created on first start if no users exist.
    admin_email: str = "admin@example.com"
    admin_password: str = ""
    admin_name: str = "CTO"

    # Seed the plan's workstreams, phases and tasks into an empty database.
    seed_on_start: bool = True
    # Day 1 of the 30/60/90-day roadmap; seeded due dates are counted from it.
    program_start_date: date = date(2026, 11, 11)

    # Lock an account for this many minutes after this many failed logins.
    max_failed_logins: int = 5
    lockout_minutes: int = 15


settings = Settings()
