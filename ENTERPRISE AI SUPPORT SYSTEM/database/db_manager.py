import sqlite3
import os
from datetime import datetime

# ==========================================
# DATABASE PATH
# ==========================================

DB_PATH = os.path.join(
    os.path.dirname(__file__),
    "enterprise_support.db"
)

DOCUMENTS_DIR = os.path.join(
    os.path.dirname(__file__),
    "..",
    "data",
    "documents"
)

# ==========================================
# DATABASE CONNECTION
# ==========================================

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ==========================================
# INITIALIZE DATABASE
# ==========================================

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            plan TEXT,
            account_balance TEXT,
            status TEXT,
            password_hash TEXT,
            role TEXT NOT NULL DEFAULT 'CUSTOMER',
            created_at TEXT
        )
    """)

    # 2. Tickets Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            issue TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'OPEN',
            priority TEXT NOT NULL DEFAULT 'MEDIUM',
            assigned_to TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    # 3. Chat Messages Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            agent_name TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    # Seed Default Accounts with working Bcrypt passwords
    # password123 hash: $2b$12$DCbbVcq2hYg7/3wEWwiQmusnf3yOMmEH9PhNaN0wtDbrYoaHlTUL.
    # admin123 hash: $2b$12$ZQq0NL5gyVks4Zq3vF874Ow9hwWtIgssCQPy0EMDOpdG8jz7IYuMW
    default_users = [
        (
            "USR101",
            "Alex Johnson",
            "Enterprise Tier",
            "$1,200 / mo",
            "Active",
            "$2b$12$DCbbVcq2hYg7/3wEWwiQmusnf3yOMmEH9PhNaN0wtDbrYoaHlTUL.",
            "ADMIN"
        ),
        (
            "ADMIN01",
            "System Administrator",
            "Executive Suite",
            "$0.00",
            "Active",
            "$2b$12$ZQq0NL5gyVks4Zq3vF874Ow9hwWtIgssCQPy0EMDOpdG8jz7IYuMW",
            "ADMIN"
        ),
        (
            "USR102",
            "Sam Lee",
            "Free Pro Plan",
            "$0.00 (Overdue)",
            "Pending Payment",
            "$2b$12$DCbbVcq2hYg7/3wEWwiQmusnf3yOMmEH9PhNaN0wtDbrYoaHlTUL.",
            "CUSTOMER"
        ),
        (
            "USR103",
            "SBI Customer",
            "Savings Account",
            "$72.00 (Active)",
            "Active",
            "$2b$12$DCbbVcq2hYg7/3wEWwiQmusnf3yOMmEH9PhNaN0wtDbrYoaHlTUL.",
            "CUSTOMER"
        )
    ]

    now_iso = datetime.utcnow().isoformat()
    for u in default_users:
        cursor.execute("""
            INSERT INTO users (
                user_id, name, plan, account_balance, status,
                password_hash, role, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                role = excluded.role,
                name = excluded.name,
                plan = excluded.plan
        """, (u[0], u[1], u[2], u[3], u[4], u[5], u[6], now_iso))

    conn.commit()
    conn.close()

# ==========================================
# USER OPERATIONS
# ==========================================

def get_user_details(user_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT user_id, name, plan, account_balance, status,
               password_hash, role, created_at
        FROM users
        WHERE user_id = ?
    """, (user_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return dict(result)
    return None

def get_all_users():
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

def update_user_password(user_id: str, password_hash: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users
        SET password_hash = ?
        WHERE user_id = ?
    """, (password_hash, user_id))
    updated = cursor.rowcount
    conn.commit()
    conn.close()
    return updated > 0

def create_customer_user(user_id: str, name: str, password_hash: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if cursor.fetchone():
        conn.close()
        raise ValueError("User ID already exists.")

    cursor.execute("""
        INSERT INTO users (
            user_id, name, plan, account_balance, status,
            password_hash, role, created_at
        )
        VALUES (?, ?, 'Free Plan', '$0.00', 'Active', ?, 'CUSTOMER', ?)
    """, (user_id, name, password_hash, datetime.utcnow().isoformat()))

    conn.commit()
    conn.close()
    return True

def update_user_role(user_id: str, role: str):
    allowed_roles = {"CUSTOMER", "ADMIN"}
    role = role.upper()

    if role not in allowed_roles:
        raise ValueError(f"Invalid role: {role}")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET role = ? WHERE user_id = ?",
        (role, user_id)
    )
    updated = cursor.rowcount
    conn.commit()
    conn.close()
    return updated > 0

# ==========================================
# TICKET OPERATIONS
# ==========================================

def create_ticket(
    user_id: str,
    issue_description: str,
    priority: str = "MEDIUM"
):
    allowed_priorities = {"LOW", "MEDIUM", "HIGH", "URGENT"}
    priority = priority.upper()

    if priority == "CRITICAL":
        priority = "URGENT"

    if priority not in allowed_priorities:
        raise ValueError(f"Invalid ticket priority: {priority}")

    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()

    cursor.execute("""
        INSERT INTO tickets (
            user_id, issue, status, priority,
            assigned_to, created_at, updated_at
        )
        VALUES (?, ?, 'OPEN', ?, 'Support AI Team', ?, ?)
    """, (user_id, issue_description, priority, now, now))

    ticket_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return ticket_id

def get_all_tickets():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ticket_id, user_id, issue, status, priority,
               assigned_to, created_at, updated_at
        FROM tickets
        ORDER BY ticket_id DESC
    """)
    tickets = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return tickets

def get_user_tickets(user_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ticket_id, user_id, issue, status, priority,
               assigned_to, created_at, updated_at
        FROM tickets
        WHERE user_id = ?
        ORDER BY ticket_id DESC
    """, (user_id,))
    tickets = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return tickets

def update_ticket_status(ticket_id: int, status: str):
    status = status.upper()

    if status == "PENDING":
        status = "IN_PROGRESS"

    allowed_statuses = {
        "OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"
    }

    if status not in allowed_statuses:
        raise ValueError(f"Invalid ticket status: {status}")

    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()

    cursor.execute("""
        UPDATE tickets
        SET status = ?, updated_at = ?
        WHERE ticket_id = ?
    """, (status, now, ticket_id))

    updated = cursor.rowcount
    conn.commit()
    conn.close()
    return updated

def update_ticket_priority(ticket_id: int, priority: str):
    priority = priority.upper()

    if priority == "CRITICAL":
        priority = "URGENT"

    allowed_priorities = {"LOW", "MEDIUM", "HIGH", "URGENT"}

    if priority not in allowed_priorities:
        raise ValueError(f"Invalid ticket priority: {priority}")

    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()

    cursor.execute("""
        UPDATE tickets
        SET priority = ?, updated_at = ?
        WHERE ticket_id = ?
    """, (priority, now, ticket_id))

    updated = cursor.rowcount
    conn.commit()
    conn.close()
    return updated

def get_ticket_stats(user_id: str = None):
    conn = get_connection()
    cursor = conn.cursor()

    if user_id:
        cursor.execute(
            "SELECT status, count(*) FROM tickets "
            "WHERE user_id = ? GROUP BY status",
            (user_id,)
        )
        rows = cursor.fetchall()

        cursor.execute(
            "SELECT count(*) FROM tickets WHERE user_id = ?",
            (user_id,)
        )
        total = cursor.fetchone()[0]
    else:
        cursor.execute(
            "SELECT status, count(*) FROM tickets GROUP BY status"
        )
        rows = cursor.fetchall()

        cursor.execute("SELECT count(*) FROM tickets")
        total = cursor.fetchone()[0]

    status_counts = {
        "OPEN": 0,
        "IN_PROGRESS": 0,
        "RESOLVED": 0,
        "CLOSED": 0
    }

    for row in rows:
        st = str(row[0]).upper()
        if st in status_counts:
            status_counts[st] = row[1]

    conn.close()

    return {
        "total": total,
        "open": status_counts["OPEN"],
        "in_progress": status_counts["IN_PROGRESS"],
        "resolved": status_counts["RESOLVED"],
        "closed": status_counts["CLOSED"],
        "pending_or_active": (
            status_counts["OPEN"] +
            status_counts["IN_PROGRESS"]
        )
    }

# ==========================================
# CHAT PERSISTENCE OPERATIONS
# ==========================================

def save_chat_message(
    user_id: str,
    role: str,
    content: str,
    agent_name: str = None
):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()

    cursor.execute("""
        INSERT INTO chat_messages (
            user_id, role, content, agent_name, created_at
        )
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, role, content, agent_name, now))

    msg_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return msg_id

def get_user_chat_history(user_id: str, limit: int = 50):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, user_id, role, content, agent_name, created_at
        FROM chat_messages
        WHERE user_id = ?
        ORDER BY id ASC
        LIMIT ?
    """, (user_id, limit))

    history = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return history

def get_chat_count(user_id: str = None):
    conn = get_connection()
    cursor = conn.cursor()

    if user_id:
        cursor.execute(
            "SELECT count(*) FROM chat_messages "
            "WHERE user_id = ? AND role = 'user'",
            (user_id,)
        )
    else:
        cursor.execute(
            "SELECT count(*) FROM chat_messages WHERE role = 'user'"
        )

    count = cursor.fetchone()[0]
    conn.close()
    return count

def clear_user_chat_history(user_id: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM chat_messages WHERE user_id = ?",
        (user_id,)
    )

    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted

def delete_ticket(ticket_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM tickets WHERE ticket_id = ?",
        (ticket_id,)
    )

    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted > 0

# ==========================================
# KNOWLEDGE BASE DOCUMENT METADATA
# ==========================================

def get_knowledge_documents():
    docs = []

    if os.path.exists(DOCUMENTS_DIR):
        for fname in sorted(os.listdir(DOCUMENTS_DIR)):
            if fname.lower().endswith(".pdf"):
                fpath = os.path.join(DOCUMENTS_DIR, fname)
                size_kb = round(
                    os.path.getsize(fpath) / 1024,
                    1
                )
                mtime = datetime.fromtimestamp(
                    os.path.getmtime(fpath)
                ).strftime("%Y-%m-%d %H:%M")

                docs.append({
                    "filename": fname,
                    "size_kb": size_kb,
                    "last_modified": mtime,
                    "status": "INDEXED",
                    "type": "PDF Security / Policy Document"
                })

    return docs

# ==========================================
# INITIALIZATION
# ==========================================

if __name__ == "__main__":
    init_db()
    print(
        "Database initialized successfully "
        "with updated tables and seed accounts!"
    )
