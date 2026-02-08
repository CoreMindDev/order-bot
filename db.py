import sqlite3
from datetime import datetime

def init_db():
    with sqlite3.connect("orders.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            name TEXT,
            task TEXT,
            status TEXT DEFAULT 'new',
            created_at TEXT
        )
        """)
        conn.commit()

def save_order(user_id: int, username: str, name: str, task: str) -> int:
    with sqlite3.connect("orders.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO orders (user_id, username, name, task, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                username,
                name,
                task,
                datetime.now().strftime("%Y-%m-%d %H:%M")
            )
        )
        conn.commit()
        return cursor.lastrowid

def get_orders(status: str | None = None):
    with sqlite3.connect("orders.db") as conn:
        cursor = conn.cursor()
        if status:
            cursor.execute(
                "SELECT id, user_id, username, name, task, status FROM orders WHERE status = ?",
                (status,)
            )
        else:
            cursor.execute(
                "SELECT id, user_id, username, name, task, status FROM orders"
            )
        return cursor.fetchall()
    
def get_new_orders():
    return get_orders("new")

def set_in_progress(order_id: int) -> bool:
    with sqlite3.connect("orders.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE orders SET status = 'in_progress' WHERE id = ?",
            (order_id,)
        )
        conn.commit()
        return cursor.rowcount > 0
        
def set_done(order_id: int) -> bool:
    with sqlite3.connect("orders.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE orders SET status = 'done' WHERE id = ?",
            (order_id,)
        )
        conn.commit()
        return cursor.rowcount > 0
    
def get_order(order_id: int):
    with sqlite3.connect("orders.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id, username, name, task, status FROM orders WHERE id = ?",
            (order_id,)
        )
        return cursor.fetchone()