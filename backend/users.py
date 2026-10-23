"""User account queries against the existing `users` table (schema unchanged)."""

from __future__ import annotations

import sqlite3

from db import connect
from models import UserPublic

_USER_COLUMNS = "id, name, email, first_name, last_name, created_at"


class EmailAlreadyRegistered(Exception):
    pass


def normalize_email(email: str) -> str:
    return email.strip().lower()


def _to_public(row: sqlite3.Row) -> UserPublic:
    first, last = row["first_name"], row["last_name"]
    if not first:  # first_name/last_name are nullable; fall back to splitting the full name
        first, _, rest = (row["name"] or "").partition(" ")
        last = last or rest
    return UserPublic(
        id=row["id"],
        email=row["email"],
        first_name=first or "",
        last_name=last or "",
        name=row["name"],
        created_at=row["created_at"],
    )


def get_user(user_id: int) -> UserPublic | None:
    with connect(readonly=True) as conn:
        row = conn.execute(f"SELECT {_USER_COLUMNS} FROM users WHERE id = ?", (user_id,)).fetchone()
    return _to_public(row) if row else None


def get_login_record(email: str) -> tuple[UserPublic, str] | None:
    """The user plus their stored password hash, for login only. The hash never leaves the backend."""
    with connect(readonly=True) as conn:
        row = conn.execute(
            f"SELECT {_USER_COLUMNS}, password_hash FROM users WHERE lower(email) = ?", (normalize_email(email),)
        ).fetchone()
    return (_to_public(row), row["password_hash"]) if row else None


def create_user(first_name: str, last_name: str, email: str, password_hash: str) -> UserPublic:
    email = normalize_email(email)
    with connect() as conn:
        # Emails are compared case-insensitively; the UNIQUE constraint in SQLite is case-sensitive on its own.
        if conn.execute("SELECT 1 FROM users WHERE lower(email) = ?", (email,)).fetchone():
            raise EmailAlreadyRegistered
        try:
            cur = conn.execute(
                "INSERT INTO users (name, email, password_hash, first_name, last_name) VALUES (?, ?, ?, ?, ?)",
                (f"{first_name} {last_name}", email, password_hash, first_name, last_name),
            )
        except sqlite3.IntegrityError as exc:  # race with a simultaneous registration
            raise EmailAlreadyRegistered from exc
        row = conn.execute(f"SELECT {_USER_COLUMNS} FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()
    return _to_public(row)
