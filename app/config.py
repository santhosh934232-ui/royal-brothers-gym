"""
Royal Brothers Fitness Gym - Configuration
Holds Flask app settings, MySQL credentials, and Gmail SMTP credentials.

IMPORTANT:
All secrets (SECRET_KEY, DB_PASSWORD, MAIL_USERNAME, MAIL_PASSWORD) must be
set as environment variables. Nothing sensitive is hardcoded here anymore.
Copy .env.example to .env, fill in your real values, and load it before
running the app (e.g. with `python-dotenv`, or by exporting the vars in
your shell / hosting provider's config panel).
"""

import os
from dotenv import load_dotenv
load_dotenv()



def _require_env(name):
    """Raises a clear error at startup instead of silently running with
    a missing/blank secret."""
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            f"Set it (see .env.example) before starting the app."
        )
    return value


class Config:
    # ---------- Flask / Session Settings ----------
    SECRET_KEY = _require_env("SECRET_KEY")

    SESSION_PERMANENT = False

    # ---------- MySQL Database Settings ----------
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = _require_env("DB_PASSWORD")
    DB_NAME = os.environ.get("DB_NAME", "royal_brothers_gym")
    DB_PORT = int(os.environ.get("DB_PORT", 3306))

    # ---------- Gmail SMTP Settings ----------
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "True") == "True"
    MAIL_USE_SSL = os.environ.get("MAIL_USE_SSL", "False") == "True"
    MAIL_USERNAME = _require_env("MAIL_USERNAME")
    MAIL_PASSWORD = _require_env("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = (
        os.environ.get("MAIL_SENDER_NAME", "Royal Brothers Fitness Gym"),
        MAIL_USERNAME,
    )

    # ---------- App URL (used to build verification/reset links) ----------
    # Set this to your real domain in production (e.g. https://yourgym.com).
    # Falls back to request.host_url at runtime if not set.
    APP_BASE_URL = os.environ.get("APP_BASE_URL", "")