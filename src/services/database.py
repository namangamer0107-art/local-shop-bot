import sqlite3
import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

if os.environ.get("VERCEL"):
    DB_DIR = "/tmp/data"
    DB_PATH = "/tmp/data/local_bot.db"
else:
    DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
    DB_PATH = os.path.join(DB_DIR, "local_bot.db")

class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS appointments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenant_id TEXT NOT NULL,
                    customer_phone TEXT NOT NULL,
                    customer_name TEXT NOT NULL,
                    service TEXT NOT NULL,
                    slot TEXT NOT NULL,
                    status TEXT DEFAULT 'confirmed',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenant_id TEXT NOT NULL,
                    customer_phone TEXT NOT NULL,
                    customer_name TEXT,
                    items_json TEXT NOT NULL,
                    total_amount TEXT,
                    delivery_address TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_states (
                    customer_phone TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    step TEXT DEFAULT 'idle',
                    data_json TEXT DEFAULT '{}',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    customer_phone TEXT NOT NULL,
                    tenant_id TEXT NOT NULL,
                    customer_name TEXT DEFAULT 'Valued Customer',
                    opt_in INTEGER DEFAULT 1,
                    last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (customer_phone, tenant_id)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS broadcasts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenant_id TEXT NOT NULL,
                    message_text TEXT NOT NULL,
                    recipients_count INTEGER NOT NULL,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Live Activity Logs for Super Admin oversight
            conn.execute("""
                CREATE TABLE IF NOT EXISTS activity_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenant_id TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    details TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def log_activity(self, tenant_id: str, actor: str, action_type: str, details: str):
        """Logs user and shop actions for Super Admin audit trail."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO activity_logs (tenant_id, actor, action_type, details)
                VALUES (?, ?, ?, ?)
            """, (tenant_id, actor, action_type, details))
            conn.commit()

    def list_activities(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM activity_logs ORDER BY id DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def register_customer(self, customer_phone: str, tenant_id: str, customer_name: str = ""):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO customers (customer_phone, tenant_id, customer_name, last_interaction)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(customer_phone, tenant_id) DO UPDATE SET
                    customer_name = CASE WHEN excluded.customer_name != '' THEN excluded.customer_name ELSE customers.customer_name END,
                    last_interaction = CURRENT_TIMESTAMP
            """, (customer_phone, tenant_id, customer_name))
            conn.commit()

    def get_broadcast_subscribers(self, tenant_id: str) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT customer_phone, customer_name FROM customers WHERE tenant_id = ? AND opt_in = 1", (tenant_id,))
            return [dict(row) for row in cursor.fetchall()]

    def record_broadcast(self, tenant_id: str, message_text: str, recipients_count: int) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO broadcasts (tenant_id, message_text, recipients_count)
                VALUES (?, ?, ?)
            """, (tenant_id, message_text, recipients_count))
            conn.commit()
            return cursor.lastrowid

    def list_broadcasts(self, tenant_id: str) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM broadcasts WHERE tenant_id = ? ORDER BY id DESC", (tenant_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_user_state(self, customer_phone: str, tenant_id: str) -> Dict[str, Any]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT step, data_json FROM user_states WHERE customer_phone = ?", (customer_phone,))
            row = cursor.fetchone()
            if row:
                try:
                    return {"step": row["step"], "data": json.loads(row["data_json"])}
                except Exception:
                    return {"step": row["step"], "data": {}}
            return {"step": "idle", "data": {}}

    def save_user_state(self, customer_phone: str, tenant_id: str, step: str, data: Dict[str, Any]):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_states (customer_phone, tenant_id, step, data_json, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(customer_phone) DO UPDATE SET
                    tenant_id = excluded.tenant_id,
                    step = excluded.step,
                    data_json = excluded.data_json,
                    updated_at = CURRENT_TIMESTAMP
            """, (customer_phone, tenant_id, step, json.dumps(data)))
            conn.commit()

    def add_appointment(self, tenant_id: str, customer_phone: str, customer_name: str, service: str, slot: str) -> int:
        self.register_customer(customer_phone, tenant_id, customer_name)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO appointments (tenant_id, customer_phone, customer_name, service, slot)
                VALUES (?, ?, ?, ?, ?)
            """, (tenant_id, customer_phone, customer_name, service, slot))
            conn.commit()
            return cursor.lastrowid

    def list_appointments(self, tenant_id: str) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM appointments WHERE tenant_id = ? ORDER BY id DESC", (tenant_id,))
            return [dict(row) for row in cursor.fetchall()]

    def add_order(self, tenant_id: str, customer_phone: str, items: List[Dict[str, Any]], total: str, customer_name: str = "", address: str = "") -> int:
        self.register_customer(customer_phone, tenant_id, customer_name)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO orders (tenant_id, customer_phone, customer_name, items_json, total_amount, delivery_address)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (tenant_id, customer_phone, customer_name, json.dumps(items), total, address))
            conn.commit()
            return cursor.lastrowid

    def list_orders(self, tenant_id: str) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM orders WHERE tenant_id = ? ORDER BY id DESC", (tenant_id,))
            res = []
            for row in cursor.fetchall():
                d = dict(row)
                d["items"] = json.loads(d["items_json"])
                res.append(d)
            return res

db = Database()
