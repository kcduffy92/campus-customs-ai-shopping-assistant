"""Saved conversations for signed-in customers, stored in the `chat_messages` table.

Identity: every function takes the user id from the caller, and main.py only ever passes the id of the customer
identified by the signed session cookie. Nothing here accepts a user id from the browser, and every query filters on
it, including lookups by conversation id.

Conversations (Problem 8, follow-up 1): one small schema change, a nullable `conversation_id` column. A conversation's
id is the id of its first message, so no separate table is needed. Its title (first question), message count and last
activity are derived from its rows. `ensure_schema()` adds the column once (after backing up the database), assigns
each customer's existing messages to one "earlier conversation", and adds an index. All existing rows are kept.

products_json holds which cards were shown. New rows store [{product_id, name, price, size}]; the seeded rows store full
product snapshots. Either way only `product_id` (and `size`) are read back, and cards are rebuilt from the current
database, so restored cards never show stale prices or stock.
"""

from __future__ import annotations

import json
import logging
import re
import sqlite3
from datetime import datetime, timezone

from config import DB_PATH
from db import connect
from models import ChatTurn, ProductCard

log = logging.getLogger("campus_customs.chat_history")

CONTEXT_TURNS = 20  # newest messages OF THE CURRENT CONVERSATION sent to the model as context
PAGE_MAX = 50  # messages per history request
CONVERSATIONS_MAX = 200  # conversations listed (Problem 9: was 50, which hid older chats from heavy users)
_ID_RE = re.compile(r"^[a-z0-9-]{1,120}$")


# ---------- One-time schema change ----------


def ensure_schema() -> None:
    """Add chat_messages.conversation_id if it's missing (idempotent). Backs up the database first."""
    with connect() as conn:
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(chat_messages)")}
        if "conversation_id" in columns:
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_chat_messages_user_conversation "
                "ON chat_messages (user_id, conversation_id, id)"
            )
            return

        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        backup_path = DB_PATH.with_name(f"{DB_PATH.stem}.backup-before-conversations-{stamp}.db")
        with sqlite3.connect(backup_path) as backup:
            conn.backup(backup)
        before = conn.execute("SELECT COUNT(*) FROM chat_messages").fetchone()[0]

        conn.execute("ALTER TABLE chat_messages ADD COLUMN conversation_id INTEGER")
        # Existing messages: one earlier conversation per customer, identified by that customer's first message id.
        conn.execute(
            "UPDATE chat_messages SET conversation_id = "
            "(SELECT MIN(m.id) FROM chat_messages AS m WHERE m.user_id = chat_messages.user_id) "
            "WHERE conversation_id IS NULL"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_chat_messages_user_conversation ON chat_messages (user_id, conversation_id, id)"
        )
        after = conn.execute("SELECT COUNT(*) FROM chat_messages").fetchone()[0]
        if after != before:
            raise RuntimeError("Message count changed during migration; rolling back")
    log.warning(
        "Database updated: added chat_messages.conversation_id (%d existing messages kept). Backup: %s",
        before,
        backup_path.name,
    )


# ---------- Helpers ----------


def _parse_products(raw: str | None) -> tuple[list[str], str | None]:
    """(product ids in display order, requested size) from a products_json value. Tolerates both storage formats
    and ignores anything malformed."""
    if not raw:
        return [], None
    try:
        items = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return [], None
    if not isinstance(items, list):
        return [], None
    ids: list[str] = []
    size = None
    for item in items:
        pid = item.get("product_id") if isinstance(item, dict) else None
        if isinstance(pid, str) and _ID_RE.match(pid) and pid not in ids:
            ids.append(pid)
            if size is None and isinstance(item.get("size"), str):
                size = item["size"]
    return ids[:6], size


def product_ids_and_size(raw: str | None) -> tuple[list[str], str | None]:
    return _parse_products(raw)


# ---------- Conversations ----------


