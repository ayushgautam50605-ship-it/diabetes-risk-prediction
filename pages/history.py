"""
pages/history.py
Secure Patient Prediction History Interface.
Enforces strict user isolation: User A can NEVER view User B's health records.
"""

import pandas as pd
import streamlit as st

from auth.authentication import require_auth, init_session
from database.database import get_predictions_by_user


def render_history() -> None:
    """Render the authenticated user's prediction history."""
    init_session()
    # Security Barrier: Require active authenticated session
    require_auth()

    user_id = st.session_state.user_id
    user_uid = st.session_state.user_uid
    username = st.session_state.username

    st.title("📜 Personal Prediction History")
    st.markdown(
        f"**Patient ID**: `{user_uid}` &nbsp;|&nbsp; "
        f"**User**: `{username}`"
    )
    st.caption("Confidential health records and historical assessment outcomes.")

    # Strictly fetch predictions belonging to the logged-in user
    records = get_predictions_by_user(user_id)

    if not records:
        st.info(
            "No prediction history found. Complete a diabetes risk assessment on "
            "the Prediction page to record your first health evaluation.",
            icon="ℹ️",
        )
        if st.button("Go to Diabetes Risk Prediction", use_container_width=True, type="primary"):
            st.session_state.current_page = "Diabetes Prediction"
            st.rerun()
        return

    # Aggregate metrics for the patient
    total = len(records)
    high_count = sum(1 for r in records if r["prediction"] == 1)
    low_count = total - high_count
    avg_proba = sum(r["probability"] for r in records) / total

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Assessments", total)
    c2.metric("Higher Risk Results", high_count)
    c3.metric("Lower Risk Results", low_count)
    c4.metric("Avg Estimated Probability", f"{avg_proba:.1%}")

    st.markdown("---")

    # Format dataframe for display
    display_rows = []
    for r in records:
        display_rows.append(
            {
                "Assessment Date": r["created_at"],
                "Risk Category": r["prediction_label"],
                "Probability": f"{r['probability']:.1%}",
                "Glucose": r["glucose"],
                "Blood Pressure": r["blood_pressure"],
                "BMI": r["bmi"],
                "Age": r["age"],
                "Insulin": r["insulin"],
                "Skin Thickness": r["skin_thickness"],
                "Pedigree Score": f"{r['diabetes_pedigree_function']:.3f}",
                "Pregnancies": r["pregnancies"],
            }
        )

    df_display = pd.DataFrame(display_rows)

    st.subheader("Historical Assessment Records")
    st.dataframe(df_display, use_container_width=True)

    # Download CSV export for the patient's personal records
    csv_bytes = df_display.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download My Health History (CSV)",
        data=csv_bytes,
        file_name=f"diabetes_risk_history_{user_uid}.csv",
        mime="text/csv",
        use_container_width=True,
    )

    st.caption("🔒 Security Notice: Records are accessed via parameterized queries and filtered exclusively by your user ID.")


if __name__ == "__main__":
    render_history()
