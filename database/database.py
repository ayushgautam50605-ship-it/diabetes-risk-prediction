"""
database/database.py
Database and Persistence layer for the Secure Diabetes Risk Prediction System.
Uses SQLite with strict parameterized queries to prevent SQL Injection attacks.
Includes User management, Predictions history, and Audit / Security Logging.
"""

import os
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from dotenv import load_dotenv

# Import security helpers
from security.security import hash_password, generate_patient_id

# Load environment configuration
load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_ENV_PATH = os.getenv("DATABASE_PATH", "database/diabetes_secure.db")
if os.path.isabs(DB_ENV_PATH):
    DATABASE_PATH = DB_ENV_PATH
else:
    DATABASE_PATH = os.path.join(BASE_DIR, DB_ENV_PATH)

LOGS_DIR = os.path.join(BASE_DIR, "logs")
AUDIT_LOG_FILE = os.path.join(LOGS_DIR, "security_audit.log")


def get_db_path() -> str:
    """Return the resolved database path."""
    return DATABASE_PATH


def set_db_path(custom_path: str) -> None:
    """Override database path (primarily used for test isolation)."""
    global DATABASE_PATH
    if os.path.isabs(custom_path):
        DATABASE_PATH = custom_path
    else:
        DATABASE_PATH = os.path.join(BASE_DIR, custom_path)


def get_connection() -> sqlite3.Connection:
    """Create and return a configured database connection."""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db() -> None:
    """
    Initialize SQLite tables with parameterized statements and create
    the default admin user if none exists.
    """
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)

    with get_connection() as conn:
        cursor = conn.cursor()

        # Users table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_uid TEXT UNIQUE NOT NULL,
                username TEXT UNIQUE NOT NULL COLLATE NOCASE,
                email TEXT UNIQUE NOT NULL COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Predictions table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                user_uid TEXT NOT NULL,
                pregnancies INTEGER NOT NULL,
                glucose REAL NOT NULL,
                blood_pressure REAL NOT NULL,
                skin_thickness REAL NOT NULL,
                insulin REAL NOT NULL,
                bmi REAL NOT NULL,
                diabetes_pedigree_function REAL NOT NULL,
                age INTEGER NOT NULL,
                prediction INTEGER NOT NULL,
                prediction_label TEXT NOT NULL,
                probability REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )

        # Audit logs table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_uid TEXT,
                username TEXT,
                action TEXT NOT NULL,
                details TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Performance and integrity indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_predictions_user_id ON predictions(user_id);"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);"
        )

        conn.commit()

    # Seed default administrator if not present
    seed_default_admin()


def seed_default_admin() -> None:
    """Seed the default administrator account from environment configuration."""
    admin_username = os.getenv("ADMIN_USERNAME", "admin").strip()
    admin_email = os.getenv("ADMIN_EMAIL", "admin@securehealth.local").strip()
    admin_password = os.getenv("ADMIN_INITIAL_PASSWORD", "Admin@Secure2026!")

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM users WHERE role = 'admin' LIMIT 1"
        )
        existing_admin = cursor.fetchone()

        if not existing_admin:
            # Check if admin username is already taken
            cursor.execute(
                "SELECT id FROM users WHERE username = ? COLLATE NOCASE",
                (admin_username,),
            )
            if not cursor.fetchone():
                admin_uid = "ADM-1001"
                hashed_pw = hash_password(admin_password)
                cursor.execute(
                    """
                    INSERT INTO users (user_uid, username, email, password_hash, role)
                    VALUES (?, ?, ?, ?, 'admin')
                    """,
                    (admin_uid, admin_username, admin_email, hashed_pw),
                )
                conn.commit()
                log_audit_event(
                    action="SYSTEM_INIT",
                    details="Default administrator account initialized.",
                    user_uid=admin_uid,
                    username=admin_username,
                )


# ---------------------------------------------------------------------
# User Management Operations (Parameterized)
# ---------------------------------------------------------------------
def create_user(
    username: str,
    email: str,
    password_hash: str,
    role: str = "user",
    user_uid: Optional[str] = None,
) -> Tuple[int, str]:
    """Insert a new user account with parameterized query."""
    if not user_uid:
        prefix = "ADM" if role == "admin" else "PID"
        user_uid = generate_patient_id(prefix=prefix)

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO users (user_uid, username, email, password_hash, role)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_uid, username.strip(), email.strip().lower(), password_hash, role),
        )
        conn.commit()
        user_id = cursor.lastrowid
        return user_id, user_uid


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Retrieve user record by username using parameterized query."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE username = ? COLLATE NOCASE",
            (username.strip(),),
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Retrieve user record by email using parameterized query."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE email = ? COLLATE NOCASE",
            (email.strip().lower(),),
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve user record by ID using parameterized query."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def get_all_users() -> List[Dict[str, Any]]:
    """
    Retrieve all registered users for Admin view.
    SECURITY: Explicitly excludes password_hash from the returned payload.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, user_uid, username, email, role, created_at
            FROM users
            ORDER BY id ASC
            """
        )
        return [dict(row) for row in cursor.fetchall()]


