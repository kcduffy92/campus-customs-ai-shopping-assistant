"""SQLite connection handling. Every module that touches the database goes through `connect()`.

- Opens the existing file only (mode=rw): a missing database raises an error instead of silently creating an empty one.
- Turns on foreign-key enforcement, which SQLite leaves off by default (see output/design.md, section 1.7).
- Returns rows as sqlite3.Row so columns can be read by name.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

from config import DB_PATH


class DatabaseUnavailable(RuntimeError):
    pass


@contextmanager
def connect(readonly: bool = False) -> Iterator[sqlite3.Connection]:
    if not DB_PATH.is_file():
        raise DatabaseUnavailable(f"Database not found at {DB_PATH}. Unzip the course data into hw4/data/.")
    mode = "ro" if readonly else "rw"
    conn = sqlite3.connect(f"{DB_PATH.as_uri()}?mode={mode}", uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        if not readonly:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
