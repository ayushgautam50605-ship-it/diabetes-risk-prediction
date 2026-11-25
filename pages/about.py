"""
pages/about.py
System Information and Security Architecture Documentation.
"""

import streamlit as st


def render_about() -> None:
    """Render the system information and security architecture overview."""
    st.title("ℹ️ Secure Diabetes Risk Prediction System")
    st.caption("Machine Learning Medical Screening Platform with Information Security Controls.")

    st.markdown(
        """
        ### 🎯 System Purpose & Overview
        This platform extends a machine learning-based diabetes screening system with an enterprise-grade
        **Information Security Layer**. It ensures patient data confidentiality, integrity, and non-repudiation
        while fully preserving the statistical predictive power of the underlying ML models.
        """
    )

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("🛡️ Security Layer Features")
        st.markdown(
            """
            - **Cryptographic Authentication**: Passwords hashed using salted `bcrypt` (12 rounds).
            - **Session Isolation**: Role-based access control (USER vs. ADMIN) with session barriers.
            - **Patient Privacy**: Anonymized Patient Identifiers (e.g. `PID-XXXXX`) decouple health records from identity.
            - **Strict User Isolation**: Patients can access only their own assessment history.
            - **Defensive SQL**: 100% parameterized SQLite queries preventing SQL Injection.
            - **Security Audit Trail**: High-fidelity logging of all login, logout, registration, prediction, and unauthorized access events.
            - **Environment Secret Isolation**: Credentials and paths stored in `.env` and kept out of version control.
            """
        )

    with c2:
        st.subheader("🤖 Machine Learning Engine")
        st.markdown(
            """
            - **Dataset**: Pima Indians Diabetes Dataset (768 patient records, 8 clinical features).
            - **Preprocessing**: Physiologically invalid zero values cleaned with median imputation; `StandardScaler` feature normalization.
            - **Candidate Models**: Logistic Regression, Decision Tree, Random Forest.
            - **Model Selection**: Ranked and selected by ROC-AUC for balanced screening precision.
            - **Transparency**: Real-time display of accuracy, precision, recall, ROC-AUC, and test confusion matrix.
            """
        )

    st.markdown("---")
    st.info(
        "**Clinical Disclaimer**: This application is a screening and educational tool. "
        "It provides statistical probability estimates based on historical data and does not "
        "constitute medical advice, diagnosis, or treatment. Consult a licensed medical practitioner.",
        icon="🩺",
    )


if __name__ == "__main__":
    render_about()
