"""
security/security.py
Information Security utility layer for the Secure Diabetes Risk Prediction System.
Handles password hashing (bcrypt), input validation, anonymized identifier generation,
and defensive sanitization.
"""

import os
import re
import html
import secrets
from typing import Tuple, Dict, Any
import bcrypt
from dotenv import load_dotenv

# Load environment configuration
load_dotenv()

PASSWORD_MIN_LENGTH = int(os.getenv("PASSWORD_MIN_LENGTH", "8"))
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_]{3,30}$")


# ---------------------------------------------------------------------
# Cryptographic Password Hashing & Verification
# ---------------------------------------------------------------------
def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt with salt factor 12."""
    if not password:
        raise ValueError("Password cannot be empty.")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


# ---------------------------------------------------------------------
# Anonymized Identifier Generation
# ---------------------------------------------------------------------
def generate_patient_id(prefix: str = "PID") -> str:
    """
    Generate a cryptographically randomized, anonymized Patient/User ID
    e.g. PID-84729 or USR-19382 to avoid exposing personal names or raw IDs.
    """
    random_num = secrets.randbelow(90000) + 10000  # 5-digit random integer
    return f"{prefix}-{random_num}"


# ---------------------------------------------------------------------
# Input Validation Routines
# ---------------------------------------------------------------------
def validate_username(username: str) -> Tuple[bool, str]:
    """Validate username criteria: 3-30 chars, alphanumeric and underscore."""
    if not username or not username.strip():
        return False, "Username is required."
    clean = username.strip()
    if len(clean) < 3 or len(clean) > 30:
        return False, "Username must be between 3 and 30 characters."
    if not USERNAME_REGEX.match(clean):
        return False, "Username can only contain letters, numbers, and underscores (_)."
    return True, ""


def validate_email(email: str) -> Tuple[bool, str]:
    """Validate email format and length."""
    if not email or not email.strip():
        return False, "Email address is required."
    clean = email.strip()
    if len(clean) > 100:
        return False, "Email address exceeds maximum length (100 characters)."
    if not EMAIL_REGEX.match(clean):
        return False, "Please enter a valid email address (e.g., patient@example.com)."
    return True, ""


def validate_password(password: str) -> Tuple[bool, str]:
    """
    Validate password strength:
    - At least PASSWORD_MIN_LENGTH characters
    - Contains at least one lowercase letter
    - Contains at least one uppercase letter
    - Contains at least one numeric digit
    """
    if not password:
        return False, "Password is required."
    if len(password) < PASSWORD_MIN_LENGTH:
        return False, f"Password must be at least {PASSWORD_MIN_LENGTH} characters long."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number."
    return True, ""


def validate_prediction_inputs(inputs: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate health/clinical input values against expected biological ranges
    for the Pima Indians Diabetes model features.
    Prevents empty values, NaN/Inf, and impossible values.
    """
    required_fields = [
        ("Pregnancies", int, 0, 20),
        ("Glucose", float, 0.0, 300.0),
        ("BloodPressure", float, 0.0, 200.0),
        ("SkinThickness", float, 0.0, 100.0),
        ("Insulin", float, 0.0, 900.0),
        ("BMI", float, 0.0, 70.0),
        ("DiabetesPedigreeFunction", float, 0.0, 3.0),
        ("Age", int, 1, 120),
    ]

    for field_name, expected_type, min_val, max_val in required_fields:
        if field_name not in inputs:
            return False, f"Missing required health parameter: {field_name}."

        raw_val = inputs[field_name]
        if raw_val is None:
            return False, f"Value for '{field_name}' cannot be empty."

        try:
            val = expected_type(raw_val)
        except (ValueError, TypeError):
            return False, f"Value for '{field_name}' must be a valid numeric {expected_type.__name__}."

        # Check for NaN or Infinite values
        if isinstance(val, float) and (val != val or val in (float("inf"), float("-inf"))):
            return False, f"Invalid numeric value provided for '{field_name}'."

        if val < min_val or val > max_val:
            return (
                False,
                f"'{field_name}' value {val} is outside clinical boundary [{min_val}, {max_val}].",
            )

    return True, ""


# ---------------------------------------------------------------------
# Sanitization Helper
# ---------------------------------------------------------------------
def sanitize_text(text: str) -> str:
    """Sanitize user text input to mitigate HTML / Cross-Site Scripting (XSS)."""
    if text is None:
        return ""
    return html.escape(str(text).strip())
