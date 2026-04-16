import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "restaurant.db"


def init_db() -> None:
    """Create tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            items       TEXT NOT NULL,
            total       TEXT,
            placed_at   TEXT NOT NULL,
            status      TEXT DEFAULT 'confirmed'
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            date        TEXT NOT NULL,
            time        TEXT NOT NULL,
            guests      INTEGER,
            placed_at   TEXT NOT NULL,
            status      TEXT DEFAULT 'confirmed'
        )
    """)
    conn.commit()
    conn.close()


def save_order(customer_name: str, items: list, total: str) -> int:
    """Insert a confirmed order and return its ID."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO orders (customer_name, items, total, placed_at) VALUES (?, ?, ?, ?)",
        (customer_name, json.dumps(items), total, datetime.now().isoformat()),
    )
    order_id = c.lastrowid
    conn.commit()
    conn.close()
    return order_id


def save_reservation(customer_name: str, date: str, time: str, guests: int) -> int:
    """Insert a confirmed reservation and return its ID."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO reservations (customer_name, date, time, guests, placed_at) VALUES (?, ?, ?, ?, ?)",
        (customer_name, date, time, guests, datetime.now().isoformat()),
    )
    res_id = c.lastrowid
    conn.commit()
    conn.close()
    return res_id


def get_orders(limit: int = 20) -> list[dict]:
    """Return the most recent orders."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM orders ORDER BY placed_at DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    for row in rows:
        row["items"] = json.loads(row["items"])
    return rows


def get_reservations(limit: int = 20) -> list[dict]:
    """Return the most recent reservations."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM reservations ORDER BY placed_at DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows
