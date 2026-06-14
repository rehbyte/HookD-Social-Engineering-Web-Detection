"""
Local SQLite storage for scan history and user profiles.

No internet or external service required — everything lives in a single file
(hookd.db by default), which makes it ideal for an offline exhibit.
The public functions keep the same names/signatures the rest of the app expects.
"""
import os
import uuid
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# DB file lives next to this module by default; override with DATABASE_PATH.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.environ.get("DATABASE_PATH", os.path.join(BASE_DIR, "hookd.db"))


def _connect():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # rows behave like dicts -> templates use log.field
    return conn


def init_db():
    """Create tables if they don't exist yet. Safe to call on every startup."""
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id             TEXT PRIMARY KEY,
                user_id        TEXT,
                history_name   TEXT,
                content        TEXT,
                content_type   TEXT,
                result         TEXT,
                result_details TEXT,
                created_at     TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id            TEXT PRIMARY KEY,
                email         TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                first_name    TEXT,
                last_name     TEXT,
                display_name  TEXT,
                created_at    TEXT
            )
        """)


# Initialize on import so the tables always exist.
init_db()


def log_scan(scan_type, result, sender, content, user_id):
    """Save a scan result to the local history table."""
    try:
        details_string = f"Score: {result['confidence']}% - Risk Score: {result['confidence']}%"
        with _connect() as conn:
            conn.execute(
                """INSERT INTO history
                   (id, user_id, history_name, content, content_type, result, result_details, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    str(uuid.uuid4()),
                    user_id,
                    sender,
                    content,
                    scan_type,
                    result["label"],
                    details_string,
                    datetime.now().isoformat(),
                ),
            )
        print("Scan logged to history.")
    except Exception as e:
        print(f"Error logging scan: {e}")


def get_scan_history(user_id):
    """Fetch the last 50 scans for a user, newest first."""
    try:
        with _connect() as conn:
            rows = conn.execute(
                """SELECT * FROM history
                   WHERE user_id = ?
                   ORDER BY created_at DESC
                   LIMIT 50""",
                (user_id,),
            ).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"Error fetching history: {e}")
        return []


def delete_scan_log(log_id, user_id):
    """Delete one scan, scoped to its owner so users can't delete others' logs."""
    try:
        with _connect() as conn:
            conn.execute(
                "DELETE FROM history WHERE id = ? AND user_id = ?",
                (log_id, user_id),
            )
        return True
    except Exception as e:
        print(f"Error deleting log: {e}")
        return False


# --- Local authentication (offline, password-hashed) ---

def create_user(email, password, first_name, last_name):
    """
    Create a local account with a hashed password.
    Returns (user_dict, None) on success or (None, error_message) on failure.
    """
    email = (email or "").strip().lower()
    if not email or not password:
        return None, "Email and password are required."
    if len(password) < 8:
        return None, "Password must be at least 8 characters."

    display_name = f"{(first_name or '').strip()} {(last_name or '').strip()}".strip() or email.split("@")[0]
    user_id = str(uuid.uuid4())
    try:
        with _connect() as conn:
            conn.execute(
                """INSERT INTO users
                   (id, email, password_hash, first_name, last_name, display_name, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    user_id,
                    email,
                    generate_password_hash(password),
                    first_name,
                    last_name,
                    display_name,
                    datetime.now().isoformat(),
                ),
            )
        return {"id": user_id, "email": email, "display_name": display_name}, None
    except sqlite3.IntegrityError:
        return None, "An account with that email already exists."
    except Exception as e:
        return None, f"Could not create account: {e}"


def authenticate_user(email, password):
    """Return the user dict if email+password are valid, else None."""
    email = (email or "").strip().lower()
    try:
        with _connect() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE email = ?", (email,)
            ).fetchone()
        if row and check_password_hash(row["password_hash"], password or ""):
            return {"id": row["id"], "email": row["email"], "display_name": row["display_name"]}
        return None
    except Exception as e:
        print(f"Error authenticating user: {e}")
        return None


def get_user_profile(user_id):
    try:
        with _connect() as conn:
            row = conn.execute(
                "SELECT id, email, first_name, last_name, display_name FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
        return dict(row) if row else None
    except Exception:
        return None
