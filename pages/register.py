"""
pages/register.py
User Registration Interface with strict field validation and password complexity.
"""

import streamlit as st
from auth.authentication import register_user, is_authenticated, init_session


def render_register() -> None:
    """Render the user registration interface."""
    init_session()

    if is_authenticated():
        st.info("You already have an active session.")
        if st.button("Go to Application", use_container_width=True):
            st.session_state.current_page = "Dashboard"
            st.rerun()
        return

    st.title("📝 Register New Account")
    st.caption("Create an encrypted patient profile for diabetes risk assessment.")

    col1, col2 = st.columns([1, 1])

    with col1:
        with st.form("register_form", clear_on_submit=False):
            st.subheader("Account Details")

            username = st.text_input(
                "Username",
                placeholder="e.g. john_doe",
                help="3-30 characters, letters, numbers, and underscores only.",
            )
            email = st.text_input(
                "Email Address",
                placeholder="e.g. john@example.com",
                help="Valid email address for notification and verification.",
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="At least 8 characters",
                help="Must contain uppercase, lowercase, and a number.",
            )
            confirm_password = st.text_input(
                "Confirm Password",
                type="password",
                placeholder="Re-enter your password",
            )

            submitted = st.form_submit_button("Create Account", use_container_width=True)

            if submitted:
                success, message = register_user(
                    username=username,
                    email=email,
                    password=password,
                    confirm_password=confirm_password,
                )
                if success:
                    st.success(message)
                    st.balloons()
                    st.info("You can now sign in with your credentials.")
                else:
                    st.error(message)

        st.markdown("---")
        st.markdown("Already registered?")
        if st.button("Sign In to Existing Account", use_container_width=True, type="secondary"):
            st.session_state.current_page = "Login"
            st.rerun()

    with col2:
        st.info(
            "### 📋 Password & Security Rules\n\n"
            "- **Username**: 3 to 30 characters (letters, numbers, `_`)\n"
            "- **Email**: Must be a valid email format\n"
            "- **Password Requirements**:\n"
            "  - Minimum 8 characters in length\n"
            "  - At least one uppercase letter (A-Z)\n"
            "  - At least one lowercase letter (a-z)\n"
            "  - At least one numeric digit (0-9)\n"
            "- **Unique Patient Identifier**: A secure Patient ID (e.g. `PID-XXXXX`) "
            "is automatically assigned upon registration to protect privacy.",
            icon="ℹ️",
        )


if __name__ == "__main__":
    render_register()
