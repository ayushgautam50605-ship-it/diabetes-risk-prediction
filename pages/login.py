"""
pages/login.py
User and Administrator Authentication Interface.
"""

import streamlit as st
from auth.authentication import login_user, is_authenticated, init_session


def render_login() -> None:
    """Render the secure login interface."""
    init_session()

    if is_authenticated():
        st.success(f"You are already logged in as **{st.session_state.username}**.")
        if st.button("Go to Application", use_container_width=True):
            if st.session_state.role == "admin":
                st.session_state.current_page = "Admin Dashboard"
            else:
                st.session_state.current_page = "Dashboard"
            st.rerun()
        return

    st.title("🔐 Secure System Login")
    st.caption("Access the Secure Diabetes Risk Prediction System.")

    col1, col2 = st.columns([1, 1])

    with col1:
        with st.form("login_form", clear_on_submit=False):
            st.subheader("Sign In")

            username = st.text_input(
                "Username",
                placeholder="Enter your username",
                help="Your registered account username.",
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                help="Your secure account password.",
            )

            submitted = st.form_submit_button("Sign In", use_container_width=True)

            if submitted:
                if not username.strip() or not password:
                    st.error("Please provide both username and password.")
                else:
                    success, message = login_user(username.strip(), password)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

        st.markdown("---")
        st.markdown("Don't have an account yet?")
        if st.button("Create New Account", use_container_width=True, type="secondary"):
            st.session_state.current_page = "Register"
            st.rerun()

    with col2:
        st.info(
            "### 🛡️ Security Protections\n\n"
            "- **Bcrypt Password Hashing**: Passwords are protected with salted bcrypt hashes.\n"
            "- **Parameterized Queries**: Strict SQL injection prevention.\n"
            "- **Defense-in-Depth**: Role-based access controls and unauthenticated request barriers.\n"
            "- **Security Audit Logging**: All authentication attempts are logged for security oversight.\n"
            "- **Anonymized Patient Records**: Sensitive data tied only to private patient IDs.",
            icon="🔒",
        )


if __name__ == "__main__":
    render_login()