def owns_conversation(user_id: int, conversation_id: int) -> bool:
    with connect(readonly=True) as conn:
        row = conn.execute(
            "SELECT 1 FROM chat_messages WHERE user_id = ? AND conversation_id = ? LIMIT 1", (user_id, conversation_id)
        ).fetchone()
    return row is not None


_REFERS_TO_THIS = re.compile(r"\b(this|that|it|these|those|this one|that one)\b", re.I)


def _clean_title(text: str, limit: int = 60) -> str:
    text = " ".join(re.sub(r"[*_`#>]+", "", text or "").split())
    if len(text) > limit:
        text = text[: limit - 1].rsplit(" ", 1)[0].rstrip(",.;:-") + "…"
    return text[:1].upper() + text[1:]


def _preview(text: str, limit: int = 90) -> str:
    first = next((line for line in (text or "").splitlines() if line.strip()), "")
    first = " ".join(re.sub(r"[*_`#>]+|^\s*[-•]\s*", "", first).split())
    return first if len(first) <= limit else first[: limit - 1].rstrip() + "…"


def list_conversations(user_id: int, limit: int = CONVERSATIONS_MAX) -> list[dict]:
    """The customer's conversations, most recently active first (Problem 9: easier to recognize).

    - title: the first message that isn't small talk ("hi", "thanks"), so "hi there!" doesn't name a chat about
      hoodies. Falls back to "Chat about <category>" (from the products shown) or "Quick chat".
    - topics: up to 3 product categories from the cards shown in the conversation, looked up in the catalogue.
    - preview: the start of the latest assistant reply.
    Everything is derived from the existing rows; nothing new is stored.
    """
    from smalltalk import is_small_talk  # local import keeps module import order simple
    import catalogue

    with connect(readonly=True) as conn:
        convs = conn.execute(
            """
            SELECT conversation_id AS id, MIN(created_at) AS started_at, MAX(created_at) AS updated_at,
                   COUNT(*) AS message_count, MAX(id) AS last_id
              FROM chat_messages
             WHERE user_id = ? AND conversation_id IS NOT NULL
             GROUP BY conversation_id
             ORDER BY last_id DESC
             LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
        ids = [c["id"] for c in convs]
        rows = (
            conn.execute(
                f"SELECT conversation_id, role, content, products_json FROM chat_messages "
                f"WHERE user_id = ? AND conversation_id IN ({','.join('?' * len(ids))}) ORDER BY id",
                [user_id, *ids],
            ).fetchall()
            if ids
            else []
        )

    products = catalogue.list_products()
    category_of = {p.product_id: p.category.label for p in products}
    name_of = {p.product_id: p.display_name for p in products}
    per_conv: dict[int, list[sqlite3.Row]] = {}
    for r in rows:
        per_conv.setdefault(r["conversation_id"], []).append(r)

    out = []
    for c in convs:
        msgs = per_conv.get(c["id"], [])
        user_texts = [m["content"] for m in msgs if m["role"] == "user"]
        topics: list[str] = []
        for m in msgs:
            if m["role"] == "assistant":
                for pid in _parse_products(m["products_json"])[0]:
                    label = category_of.get(pid)
                    if label and label not in topics:
                        topics.append(label)
        substantive_index = next((i for i, m in enumerate(msgs) if m["role"] == "user" and not is_small_talk(m["content"])), None)
        substantive = msgs[substantive_index]["content"] if substantive_index is not None else None
        if substantive:
            title = _clean_title(substantive)
            # "Is this available in medium?" asked on a product page: name the product the reply was about.
            if _REFERS_TO_THIS.search(substantive):
                reply = next((m for m in msgs[substantive_index + 1 :] if m["role"] == "assistant"), None)
                shown = _parse_products(reply["products_json"])[0] if reply else []
                if len(shown) == 1 and shown[0] in name_of:
                    title = _clean_title(f"{name_of[shown[0]]}: {substantive}", 70)
        elif topics:
            title = f"Chat about {topics[0].lower()}"
        else:
            title = "Quick chat"
        last_reply = next((m["content"] for m in reversed(msgs) if m["role"] == "assistant"), "")
        out.append(
            {
                "id": c["id"],
                "title": title,
                "topics": topics[:3],
                "preview": _preview(last_reply),
                "started_at": c["started_at"],
                "updated_at": c["updated_at"],
                "message_count": c["message_count"],
            }
        )
    return out


def latest_conversation_id(user_id: int) -> int | None:
    with connect(readonly=True) as conn:
        row = conn.execute(
            "SELECT conversation_id FROM chat_messages WHERE user_id = ? AND conversation_id IS NOT NULL "
            "ORDER BY id DESC LIMIT 1",
            (user_id,),
        ).fetchone()
    return row["conversation_id"] if row else None


# ---------- Messages ----------


def save_exchange(
    user_id: int, conversation_id: int | None, user_text: str, assistant_text: str, cards: list[ProductCard]
) -> tuple[int, int, int]:
    """Save one question and its answer together (one transaction).

    conversation_id None starts a new conversation whose id is the new question's own id. The caller must have
    checked that an existing conversation_id belongs to this user. Returns (conversation_id, user_msg_id, assistant_msg_id).
    """
    products = [{"product_id": c.product_id, "name": c.name, "price": c.price, "size": c.size} for c in cards]
    with connect() as conn:
        u = int(
            conn.execute(
                "INSERT INTO chat_messages (user_id, role, content, products_json, conversation_id) "
                "VALUES (?, 'user', ?, NULL, ?)",
                (user_id, user_text, conversation_id),
            ).lastrowid
        )
        if conversation_id is None:
            conversation_id = u
            conn.execute("UPDATE chat_messages SET conversation_id = ? WHERE id = ? AND user_id = ?", (u, u, user_id))
        a = int(
            conn.execute(
                "INSERT INTO chat_messages (user_id, role, content, products_json, conversation_id) "
                "VALUES (?, 'assistant', ?, ?, ?)",
                (user_id, assistant_text, json.dumps(products), conversation_id),
            ).lastrowid
        )
    return conversation_id, u, a


def _rows(conn: sqlite3.Connection, user_id: int, conversation_id: int, before_id: int | None, limit: int) -> list[sqlite3.Row]:
    sql = (
        "SELECT id, role, content, products_json, created_at FROM chat_messages "
        "WHERE user_id = ? AND conversation_id = ? AND role IN ('user', 'assistant')"
    )
    params: list[object] = [user_id, conversation_id]
    if before_id is not None:
        sql += " AND id < ?"
        params.append(before_id)
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    return list(reversed(conn.execute(sql, params).fetchall()))


def context_turns(
    user_id: int, conversation_id: int, limit: int = CONTEXT_TURNS
) -> tuple[list[ChatTurn], str | None, str | None]:
    """The newest messages of ONE conversation as model context, plus the first/last timestamps they span."""
    with connect(readonly=True) as conn:
        rows = _rows(conn, user_id, conversation_id, None, limit)
    turns = []
    for r in rows:
        ids, _ = _parse_products(r["products_json"]) if r["role"] == "assistant" else ([], None)
        content = (r["content"] or "").strip()[:4000]
        if content:
            turns.append(ChatTurn(role=r["role"], content=content, product_ids=ids))
    first = rows[0]["created_at"] if rows else None
    last = rows[-1]["created_at"] if rows else None
    return turns, first, last


def history_page(user_id: int, conversation_id: int, before_id: int | None, limit: int) -> tuple[list[sqlite3.Row], bool]:
    """One page of a conversation's messages (oldest first) and whether older ones exist."""
    limit = max(1, min(limit, PAGE_MAX))
    with connect(readonly=True) as conn:
        rows = _rows(conn, user_id, conversation_id, before_id, limit + 1)
    has_more = len(rows) > limit
    return (rows[1:] if has_more else rows), has_more
