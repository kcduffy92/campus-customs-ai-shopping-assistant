"""Password hashing and login sessions.

Passwords (Problem 4 specification):
- PBKDF2-HMAC-SHA256, 120,000 iterations.
- Stored as  pbkdf2_sha256$<salt>$<hex digest>.  The salt string is used as UTF-8 bytes, exactly as it appears in the
  stored value. This reproduces the existing seeded hashes (verified against the provided test account).
- Login re-hashes the entered password with the salt taken from the stored hash and compares in constant time.

Sessions: after login/registration the browser gets an HttpOnly cookie holding  <user_id>.<expiry>.<HMAC signature>.
The signature uses SESSION_SECRET from .env, so the cookie cannot be forged or edited. No session table is needed,
so the database structure stays unchanged.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import time

from config import SESSION_SECRET

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 120_000
SALT_BYTES = 16  # secrets.token_hex(16) -> 32-character hex salt string

SESSION_COOKIE = "cc_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 7  # 7 days


def _pbkdf2_hex(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), ITERATIONS).hex()


def hash_password(password: str) -> str:
    salt = secrets.token_hex(SALT_BYTES)
    return f"{ALGORITHM}${salt}${_pbkdf2_hex(password, salt)}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, salt, expected = stored.split("$")
    except (AttributeError, ValueError):
        return False
    if algorithm != ALGORITHM or not salt:
        return False
    return hmac.compare_digest(_pbkdf2_hex(password, salt), expected)


# Used when an email is not registered, so a failed login takes the same time whether or not the account exists.
_DUMMY_HASH = hash_password(secrets.token_hex(8))


def burn_equivalent_time(password: str) -> None:
    verify_password(password, _DUMMY_HASH)


def _sign(payload: str) -> str:
    return hmac.new(SESSION_SECRET.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()


def create_session_token(user_id: int) -> str:
    payload = f"{user_id}.{int(time.time()) + SESSION_MAX_AGE}"
    return f"{payload}.{_sign(payload)}"


def read_session_token(token: str | None) -> int | None:
    """Return the user id from a valid, unexpired token, otherwise None."""
    if not token:
        return None
    try:
        user_id, expires, signature = token.split(".")
        if not hmac.compare_digest(signature, _sign(f"{user_id}.{expires}")):
            return None
        if int(expires) < time.time():
            return None
        return int(user_id)
    except ValueError:
        return None
