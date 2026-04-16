"""
database.py — Streamlit-native database layer

Uses SQLAlchemy + st.cache_resource (Streamlit's recommended pattern for
shared resources). The engine is created once and reused across all reruns.

Local dev  : SQLite — zero config, auto-detected.
Production : PostgreSQL — set DATABASE_URL in Streamlit Cloud → Settings → Secrets:
               DATABASE_URL = "postgresql://user:password@host:5432/dbname"
             Recommended free host: Supabase (https://supabase.com)

Local .streamlit/secrets.toml example:
    DATABASE_URL = "postgresql+psycopg2://user:password@host:5432/dbname"
"""
import json
import os
from datetime import datetime
from pathlib import Path

import streamlit as st
from sqlalchemy import text

SQLITE_PATH = Path(__file__).parent / "restaurant.db"

# ---------------------------------------------------------------------------
# URL resolution
# ---------------------------------------------------------------------------

def _get_database_url() -> str:
    """Resolve DATABASE_URL: env → Streamlit secrets → local SQLite fallback."""
    url = os.getenv("DATABASE_URL", "")
    if not url:
        try:
            url = st.secrets.get("DATABASE_URL", "")
        except Exception:
            pass
    if not url:
        url = f"sqlite:///{SQLITE_PATH}"
    # SQLAlchemy requires the psycopg2 dialect prefix for Postgres URLs
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url

# ---------------------------------------------------------------------------
# Cached engine — st.cache_resource keeps one engine alive for the process
# ---------------------------------------------------------------------------

@st.cache_resource
def _get_engine():
    from sqlalchemy import create_engine
    url = _get_database_url()
    extra = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, pool_pre_ping=True, connect_args=extra)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def init_db() -> None:
    """Create tables if they don't exist (dialect-aware)."""
    engine = _get_engine()
    pg = engine.dialect.name == "postgresql"
    id_col = "SERIAL PRIMARY KEY" if pg else "INTEGER PRIMARY KEY AUTOINCREMENT"

    with engine.begin() as conn:
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS orders (
                id            {id_col},
                customer_name TEXT NOT NULL,
                items         TEXT NOT NULL,
                total         TEXT,
                placed_at     TEXT NOT NULL,
                status        TEXT DEFAULT 'confirmed'
            )
        """))
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS reservations (
                id            {id_col},
                customer_name TEXT NOT NULL,
                date          TEXT NOT NULL,
                time          TEXT NOT NULL,
                guests        INTEGER,
                placed_at     TEXT NOT NULL,
                status        TEXT DEFAULT 'confirmed'
            )
        """))


def save_order(customer_name: str, items: list, total: str) -> int:
    """Insert a confirmed order and return its ID."""
    now = datetime.now().isoformat()
    with _get_engine().begin() as conn:
        result = conn.execute(
            text(
                "INSERT INTO orders (customer_name, items, total, placed_at) "
                "VALUES (:name, :items, :total, :now) RETURNING id"
            ),
            {"name": customer_name, "items": json.dumps(items), "total": total, "now": now},
        )
        return result.fetchone()[0]


def save_reservation(customer_name: str, date: str, time: str, guests: int) -> int:
    """Insert a confirmed reservation and return its ID."""
    now = datetime.now().isoformat()
    with _get_engine().begin() as conn:
        result = conn.execute(
            text(
                "INSERT INTO reservations (customer_name, date, time, guests, placed_at) "
                "VALUES (:name, :date, :time, :guests, :now) RETURNING id"
            ),
            {"name": customer_name, "date": date, "time": time, "guests": guests, "now": now},
        )
        return result.fetchone()[0]


def get_orders(limit: int = 20) -> list[dict]:
    """Return the most recent orders."""
    with _get_engine().connect() as conn:
        result = conn.execute(
            text("SELECT * FROM orders ORDER BY placed_at DESC LIMIT :limit"),
            {"limit": limit},
        )
        rows = [dict(r._mapping) for r in result.fetchall()]
    for row in rows:
        if isinstance(row.get("items"), str):
            row["items"] = json.loads(row["items"])
    return rows


def get_reservations(limit: int = 20) -> list[dict]:
    """Return the most recent reservations."""
    with _get_engine().connect() as conn:
        result = conn.execute(
            text("SELECT * FROM reservations ORDER BY placed_at DESC LIMIT :limit"),
            {"limit": limit},
        )
        return [dict(r._mapping) for r in result.fetchall()]
