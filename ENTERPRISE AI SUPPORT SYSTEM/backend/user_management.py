from datetime import datetime
from database.db_manager import get_connection
from backend.auth import hash_password


def get_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT user_id, name, plan, account_balance, status, role, created_at
        FROM users
        ORDER BY created_at DESC
    """)
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return users


def get_user(user_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT user_id, name, plan, account_balance, status, role, created_at
        FROM users
        WHERE user_id = ?
    """, (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_user_status(user_id: str, status: str):
    status = status.strip().title()
    if status not in {"Active", "Blocked"}:
        raise ValueError("Status must be Active or Blocked.")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET status = ? WHERE user_id = ?",
        (status, user_id)
    )
    updated = cursor.rowcount
    conn.commit()
    conn.close()
    return updated > 0


def create_admin(user_id: str, name: str, password: str,
                 plan: str = "Admin Enterprise"):
    user_id = user_id.strip()
    name = name.strip()
    password = password.strip()
    plan = plan.strip() or "Admin Enterprise"

    if not user_id:
        raise ValueError("Admin ID is required.")
    if not name:
        raise ValueError("Admin name is required.")
    if len(password) < 6:
        raise ValueError("Password must contain at least 6 characters.")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id FROM users WHERE user_id = ?",
        (user_id,)
    )

    if cursor.fetchone():
        conn.close()
        raise ValueError("User ID already exists.")

    cursor.execute("""
        INSERT INTO users (
            user_id, name, plan, account_balance, status,
            password_hash, role, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id, name, plan, "$0.00", "Active",
        hash_password(password), "ADMIN",
        datetime.utcnow().isoformat()
    ))

    conn.commit()
    conn.close()
    return True
