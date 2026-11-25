"""
pages/admin.py
Administrator Dashboard and Governance Console.
Accessible exclusively to users with the 'admin' role.
Provides user management (without password exposure), aggregate prediction statistics,
and security audit logs.
"""

import pandas as pd
import streamlit as st

from auth.authentication import require_role, init_session
from database.database import (
    get_all_users,
    get_all_predictions,
    get_prediction_statistics,
    get_audit_logs,
    get_system_counts,
    log_audit_event,
)


def render_admin() -> None:
    """Render the administrator governance and audit dashboard."""
    init_session()
    # Security Barrier: Enforces administrator privileges
    require_role("admin")

    st.title("🛡️ Administrator Governance Dashboard")
    st.caption("System oversight, user management, and security audit monitoring.")

    # Log admin view event
    log_audit_event(
        action="ADMIN_ACTION",
        details="Admin accessed governance dashboard",
        user_uid=st.session_state.user_uid,
        username=st.session_state.username,
    )

    counts = get_system_counts()
    stats = get_prediction_statistics()

    # ---------------------------------------------------------------------
    # Top-Level Summary Metrics
    # ---------------------------------------------------------------------
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Registered Users", counts["total_users"])
    m2.metric("Total Predictions", counts["total_predictions"])
    m3.metric("High Risk Outcomes", f"{stats['high_risk']} ({stats['high_risk_pct']:.1f}%)")
    m4.metric("Low Risk Outcomes", f"{stats['low_risk']} ({stats['low_risk_pct']:.1f}%)")
    m5.metric("Audit Events", counts["total_audit_events"])

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs([
        "📊 Prediction Analytics",
        "👥 Registered Users",
        "📋 Security Audit Logs",
    ])

    # ---------------------------------------------------------------------
    # Tab 1: Prediction Analytics & Overview
    # ---------------------------------------------------------------------
    with tab1:
        st.subheader("Population Prediction Statistics")

        col1, col2, col3 = st.columns(3)
        col1.metric("Average Glucose (mg/dL)", f"{stats['avg_glucose']}")
        col2.metric("Average BMI", f"{stats['avg_bmi']}")
        col3.metric("Average Patient Age", f"{stats['avg_age']} yrs")

        st.markdown("#### All Prediction Records")
        all_preds = get_all_predictions()
        if all_preds:
            df_preds = pd.DataFrame(
                [
                    {
                        "ID": p["id"],
                        "Patient UID": p["user_uid"],
                        "Username": p.get("username", "N/A"),
                        "Date": p["created_at"],
                        "Outcome": p["prediction_label"],
                        "Probability": f"{p['probability']:.1%}",
                        "Glucose": p["glucose"],
                        "Blood Pressure": p["blood_pressure"],
                        "BMI": p["bmi"],
                        "Age": p["age"],
                    }
                    for p in all_preds
                ]
            )
            st.dataframe(df_preds, use_container_width=True)
        else:
            st.info("No prediction records found in the database.")

    # ---------------------------------------------------------------------
    # Tab 2: User Management (NO Passwords Displayed)
    # ---------------------------------------------------------------------
    with tab2:
        st.subheader("Registered User Accounts")
        st.caption("Cryptographic hashes are strictly excluded from administrative views.")

        users = get_all_users()
        if users:
            df_users = pd.DataFrame(
                [
                    {
                        "Database ID": u["id"],
                        "Patient/User UID": u["user_uid"],
                        "Username": u["username"],
                        "Email Address": u["email"],
                        "Assigned Role": u["role"].upper(),
                        "Registered Date": u["created_at"],
                    }
                    for u in users
                ]
            )
            st.dataframe(df_users, use_container_width=True)
        else:
            st.info("No users registered.")

    # ---------------------------------------------------------------------
    # Tab 3: Security & Audit Logs
    # ---------------------------------------------------------------------
    with tab3:
        st.subheader("Security & Audit Event Trail")

        filter_col, limit_col = st.columns([2, 1])
        with filter_col:
            action_options = [
                "ALL",
                "LOGIN_SUCCESS",
                "LOGIN_FAILURE",
                "LOGOUT",
                "USER_REGISTER",
                "PREDICTION_GENERATED",
                "UNAUTHORIZED_ACCESS_ATTEMPT",
                "ADMIN_ACTION",
                "SYSTEM_INIT",
            ]
            selected_action = st.selectbox("Filter by Security Event Type", action_options)

        with limit_col:
            log_limit = st.slider("Max Events", min_value=10, max_value=200, value=50, step=10)

        logs = get_audit_logs(limit=log_limit, action_filter=selected_action)

        if logs:
            df_logs = pd.DataFrame(
                [
                    {
                        "Timestamp": l["timestamp"],
                        "Actor UID": l["user_uid"],
                        "Username": l["username"],
                        "Security Action": l["action"],
                        "Event Details": l["details"],
                    }
                    for l in logs
                ]
            )
            st.dataframe(df_logs, use_container_width=True)

            # Export Audit Log
            audit_csv = df_logs.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download Audit Trail (CSV)",
                data=audit_csv,
                file_name="security_audit_log.csv",
                mime="text/csv",
            )
        else:
            st.info("No audit events match the specified criteria.")


if __name__ == "__main__":
    render_admin()
