"""
auth/authentication.py
Authentication and Role-Based Access Control (RBAC) layer for the
Secure Diabetes Risk Prediction System.
Integrates with Streamlit session state and enforces access barriers.
"""

from datetime import datetime
from typing import Tuple, Dict, Any, Optional
import streamlit as st

from security.security import (
    hash_password,
    verify_password,
    validate_username,
    validate_email,
    validate_password,
)
from database.database import (
    create_user,
    get_user_by_username,
    get_user_by_email,
    log_audit_event,
)


def init_session() -> None:
    """Initialize essential security attributes in Streamlit's session state."""
    defaults = {
        "authenticated": False,
        "user_id": None,
        "user_uid": None,
        "username": None,
        "email": None,
        "role": None,
        "login_time": None,
        "current_page": "Login",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def is_authenticated() -> bool:
    """Check if the current session represents an authenticated user."""
    return bool(st.session_state.get("authenticated", False))


def is_admin() -> bool:
    """Check if the current user possesses administrator privileges."""
    return is_authenticated() and st.session_state.get("role") == "admin"


def get_current_user() -> Dict[str, Any]:
    """Return dictionary of current authenticated user session data."""
    return {
        "user_id": st.session_state.get("user_id"),
        "user_uid": st.session_state.get("user_uid"),
        "username": st.session_state.get("username"),
        "email": st.session_state.get("email"),
        "role": st.session_state.get("role"),
        "login_time": st.session_state.get("login_time"),
    }


def login_user(username: str, password: str) -> Tuple[bool, str]:
    """
    Authenticate user credentials against hashed database records.
    Logs successful logins and failed attempts (without recording passwords).
    Returns (True, "Welcome") or (False, "Invalid username or password.").
    """
    clean_username = username.strip() if username else ""

    if not clean_username or not password:
        return False, "Please enter both username and password."

    user = get_user_by_username(clean_username)

    if not user:
        # User not found - record failed attempt and return generic message
        log_audit_event(
            action="LOGIN_FAILURE",
            details=f"Failed login attempt for non-existent or incorrect username: {clean_username}",
            user_uid="ANONYMOUS",
            username=clean_username,
        )
        return False, "Invalid username or password."

    if not verify_password(password, user["password_hash"]):
        # Incorrect password - record failure without leaking password
        log_audit_event(
            action="LOGIN_FAILURE",
            details=f"Failed login attempt with incorrect password for username: {clean_username}",
            user_uid=user["user_uid"],
            username=clean_username,
        )
        return False, "Invalid username or password."

    # Successful authentication
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.authenticated = True
    st.session_state.user_id = user["id"]
    st.session_state.user_uid = user["user_uid"]
    st.session_state.username = user["username"]
    st.session_state.email = user["email"]
    st.session_state.role = user["role"]
    st.session_state.login_time = now_str

    # Default landing page after login based on role
    if user["role"] == "admin":
        st.session_state.current_page = "Admin Dashboard"
    else:
        st.session_state.current_page = "Dashboard"

    log_audit_event(
        action="LOGIN_SUCCESS",
        details=f"User {user['user_uid']} logged in successfully with role '{user['role']}'",
        user_uid=user["user_uid"],
        username=user["username"],
    )
    return True, "Login successful!"


def logout_user() -> None:
    """
    Terminate the authenticated user session, log audit event,
    and reset session state.
    """
    user_uid = st.session_state.get("user_uid", "ANONYMOUS")
    username = st.session_state.get("username", "anonymous")

    if is_authenticated():
        log_audit_event(
            action="LOGOUT",
            details=f"User {user_uid} logged out",
            user_uid=user_uid,
            username=username,
        )

    st.session_state.authenticated = False
    st.session_state.user_id = None
    st.session_state.user_uid = None
    st.session_state.username = None
    st.session_state.email = None
    st.session_state.role = None
    st.session_state.login_time = None
    st.session_state.current_page = "Login"

    st.rerun()


def register_user(
    username: str,
    email: str,
    password: str,
    confirm_password: str,
) -> Tuple[bool, str]:
    """
    Validate and register a new user account.
    Enforces password complexity, unique constraints, and bcrypt hashing.
    """
    # 1. Username validation
    valid_u, err_u = validate_username(username)
    if not valid_u:
        return False, err_u

    # 2. Email validation
    valid_e, err_e = validate_email(email)
    if not valid_e:
        return False, err_e

    # 3. Password matching validation
    if password != confirm_password:
        return False, "Passwords do not match."

    # 4. Password complexity validation
    valid_p, err_p = validate_password(password)
    if not valid_p:
        return False, err_p

    # 5. Check duplicate username
    if get_user_by_username(username):
        return False, f"Username '{username}' is already taken. Please choose another."

    # 6. Check duplicate email
    if get_user_by_email(email):
        return False, "This email address is already registered."

    # 7. Hash password securely
    password_hash = hash_password(password)

    # 8. Insert user record
    try:
        user_id, user_uid = create_user(
            username=username,
            email=email,
            password_hash=password_hash,
            role="user",
        )
        log_audit_event(
            action="USER_REGISTER",
            details=f"New user registered with Patient ID: {user_uid}",
            user_uid=user_uid,
            username=username,
        )
        return True, f"Account successfully created for {username}! Your Patient ID is {user_uid}."
    except Exception as e:
        return False, f"Failed to register account: {str(e)}"


# ---------------------------------------------------------------------
# Access Control Barriers / Page Guards
# ---------------------------------------------------------------------
def require_auth() -> None:
    """
    Ensure the current user is authenticated.
    If unauthenticated, logs unauthorized access attempt, displays
    warning, and immediately halts page rendering.
    """
    if not is_authenticated():
        log_audit_event(
            action="UNAUTHORIZED_ACCESS_ATTEMPT",
            details="Unauthenticated user attempted to access protected resource",
            user_uid="ANONYMOUS",
            username="anonymous",
        )
        st.warning("Please login to access the prediction system.", icon="🔒")
        if st.button("Go to Login Page", use_container_width=True):
            st.session_state.current_page = "Login"
            st.rerun()
        st.stop()


def require_role(required_role: str) -> None:
    """
    Ensure the current user has the specified role (e.g. 'admin').
    If role does not match, logs unauthorized attempt, displays error,
    and immediately halts page rendering.
    """
    require_auth()

    user_role = st.session_state.get("role")
    if user_role != required_role:
        user_uid = st.session_state.get("user_uid", "UNKNOWN")
        username = st.session_state.get("username", "unknown")
        log_audit_event(
            action="UNAUTHORIZED_ACCESS_ATTEMPT",
            details=f"User {user_uid} (role: {user_role}) attempted to access {required_role}-only resource",
            user_uid=user_uid,
            username=username,
        )
        st.error("You are not authorized to access this page.", icon="⛔")
        st.info("This section requires administrator privileges.", icon="ℹ️")
        if st.button("Return to Dashboard", use_container_width=True):
            st.session_state.current_page = "Dashboard"
            st.rerun()
        st.stop()
