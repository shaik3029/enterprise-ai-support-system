import sqlite3
import os
from datetime import datetime


DB_PATH = os.path.join(
    os.path.dirname(__file__),
    "enterprise_support.db"
)


def migrate_users():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check existing columns
    cursor.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]

    print("Existing columns:", columns)

    # Add password hash
    if "password_hash" not in columns:

        cursor.execute("""
            ALTER TABLE users
            ADD COLUMN password_hash TEXT
        """)

        print("Added: password_hash")

    # Add role
    if "role" not in columns:

        cursor.execute("""
            ALTER TABLE users
            ADD COLUMN role TEXT NOT NULL DEFAULT 'CUSTOMER'
        """)

        print("Added: role")

    # Add created timestamp
    if "created_at" not in columns:

        cursor.execute("""
            ALTER TABLE users
            ADD COLUMN created_at TEXT
        """)

        print("Added: created_at")

    # Set timestamp for existing users
    now = datetime.utcnow().isoformat()

    cursor.execute("""
        UPDATE users
        SET created_at = ?
        WHERE created_at IS NULL
    """, (now,))

    conn.commit()

    # Verify final structure
    cursor.execute("PRAGMA table_info(users)")
    final_columns = [row[1] for row in cursor.fetchall()]

    print("\nFinal user columns:")

    for column in final_columns:
        print("-", column)

    conn.close()

    print("\nUser table migration completed successfully!")


if __name__ == "__main__":
    migrate_users()