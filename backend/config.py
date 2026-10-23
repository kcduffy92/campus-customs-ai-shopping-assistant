"""Shared paths and settings for the backend. Secrets come from hw4/.env, never from source code."""

from __future__ import annotations

import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent

load_dotenv(PROJECT_DIR / ".env")

DATA_DIR = Path(os.getenv("CAMPUS_DATA_DIR") or PROJECT_DIR / "data")
DB_PATH = DATA_DIR / "campus_customs.db"
PRODUCTS_DIR = DATA_DIR / "products"

# URL prefix under which product images are served; catalogue rows store paths like "products/<file>.jpg".
MEDIA_URL = "/media"

# AI model: OpenAI model routed through Portkey. Keys stay on the server and are never sent to the browser.
PORTKEY_BASE_URL = os.getenv("PORTKEY_BASE_URL", "https://api.portkey.ai/v1")
PORTKEY_PROVIDER = os.getenv("PORTKEY_PROVIDER", "openai")
OPENAI_MODEL = os.getenv("OPENAI_MODEL") or "gpt-5.6-luna"
PROMPT_PATH = BACKEND_DIR / "prompts" / "prompt.md"


def portkey_api_key() -> str:
    """Read at call time so a key added to .env is picked up after a restart without code changes."""
    return (os.getenv("PORTKEY_API_KEY") or "").strip()


# Signs login session cookies. Set a long random value in .env; without one, a temporary key is generated and
# everyone is signed out whenever the backend restarts.
SESSION_SECRET = os.getenv("SESSION_SECRET") or secrets.token_hex(32)
SESSION_SECRET_IS_TEMPORARY = not os.getenv("SESSION_SECRET")
# Send the session cookie over HTTPS only. Keep false for local http://localhost development.
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"

# Allowed browser origins for direct (non-proxied) API calls during development.
FRONTEND_ORIGINS = [o.strip() for o in os.getenv("FRONTEND_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if o.strip()]