# ---------------------------------------------------------------------
# Prediction Operations (User Isolation & Parameterized)
# ---------------------------------------------------------------------
def save_prediction(
    user_id: int,
    user_uid: str,
    features: Dict[str, Any],
    prediction: int,
    prediction_label: str,
    probability: float,
) -> int:
    """Save a patient's prediction record with parameterized query."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO predictions (
                user_id, user_uid, pregnancies, glucose, blood_pressure,
                skin_thickness, insulin, bmi, diabetes_pedigree_function,
                age, prediction, prediction_label, probability
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                user_uid,
                int(features["Pregnancies"]),
                float(features["Glucose"]),
                float(features["BloodPressure"]),
                float(features["SkinThickness"]),
                float(features["Insulin"]),
                float(features["BMI"]),
                float(features["DiabetesPedigreeFunction"]),
                int(features["Age"]),
                int(prediction),
                str(prediction_label),
                float(probability),
            ),
        )
        conn.commit()
        return cursor.lastrowid


def get_predictions_by_user(user_id: int) -> List[Dict[str, Any]]:
    """
    Retrieve prediction history for a SPECIFIC user only.
    Enforces strict user isolation: User A cannot access User B's records.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM predictions
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,),
        )
        return [dict(row) for row in cursor.fetchall()]


def get_all_predictions() -> List[Dict[str, Any]]:
    """
    Retrieve all predictions for the Admin Dashboard.
    Joins with users to include username for administrative audit.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT p.*, u.username
            FROM predictions p
            LEFT JOIN users u ON p.user_id = u.id
            ORDER BY p.created_at DESC
            """
        )
        return [dict(row) for row in cursor.fetchall()]


def get_prediction_statistics() -> Dict[str, Any]:
    """Calculate aggregate statistics on prediction outcomes."""
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) AS total FROM predictions")
        total = cursor.fetchone()["total"]

        if total == 0:
            return {
                "total": 0,
                "high_risk": 0,
                "low_risk": 0,
                "high_risk_pct": 0.0,
                "low_risk_pct": 0.0,
                "avg_glucose": 0.0,
                "avg_bmi": 0.0,
                "avg_age": 0.0,
            }

        cursor.execute("SELECT COUNT(*) AS high FROM predictions WHERE prediction = 1")
        high_risk = cursor.fetchone()["high"]
        low_risk = total - high_risk

        cursor.execute(
            """
            SELECT
                AVG(glucose) AS avg_glucose,
                AVG(bmi) AS avg_bmi,
                AVG(age) AS avg_age
            FROM predictions
            """
        )
        avgs = cursor.fetchone()

        return {
            "total": total,
            "high_risk": high_risk,
            "low_risk": low_risk,
            "high_risk_pct": (high_risk / total) * 100.0,
            "low_risk_pct": (low_risk / total) * 100.0,
            "avg_glucose": round(avgs["avg_glucose"] or 0.0, 1),
            "avg_bmi": round(avgs["avg_bmi"] or 0.0, 1),
            "avg_age": round(avgs["avg_age"] or 0.0, 1),
        }


# ---------------------------------------------------------------------
# Audit / Security Logging Operations
# ---------------------------------------------------------------------
def log_audit_event(
    action: str,
    details: str,
    user_uid: Optional[str] = None,
    username: Optional[str] = None,
) -> None:
    """
    Record a security/audit event into both the database table and the
    security audit log file.
    SECURITY: NEVER log passwords or sensitive authorization tokens.
    """
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    clean_uid = user_uid or "ANONYMOUS"
    clean_username = username or "anonymous"

    # 1. Parameterized write to database
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO audit_logs (user_uid, username, action, details, timestamp)
                VALUES (?, ?, ?, ?, ?)
                """,
                (clean_uid, clean_username, action, details, timestamp_str),
            )
            conn.commit()
    except Exception as e:
        # Fallback to console if DB write fails, preserving system stability
        print(f"[ERROR] Failed to record audit log in DB: {e}")

    # 2. Append to audit log file
    try:
        os.makedirs(LOGS_DIR, exist_ok=True)
        log_line = f"{timestamp_str} - User {clean_uid} ({clean_username}) - {action}: {details}\n"
        with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_line)
    except Exception as e:
        print(f"[ERROR] Failed to write to audit log file: {e}")


def get_audit_logs(limit: int = 100, action_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve recent security audit logs for the Admin Dashboard."""
    with get_connection() as conn:
        cursor = conn.cursor()
        if action_filter and action_filter != "ALL":
            cursor.execute(
                """
                SELECT * FROM audit_logs
                WHERE action = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (action_filter, limit),
            )
        else:
            cursor.execute(
                """
                SELECT * FROM audit_logs
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (limit,),
            )
        return [dict(row) for row in cursor.fetchall()]


def get_system_counts() -> Dict[str, int]:
    """Retrieve global entity counts for summary metrics."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS count FROM users")
        total_users = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) AS count FROM predictions")
        total_predictions = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) AS count FROM audit_logs")
        total_audit_events = cursor.fetchone()["count"]

        return {
            "total_users": total_users,
            "total_predictions": total_predictions,
            "total_audit_events": total_audit_events,
        }
