"""
app.py
Secure Diabetes Risk Prediction System Using Machine Learning.
Main application entry point with authentication routing, session state management,
and role-based page dispatching.
Run with: streamlit run app.py
"""

import streamlit as st

from database.database import init_db
from auth.authentication import (
    init_session,
    is_authenticated,
    is_admin,
    logout_user,
)
from pages.login import render_login
from pages.register import render_register
from pages.dashboard import render_dashboard
from pages.prediction import render_prediction
from pages.history import render_history
from pages.admin import render_admin
from pages.about import render_about

# ---------------------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------------------
st.set_page_config(
    page_title="Secure Diabetes Risk Prediction",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize persistence and session state
init_db()
init_session()

# ---------------------------------------------------------------------
# Sidebar Navigation & Authentication Control
# ---------------------------------------------------------------------
st.sidebar.title("🩺 Secure Health System")
st.sidebar.caption("AI-Powered Diabetes Screening with Information Security")

authenticated = is_authenticated()
admin = is_admin()

# Define navigation mapping based on authentication status and user role
if not authenticated:
    nav_options = [
        "🔐 Login",
        "📝 Register",
        "ℹ️ About System",
    ]
    name_to_page = {
        "🔐 Login": "Login",
        "📝 Register": "Register",
        "ℹ️ About System": "About System",
    }
    page_to_name = {v: k for k, v in name_to_page.items()}
elif admin:
    nav_options = [
        "🛡️ Admin Dashboard",
        "🩺 Diabetes Prediction",
        "📜 Prediction History",
        "ℹ️ About System",
    ]
    name_to_page = {
        "🛡️ Admin Dashboard": "Admin Dashboard",
        "🩺 Diabetes Prediction": "Diabetes Prediction",
        "📜 Prediction History": "Prediction History",
        "ℹ️ About System": "About System",
    }
    page_to_name = {v: k for k, v in name_to_page.items()}
else:
    # Standard User
    nav_options = [
        "📊 Dashboard",
        "🩺 Diabetes Prediction",
        "📜 Prediction History",
        "ℹ️ About System",
    ]
    name_to_page = {
        "📊 Dashboard": "Dashboard",
        "🩺 Diabetes Prediction": "Diabetes Prediction",
        "📜 Prediction History": "Prediction History",
        "ℹ️ About System": "About System",
    }
    page_to_name = {v: k for k, v in name_to_page.items()}

# Display user profile banner in sidebar when logged in
if authenticated:
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"👤 **User:** `{st.session_state.username}`")
    st.sidebar.markdown(f"🆔 **ID:** `{st.session_state.user_uid}`")
    role_badge = "🔴 ADMIN" if admin else "🟢 USER"
    st.sidebar.markdown(f"🛡️ **Role:** {role_badge}")
    st.sidebar.markdown("---")

# Determine current navigation index
current_page = st.session_state.get("current_page", "Login" if not authenticated else ("Admin Dashboard" if admin else "Dashboard"))
default_name = page_to_name.get(current_page, nav_options[0])

try:
    default_index = nav_options.index(default_name)
except ValueError:
    default_index = 0

selected_option = st.sidebar.radio(
    "Navigation",
    nav_options,
    index=default_index,
    key="nav_selection",
)

# Synchronize session state page
st.session_state.current_page = name_to_page[selected_option]

# Logout button in sidebar for authenticated sessions
if authenticated:
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout", use_container_width=True, type="secondary"):
        logout_user()

st.sidebar.markdown("---")
st.sidebar.caption("🔒 Security Status: Encrypted & Monitored")
st.sidebar.caption("v2.0-Secure • SQLite & Bcrypt")

# ---------------------------------------------------------------------
# Route and Render View
# ---------------------------------------------------------------------
active_page = st.session_state.current_page

if active_page == "Login":
    render_login()
elif active_page == "Register":
    render_register()
elif active_page == "Dashboard":
    render_dashboard()
elif active_page == "Diabetes Prediction":
    render_prediction()
elif active_page == "Prediction History":
    render_history()
elif active_page == "Admin Dashboard":
    render_admin()
elif active_page == "About System":
    render_about()
else:
    st.warning("Page not found. Redirecting to home...")
    st.session_state.current_page = "Login" if not authenticated else "Dashboard"
    st.rerun()
