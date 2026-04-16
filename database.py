"""
database.py — dual-mode database layer

Locally  : uses SQLite (no config needed).
Production: uses PostgreSQL when DATABASE_URL is set in environment / Streamlit secrets.
           Recommended free-tier host: Supabase (https://supabase.com).
           Add the connection string to Streamlit Cloud → Settings → Secrets:
               DATABASE_URL = "postgresql://user:password@host:5432/dbname"
"""
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Backend selection
# ---------------------------------------------------------------------------

def _get_database_url() -> str:
    """Return DATABASE_URL from env or Streamlit secrets, empty string if absent."""
    url = os.getenv("DATABASE_URL", "")
    # howhardshoulditbe
    if not url:
        try:
            import streamlit as st
            url = st.secrets.get("DATABASE_URL", "")
        except Exception:
            pass
    return url


USE_POSTGRES = bool(_get_database_url())
SQLITE_PATH = Path(__file__).parent / "restaurant.db"

# ---------------------------------------------------------------------------
# Connection helpers
# ---------------------------------------------------------------------------

@contextmanager
def _pg_conn():
    import psycopg2
    import psycopg2.extras
    conn = psycopg2.connect(_get_database_url())
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@contextmanager
def _sqlite_conn():
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _conn():
    return _pg_conn() if USE_POSTGRES else _sqlite_conn()

# ---------------------------------------------------------------------------
# Schema — PostgreSQL uses SERIAL + %s placeholders; SQLite uses AUTOINCREMENT + ?
# ---------------------------------------------------------------------------

_ORDERS_DDL_PG = """
    CREATE TABLE IF NOT EXISTS orders (
        id            SERIAL PRIMARY KEY,
        customer_name TEXT        NOT NULL,
        items         TEXT        NOT NULL,
        total         TEXT,
        placed_at     TEXT        NOT NULL,
        status        TEXT        DEFAULT 'confirmed'
    )
"""

_RESERVATIONS_DDL_PG = """
    CREATE TABLE IF NOT EXISTS reservations (
        id            SERIAL PRIMARY KEY,
        customer_name TEXT    NOT NULL,
        date          TEXT    NOT NULL,
        time          TEXT    NOT NULL,
        guests        INTEGER,
        placed_at     TEXT    NOT NULL,
        status        TEXT    DEFAULT 'confirmed'
    )
"""

_ORDERS_DDL_SQLITE = """
    CREATE TABLE IF NOT EXISTS orders (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT        NOT NULL,
        items         TEXT        NOT NULL,
        total         TEXT,
        placed_at     TEXT        NOT NULL,
        status        TEXT        DEFAULT 'confirmed'
    )
"""

_RESERVATIONS_DDL_SQLITE = """
    CREATE TABLE IF NOT EXISTS reservations (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT    NOT NULL,
        date          TEXT    NOT NULL,
        time          TEXT    NOT NULL,
        guests        INTEGER,
        placed_at     TEXT    NOT NULL,
        status        TEXT    DEFAULT 'confirmed'
    )
"""

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def init_db() -> None:
    """Create tables if they don't exist."""
    if USE_POSTGRES:
        with _pg_conn() as conn:
            c = conn.cursor()
            c.execute(_ORDERS_DDL_PG)
            c.execute(_RESERVATIONS_DDL_PG)
    else:
        with _sqlite_conn() as conn:
            c = conn.cursor()
            c.execute(_ORDERS_DDL_SQLITE)
            c.execute(_RESERVATIONS_DDL_SQLITE)


def save_order(customer_name: str, items: list, total: str) -> int:
    """Insert a confirmed order and return its ID."""
    now = datetime.now().isoformat()
    items_json = json.dumps(items)
    if USE_POSTGRES:
        with _pg_conn() as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO orders (customer_name, items, total, placed_at) "
                "VALUES (%s, %s, %s, %s) RETURNING id",
                (customer_name, items_json, total, now),
            )
            return c.fetchone()[0]
    else:
        with _sqlite_conn() as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO orders (customer_name, items, total, placed_at) VALUES (?, ?, ?, ?)",
                (customer_name, items_json, total, now),
            )
            return c.lastrowid


def save_reservation(customer_name: str, date: str, time: str, guests: int) -> int:
    """Insert a confirmed reservation and return its ID."""
    now = datetime.now().isoformat()
    if USE_POSTGRES:
        with _pg_conn() as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO reservations (customer_name, date, time, guests, placed_at) "
                "VALUES (%s, %s, %s, %s, %s) RETURNING id",
                (customer_name, date, time, guests, now),
            )
            return c.fetchone()[0]
    else:
        with _sqlite_conn() as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO reservations (customer_name, date, time, guests, placed_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (customer_name, date, time, guests, now),
            )
            return c.lastrowid


def get_orders(limit: int = 20) -> list[dict]:
    """Return the most recent orders."""
    if USE_POSTGRES:
        import psycopg2.extras
        with _pg_conn() as conn:
            c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            c.execute("SELECT * FROM orders ORDER BY placed_at DESC LIMIT %s", (limit,))
            rows = [dict(r) for r in c.fetchall()]
    else:
        with _sqlite_conn() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM orders ORDER BY placed_at DESC LIMIT ?", (limit,))
            rows = [dict(r) for r in c.fetchall()]
    for row in rows:
        if isinstance(row.get("items"), str):
            row["items"] = json.loads(row["items"])
    return rows


def get_reservations(limit: int = 20) -> list[dict]:
    """Return the most recent reservations."""
    if USE_POSTGRES:
        import psycopg2.extras
        with _pg_conn() as conn:
            c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            c.execute("SELECT * FROM reservations ORDER BY placed_at DESC LIMIT %s", (limit,))
            return [dict(r) for r in c.fetchall()]
    else:
        with _sqlite_conn() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM reservations ORDER BY placed_at DESC LIMIT ?", (limit,))
            return [dict(r) for r in c.fetchall()]
