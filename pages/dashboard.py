"""
pages/dashboard.py
User Dashboard providing session overview, quick statistics, and navigation.
"""

import pandas as pd
import streamlit as st

from auth.authentication import require_auth, init_session
from database.database import get_predictions_by_user


def render_dashboard() -> None:
    """Render the authenticated user dashboard."""
    init_session()
    require_auth()

    username = st.session_state.username
    user_uid = st.session_state.user_uid
    user_id = st.session_state.user_id

    st.title("📊 Patient Dashboard")
    st.markdown(
        f"Welcome, **{username}** &nbsp;|&nbsp; "
        f"Patient ID: `{user_uid}` &nbsp;|&nbsp; "
        f"Role: `{st.session_state.role.upper()}`"
    )

    # Fetch user's own predictions
    user_preds = get_predictions_by_user(user_id)
    total_preds = len(user_preds)

    # Summary metrics row
    m1, m2, m3, m4 = st.columns(4)

    m1.metric("Assessments Run", total_preds)

    if total_preds > 0:
        latest = user_preds[0]
        latest_label = latest["prediction_label"]
        latest_proba = latest["probability"]
        high_risk_count = sum(1 for p in user_preds if p["prediction"] == 1)

        m2.metric("Latest Result", latest_label)
        m3.metric("Latest Probability", f"{latest_proba:.1%}")
        m4.metric("High Risk Assessments", high_risk_count)
    else:
        m2.metric("Latest Result", "N/A")
        m3.metric("Latest Probability", "N/A")
        m4.metric("High Risk Assessments", "0")

    st.markdown("---")

    # Quick Action Cards
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("🩺 Diabetes Risk Screening")
        st.write(
            "Perform a new statistical diabetes risk assessment using your clinical "
            "health indicators (Glucose, Blood Pressure, BMI, Age, etc.)."
        )
        if st.button("Start New Assessment", use_container_width=True, type="primary"):
            st.session_state.current_page = "Diabetes Prediction"
            st.rerun()

    with c2:
        st.subheader("📜 Personal Health Records")
        st.write(
            "Review your previous risk assessment results, clinical inputs, "
            "and probability trends securely stored in your account history."
        )
        if st.button("View Prediction History", use_container_width=True):
            st.session_state.current_page = "Prediction History"
            st.rerun()

    st.markdown("---")

    # Recent assessments preview
    if total_preds > 0:
        st.subheader("Recent Assessments Preview")
        recent_df = pd.DataFrame(
            [
                {
                    "Date & Time": p["created_at"],
                    "Risk Category": p["prediction_label"],
                    "Probability": f"{p['probability']:.1%}",
                    "Glucose": p["glucose"],
                    "Blood Pressure": p["blood_pressure"],
                    "BMI": p["bmi"],
                    "Age": p["age"],
                }
                for p in user_preds[:3]
            ]
        )
        st.dataframe(recent_df, use_container_width=True)
    else:
        st.info(
            "You haven't run any risk assessments yet. "
            "Click **Start New Assessment** above to evaluate your risk.",
            icon="ℹ️",
        )

    st.caption("🔒 Privacy Guarantee: Your health metrics are strictly tied to your private account and cannot be viewed by other users.")


if __name__ == "__main__":
    render_dashboard()
