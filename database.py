"""
database.py — Supabase HTTP API database layer

Uses the supabase-py client (PostgREST under the hood) — no direct Postgres
connection required.

Configuration — set in env or .streamlit/secrets.toml:
    SUPABASE_URL = "https://<project-ref>.supabase.co"
    SUPABASE_KEY = "<anon-or-service-role-key>"

Required tables (create once in the Supabase SQL editor):
    CREATE TABLE orders (
        id            SERIAL PRIMARY KEY,
        customer_name TEXT NOT NULL,
        items         TEXT NOT NULL,
        total         TEXT,
        placed_at     TEXT NOT NULL,
        status        TEXT DEFAULT 'confirmed'
    );

    CREATE TABLE reservations (
        id            SERIAL PRIMARY KEY,
        customer_name TEXT NOT NULL,
        date          TEXT NOT NULL,
        time          TEXT NOT NULL,
        guests        INTEGER,
        placed_at     TEXT NOT NULL,
        status        TEXT DEFAULT 'confirmed'
    );
"""
import json
import os
from datetime import datetime

import streamlit as st
from supabase import create_client, Client

# ---------------------------------------------------------------------------
# Credentials resolution
# ---------------------------------------------------------------------------

def _get_credentials() -> tuple[str, str]:
    """Resolve SUPABASE_URL and SUPABASE_KEY from env or Streamlit secrets."""
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_KEY", "")
    if not url or not key:
        try:
            url = url or st.secrets.get("SUPABASE_URL", "")
            key = key or st.secrets.get("SUPABASE_KEY", "")
        except Exception:
            pass
    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_KEY must be set in env or .streamlit/secrets.toml"
        )
    return url, key

# ---------------------------------------------------------------------------
# Cached client — st.cache_resource keeps one client alive for the process
# ---------------------------------------------------------------------------

@st.cache_resource
def _get_client() -> Client:
    url, key = _get_credentials()
    return create_client(url, key)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def init_db() -> None:
    """No-op: tables must be created in the Supabase SQL editor.

    See the module docstring for the required CREATE TABLE statements.
    """
    pass


def save_order(customer_name: str, items: list, total: str) -> int:
    print(customer_name, items, total)
    """Insert a confirmed order and return its ID."""
    now = datetime.now().isoformat()
    result = (
        _get_client()
        .table("orders")
        .insert(
            {
                "customer_name": customer_name,
                "items": json.dumps(items),
                "total": total,
                "placed_at": now,
                "status": "confirmed",
            }
        )
        .execute()
    )
    return result.data[0]["id"]


def save_reservation(customer_name: str, date: str, time: str, guests: int) -> int:
    print(customer_name, date, time, guests)
    """Insert a confirmed reservation and return its ID."""
    now = datetime.now().isoformat()
    result = (
        _get_client()
        .table("reservations")
        .insert(
            {
                "customer_name": customer_name,
                "date": date,
                "time": time,
                "guests": guests,
                "placed_at": now,
                "status": "confirmed",
            }
        )
        .execute()
    )
    return result.data[0]["id"]


def get_orders(limit: int = 20) -> list[dict]:
    """Return the most recent orders."""
    result = (
        _get_client()
        .table("orders")
        .select("*")
        .order("placed_at", desc=True)
        .limit(limit)
        .execute()
    )
    rows = result.data
    for row in rows:
        if isinstance(row.get("items"), str):
            row["items"] = json.loads(row["items"])
    return rows


def get_reservations(limit: int = 20) -> list[dict]:
    """Return the most recent reservations."""
    result = (
        _get_client()
        .table("reservations")
        .select("*")
        .order("placed_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data
