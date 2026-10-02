import sqlite3
import os
from datetime import datetime


DB_PATH = os.path.join(
    os.path.dirname(__file__),
    "enterprise_support.db"
)


def migrate_tickets():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check existing columns
    cursor.execute("PRAGMA table_info(tickets)")
    columns = [row[1] for row in cursor.fetchall()]

    print("Existing columns:", columns)

    # Add priority
    if "priority" not in columns:
        cursor.execute("""
            ALTER TABLE tickets
            ADD COLUMN priority TEXT NOT NULL DEFAULT 'MEDIUM'
        """)
        print("Added: priority")

    # Add assigned_to
    if "assigned_to" not in columns:
        cursor.execute("""
            ALTER TABLE tickets
            ADD COLUMN assigned_to TEXT
        """)
        print("Added: assigned_to")

    # Add created_at
    if "created_at" not in columns:
        cursor.execute("""
            ALTER TABLE tickets
            ADD COLUMN created_at TEXT
        """)
        print("Added: created_at")

    # Add updated_at
    if "updated_at" not in columns:
        cursor.execute("""
            ALTER TABLE tickets
            ADD COLUMN updated_at TEXT
        """)
        print("Added: updated_at")

    # Give existing tickets timestamps
    now = datetime.utcnow().isoformat()

    cursor.execute("""
        UPDATE tickets
        SET created_at = ?
        WHERE created_at IS NULL
    """, (now,))

    cursor.execute("""
        UPDATE tickets
        SET updated_at = ?
        WHERE updated_at IS NULL
    """, (now,))

    conn.commit()

    # Verify final structure
    cursor.execute("PRAGMA table_info(tickets)")
    final_columns = [row[1] for row in cursor.fetchall()]

    print("\nFinal columns:")

    for column in final_columns:
        print("-", column)

    conn.close()

    print("\nTicket table migration completed successfully!")


if __name__ == "__main__":
    migrate_tickets()