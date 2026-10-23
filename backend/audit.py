"""AI audit trail (Problem 12): one structured JSON record per assistant request, appended to a local JSONL file.

What a record traces: when the message arrived, which tools ran (arguments, products/inventory rows returned, timing),
which product cards were shown and whether each was verified against the database, the model usage, and how the
request ended (success / blocked / failed) with an error category that separates AI-provider problems from database
problems and application bugs.

Privacy by design (see output/harness.md, section 8):
- No message text, reply text, names, emails, passwords, cookies, tokens or keys are written.
- Customers and conversations appear only as keyed pseudonyms (HMAC-SHA256 with SESSION_SECRET), e.g. "cust_3f9a1c2b7d4e".
  The same customer gets the same reference, but the reference can't be turned back into an account without the key.
- Search words the assistant passes to its tools are kept (they are needed to troubleshoot searches) but truncated, and
  anything that looks like an email address, phone number or card number is masked.

Storage: AUDIT_LOG_PATH, default <data dir>/audit/audit_log.jsonl. It lives next to the database (git-ignored, local only)
and is appended to, so it survives restarts. Writing an audit record never breaks a customer's request.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import re
import sqlite3
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import DATA_DIR, OPENAI_MODEL, SESSION_SECRET

log = logging.getLogger("campus_customs.audit")

SCHEMA = "campus-customs.audit/1"
AUDIT_LOG_PATH = Path(os.getenv("AUDIT_LOG_PATH") or DATA_DIR / "audit" / "audit_log.jsonl")
_lock = threading.Lock()

# Error categories (troubleshooting): who is responsible for the failure.
PROVIDER_TIMEOUT = "provider_timeout"  # the AI provider didn't answer in time
PROVIDER_UNAVAILABLE = "provider_unavailable"  # couldn't reach the provider, or it returned a server error
PROVIDER_REJECTED = "provider_rejected"  # the provider refused the request (e.g. HTTP 4xx other than the content filter)
PROVIDER_CONTENT_FILTER = "provider_content_filter"  # the provider's safety filter blocked the message
MODEL_OUTPUT_ERROR = "model_output_error"  # the model answered but the answer was unusable (empty, invalid, too many steps)
NOT_CONFIGURED = "not_configured"  # no PORTKEY_API_KEY
DATABASE_ERROR = "database_error"  # SQLite missing/locked/failed
APPLICATION_ERROR = "application_error"  # a bug in our code
VALIDATION_ERROR = "validation_error"  # the request itself was invalid (empty / too long / malformed)
CONVERSATION_NOT_OWNED = "conversation_not_owned"  # asked for someone else's (or a non-existent) conversation


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _ref(kind: str, value: Any) -> str | None:
    """Keyed pseudonym: stable for the same value, not reversible without SESSION_SECRET."""
    if value is None:
        return None
    digest = hmac.new(SESSION_SECRET.encode(), f"{kind}:{value}".encode(), hashlib.sha256).hexdigest()
    return f"{kind}_{digest[:12]}"


customer_ref = lambda user_id: _ref("cust", user_id)  # noqa: E731
conversation_ref = lambda conversation_id: _ref("conv", conversation_id)  # noqa: E731

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_LONG_DIGITS = re.compile(r"\d[\d\s().-]{6,}\d")


def safe_text(text: Any, limit: int = 60) -> str | None:
    """Short, masked copy of a search term. Emails and long digit runs (phones, card numbers) become [redacted]."""
    if text is None:
        return None
    s = " ".join(str(text).split())
    s = _EMAIL.sub("[redacted-email]", s)
    s = _LONG_DIGITS.sub("[redacted-number]", s)
    return s if len(s) <= limit else s[: limit - 1] + "…"


def classify(exc: BaseException) -> str:
    """Map an exception to an error category, so provider, database and application problems are told apart."""
    from db import DatabaseUnavailable  # local import: db imports config only, but keep audit import-light

    seen: set[int] = set()
    e: BaseException | None = exc
    while e is not None and id(e) not in seen:  # look through wrapped causes
        seen.add(id(e))
        name = type(e).__name__
        if isinstance(e, (DatabaseUnavailable, sqlite3.Error)):
            return DATABASE_ERROR
        if isinstance(e, TimeoutError) or "Timeout" in name:
            return PROVIDER_TIMEOUT
        if name in ("APIConnectionError", "ConnectError", "ConnectTimeout") or "Connection" in name:
            return PROVIDER_UNAVAILABLE
        status = getattr(e, "status_code", None)
        if isinstance(status, int):
            return PROVIDER_UNAVAILABLE if status >= 500 or status == 429 else PROVIDER_REJECTED
        if name in ("UsageLimitExceeded", "UnexpectedModelBehavior"):
            return MODEL_OUTPUT_ERROR
        e = e.__cause__ or e.__context__
    return APPLICATION_ERROR


def short_error(exc: BaseException) -> str:
    """Exception type plus a short, masked message (provider messages can be long; never include request bodies)."""
    msg = safe_text(str(exc), 160) or ""
    return f"{type(exc).__name__}: {msg}" if msg else type(exc).__name__


class AuditRecord:
    """Collects one assistant request. Create it when the request arrives; call finish() exactly once."""

    def __init__(self, endpoint: str, *, user_id: int | None = None, message: str | None = None):
        self._t0 = time.perf_counter()
        self._done = False
        self.blocked_by: str | None = None  # set when the provider's content filter refused the message
        self.data: dict[str, Any] = {
            "schema": SCHEMA,
            "event": "chat_request",
            "request_id": f"req_{uuid.uuid4().hex[:16]}",
            "received_at": _now(),
            "endpoint": endpoint,
            "customer": {"signed_in": user_id is not None, "customer_ref": customer_ref(user_id)},
            "conversation": {"conversation_ref": None, "new_conversation": None, "context_messages": 0},
            "input": {"message_chars": len(message) if message is not None else None, "small_talk": None, "page": None},
            "model": {"name": OPENAI_MODEL, "requests": 0, "input_tokens": 0, "output_tokens": 0},
            "tool_calls": [],
            "recommendations": {"model_selected": [], "size": None, "shown": [], "dropped": [], "all_verified_against_database": None},
            "outcome": None,
        }

    def set_customer(self, user_id: int | None) -> None:
        self.data["customer"] = {"signed_in": user_id is not None, "customer_ref": customer_ref(user_id)}

    @property
    def request_id(self) -> str:
        return self.data["request_id"]

    def elapsed_ms(self) -> int:
        return round((time.perf_counter() - self._t0) * 1000)

    # ----- filled in while the request runs -----

    def set_context(self, *, conversation_id: int | None, new_conversation: bool, context_messages: int,
                    page_path: str | None, page_product_id: str | None) -> None:
        self.data["conversation"] = {
            "conversation_ref": conversation_ref(conversation_id),
            "new_conversation": new_conversation,
            "context_messages": context_messages,
        }
        page = (page_path or "/").split("?", 1)[0]
        kind = "product" if page.startswith("/products/") else "catalogue" if page == "/shop" else "home" if page == "/" else "account" if page.startswith("/account") else "other"
        self.data["input"]["page"] = {"type": kind, "verified_product_id": page_product_id}

    def tool_call(self, tool: str, *, arguments: dict[str, Any], status: str, started: float, result: dict[str, Any] | None = None,
                  error: str | None = None) -> None:
        self.data["tool_calls"].append({
            "seq": len(self.data["tool_calls"]) + 1,
            "tool": tool,
            "at_ms": round((started - self._t0) * 1000),
            "duration_ms": round((time.perf_counter() - started) * 1000, 1),
            "arguments": arguments,
            "status": status,
            "result": result,
            "error": error,
        })

    def recommendations(self, *, selected: list[str], size: str | None, shown: list[str], dropped: list[dict[str, str]]) -> None:
        self.data["recommendations"] = {
            "model_selected": selected,
            "size": size,
            "shown": shown,
            "dropped": dropped,
            # Every shown card was built from a catalogue row for an id a tool returned (agent.build_cards).
            "all_verified_against_database": True if shown else None,
        }

    def model_usage(self, usage: Any) -> None:
        self.data["model"].update({
            "requests": getattr(usage, "requests", 0) or 0,
            "input_tokens": getattr(usage, "input_tokens", 0) or 0,
            "output_tokens": getattr(usage, "output_tokens", 0) or 0,
        })

    def set_small_talk(self, value: bool) -> None:
        self.data["input"]["small_talk"] = value

    # ----- end of the request -----

    def finish(self, status: str, *, http_status: int, category: str | None = None, error: str | None = None,
               reply_chars: int | None = None, cards: int = 0, saved: bool | None = None) -> None:
        if self._done:
            return
        self._done = True
        self.data["outcome"] = {
            "status": status,  # success | blocked | failed
            "category": category,
            "http_status": http_status,
            "reply_chars": reply_chars,
            "cards_shown": cards,
            "saved_to_history": saved,
            "error": error,
        }
        self.data["finished_at"] = _now()
        self.data["duration_ms"] = self.elapsed_ms()
        write(self.data)


def write(record: dict[str, Any]) -> None:
    """Append one record as a JSON line. Failures are logged, never raised (auditing must not break shopping)."""
    try:
        line = json.dumps(record, ensure_ascii=False, separators=(",", ":"))
        with _lock:
            AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with AUDIT_LOG_PATH.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
                f.flush()
    except Exception:
        log.exception("Could not write audit record")


def simple_event(event: str, endpoint: str, *, user_id: int | None, status: str, category: str | None, http_status: int,
                 detail: dict[str, Any] | None = None) -> None:
    """Records for requests that never reach the assistant (invalid input, someone else's conversation)."""
    write({
        "schema": SCHEMA,
        "event": event,
        "request_id": f"req_{uuid.uuid4().hex[:16]}",
        "received_at": _now(),
        "endpoint": endpoint,
        "customer": {"signed_in": user_id is not None, "customer_ref": customer_ref(user_id)},
        "outcome": {"status": status, "category": category, "http_status": http_status},
        "detail": detail or {},
    })


def read_all(path: Path | None = None) -> list[dict[str, Any]]:
    """Read the log back (used by tests and the evidence export). Skips a partly written last line, if any."""
    p = path or AUDIT_LOG_PATH
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out
