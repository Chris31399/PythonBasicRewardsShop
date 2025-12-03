# data_layer.py
# Handles all database interactions: creating tables, seeding data,
# loading customers and rewards, updating points, inserting orders,
# and basic admin CRUD for customers/rewards.

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

    # Create orders table (without assuming status exists yet)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            reward_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            points_spent INTEGER NOT NULL,
            order_time TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            FOREIGN KEY(customer_id) REFERENCES customers(id),
            FOREIGN KEY(reward_id) REFERENCES rewards(id)
        );
    """)

    # --- Migration safety: ensure 'status' column exists even on older DBs ---
    cur.execute("PRAGMA table_info(orders);")
    cols = cur.fetchall()  # (cid, name, type, notnull, dflt_value, pk)
    col_names = {c[1] for c in cols}
    if "status" not in col_names:
        cur.execute("ALTER TABLE orders ADD COLUMN status TEXT NOT NULL DEFAULT 'pending';")

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
        (customer_id,),
    )
    row = cur.fetchone()
    conn.close()
    return row

def get_reward_by_id(reward_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, name, cost FROM rewards WHERE id = ?;",
        (reward_id,),
    )
    row = cur.fetchone()
    conn.close()
    return row

def update_customer_points(customer_id: int, new_points: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE customers SET points = ? WHERE id = ?;",
        (new_points, customer_id),
    )
    conn.commit()
    conn.close()

def insert_order(customer_id: int, reward_id: int,
                 quantity: int, points_spent: int, status: str = "pending"):
    """
    Insert a new order. Status defaults to 'pending'.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO orders (customer_id, reward_id, quantity, points_spent, order_time, status)
        VALUES (?, ?, ?, ?, ?, ?);
    """, (customer_id, reward_id, quantity, points_spent, datetime.now().isoformat(), status))
    conn.commit()
    conn.close()

def get_order_by_id(order_id: int):
    """
    Return a single order row or None.
    Columns: id, customer_id, reward_id, quantity, points_spent, order_time, status
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, customer_id, reward_id, quantity, points_spent, order_time, status
        FROM orders
        WHERE id = ?;
    """, (order_id,))
    row = cur.fetchone()
    conn.close()
    return row

def update_order_status(order_id: int, new_status: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE orders SET status = ? WHERE id = ?;",
        (new_status, order_id),
    )
    conn.commit()
    conn.close()

def get_pending_orders_with_details():
    """
    Return pending orders joined with customer & reward names, newest first-ish.
    Columns:
      id, customer_id, customer_name,
      reward_id, reward_name,
      quantity, points_spent, status, order_time
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            o.id,
            o.customer_id,
            c.name AS customer_name,
            o.reward_id,
            r.name AS reward_name,
            o.quantity,
            o.points_spent,
            o.status,
            o.order_time
        FROM orders AS o
        JOIN customers AS c ON o.customer_id = c.id
        JOIN rewards   AS r ON o.reward_id   = r.id
        WHERE o.status = 'pending'
        ORDER BY o.order_time ASC;
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

# ---------- Admin CRUD for customers and rewards ----------
def insert_customer(name: str, email: str, points: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO customers (name, email, points) VALUES (?, ?, ?);",
        (name, email, points),
    )
    conn.commit()
    conn.close()

def delete_customer(customer_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM customers WHERE id = ?;", (customer_id,))
    conn.commit()
    conn.close()

def insert_reward(name: str, cost: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO rewards (name, cost) VALUES (?, ?);",
        (name, cost),
    )
    conn.commit()
    conn.close()

def delete_reward(reward_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM rewards WHERE id = ?;", (reward_id,))
    conn.commit()
    conn.close()
