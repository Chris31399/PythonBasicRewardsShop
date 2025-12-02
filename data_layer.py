# data_layer.py
# This handles all database interactions: creating tables, seeding data, loading customers and rewards, updating points, inserting orders.
import sqlite3
from pathlib import Path
from datetime import datetime

DB_FILE = Path("rewards_shop.db")


def get_connection():
    """Return a new SQLite connection with foreign keys enabled."""
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    """Create tables if they don't exist and seed some sample data."""
    conn = get_connection()
    cur = conn.cursor()

    # Create customers table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            points INTEGER NOT NULL
        );
    """)

    # Create rewards table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS rewards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            cost INTEGER NOT NULL
        );
    """)

    # Create orders table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            reward_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            points_spent INTEGER NOT NULL,
            order_time TEXT NOT NULL,
            FOREIGN KEY(customer_id) REFERENCES customers(id),
            FOREIGN KEY(reward_id) REFERENCES rewards(id)
        );
    """)

    # Seed customers if table empty
    cur.execute("SELECT COUNT(*) FROM customers;")
    (count_customers,) = cur.fetchone()
    if count_customers == 0:
        cur.executemany("""
            INSERT INTO customers (name, email, points)
            VALUES (?, ?, ?);
        """, [
            ("Alice", "alice@example.com", 100),
            ("Bob", "bob@example.com", 60),
            ("Chris", "chris@example.com", 250),
        ])

    # Seed rewards if table empty
    cur.execute("SELECT COUNT(*) FROM rewards;")
    (count_rewards,) = cur.fetchone()
    if count_rewards == 0:
        cur.executemany("""
            INSERT INTO rewards (name, cost)
            VALUES (?, ?);
        """, [
            ("Booster Pack", 20),
            ("Playmat", 50),
            ("Sleeves", 15),
            ("Starter Deck", 40),
        ])

    conn.commit()
    conn.close()


# ---------- Basic CRUD helper functions ----------

def get_all_customers():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, email, points FROM customers ORDER BY name;")
    rows = cur.fetchall()
    conn.close()
    return rows


def get_all_rewards():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, cost FROM rewards ORDER BY cost;")
    rows = cur.fetchall()
    conn.close()
    return rows


def get_customer_by_id(customer_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, name, email, points FROM customers WHERE id = ?;",
        (customer_id,)
    )
    row = cur.fetchone()
    conn.close()
    return row


def get_reward_by_id(reward_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, name, cost FROM rewards WHERE id = ?;",
        (reward_id,)
    )
    row = cur.fetchone()
    conn.close()
    return row


def update_customer_points(customer_id: int, new_points: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE customers SET points = ? WHERE id = ?;",
        (new_points, customer_id)
    )
    conn.commit()
    conn.close()


def insert_order(customer_id: int, reward_id: int,
                 quantity: int, points_spent: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO orders (customer_id, reward_id, quantity, points_spent, order_time)
        VALUES (?, ?, ?, ?, ?);
    """, (customer_id, reward_id, quantity, points_spent, datetime.now().isoformat()))
    conn.commit()
    conn.close()
