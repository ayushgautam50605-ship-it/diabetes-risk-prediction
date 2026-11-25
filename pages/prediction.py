"""
pages/prediction.py
Diabetes Risk Prediction - Streamlit interface with ML backend and security safeguards.
Preserves existing ML model evaluation, input fields, scaling, and transparency UI,
while adding authentication barriers, clinical input validation, patient ID tagging,
and automatic encrypted history persistence.
"""

import os
import json
import numpy as np
import pandas as pd
import joblib
import streamlit as st

from auth.authentication import require_auth, init_session
from database.database import save_prediction, log_audit_event
from security.security import validate_prediction_inputs

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "model", "diabetes_model.pkl")
SCALER_PATH = os.path.join(BASE_DIR, "model", "scaler.pkl")
METRICS_PATH = os.path.join(BASE_DIR, "model", "metrics.json")

FEATURE_COLUMNS = [
    "Pregnancies",
    "Glucose",
    "BloodPressure",
    "SkinThickness",
    "Insulin",
    "BMI",
    "DiabetesPedigreeFunction",
    "Age",
]


@st.cache_resource
def load_artifacts():
    """Load machine learning model, scaler, and evaluation metrics."""
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    with open(METRICS_PATH, "r", encoding="utf-8") as f:
        metrics = json.load(f)
    return model, scaler, metrics


def render_prediction() -> None:
    """Render the secure diabetes prediction interface."""
    init_session()
    # Security Barrier: Only authenticated users can access the prediction page
    require_auth()

    model, scaler, metrics = load_artifacts()
    uses_scaled_input = metrics.get("uses_scaled_input", True)
    best_model_name = metrics.get("best_model", "Model")

    # ---------------------------------------------------------------------
    # Header & User Context
    # ---------------------------------------------------------------------
    st.title("🩺 Diabetes Risk Prediction")
    st.caption(
        f"Backend model: **{best_model_name}** trained on the Pima Indians "
        "Diabetes dataset."
    )
    st.markdown(
        f"**Patient ID**: `{st.session_state.user_uid}` &nbsp;|&nbsp; "
        f"**User**: `{st.session_state.username}`"
    )

    st.info(
        "This tool estimates a **predicted risk category** based on statistical "
        "patterns in historical data. It is an educational/college project demo "
        "and is **not a medical diagnosis**. Always consult a qualified doctor "
        "for actual medical advice.",
        icon="ℹ️",
    )

    # ---------------------------------------------------------------------
    # Input form (frontend)
    # ---------------------------------------------------------------------
    with st.form("prediction_form"):
        st.subheader("Enter patient health details")

        col1, col2 = st.columns(2)

        with col1:
            pregnancies = st.number_input(
                "Pregnancies",
                min_value=0,
                max_value=20,
                value=1,
                step=1,
                help="Number of times pregnant (0-20)",
            )
            glucose = st.number_input(
                "Glucose (mg/dL)",
                min_value=0.0,
                max_value=300.0,
                value=120.0,
                help="Plasma glucose concentration 2 hours in an oral glucose tolerance test",
            )
            blood_pressure = st.number_input(
                "Blood Pressure (mm Hg)",
                min_value=0.0,
                max_value=200.0,
                value=70.0,
                help="Diastolic blood pressure (mm Hg)",
            )
            skin_thickness = st.number_input(
                "Skin Thickness (mm)",
                min_value=0.0,
                max_value=100.0,
                value=20.0,
                help="Triceps skin fold thickness (mm)",
            )

        with col2:
            insulin = st.number_input(
                "Insulin (mu U/mL)",
                min_value=0.0,
                max_value=900.0,
                value=79.0,
                help="2-Hour serum insulin (mu U/mL)",
            )
            bmi = st.number_input(
                "BMI",
                min_value=0.0,
                max_value=70.0,
                value=25.0,
                help="Body mass index (weight in kg/(height in m)^2)",
            )
            pedigree = st.number_input(
                "Diabetes Pedigree Function",
                min_value=0.0,
                max_value=3.0,
                value=0.35,
                format="%.3f",
                help="Diabetes pedigree function score (genetic risk factor)",
            )
            age = st.number_input(
                "Age (years)",
                min_value=1,
                max_value=120,
                value=30,
                step=1,
                help="Age in years (1-120)",
            )

        submitted = st.form_submit_button("Predict Risk", use_container_width=True)

    # ---------------------------------------------------------------------
    # Prediction & Security Processing (backend logic)
    # ---------------------------------------------------------------------
    if submitted:
        input_dict = {
            "Pregnancies": pregnancies,
            "Glucose": glucose,
            "BloodPressure": blood_pressure,
            "SkinThickness": skin_thickness,
            "Insulin": insulin,
            "BMI": bmi,
            "DiabetesPedigreeFunction": pedigree,
            "Age": age,
        }

        # Rigorous input validation
        is_valid, val_err = validate_prediction_inputs(input_dict)
        if not is_valid:
            st.error(f"Input Validation Error: {val_err}")
            return

        input_data = pd.DataFrame(
            [[pregnancies, glucose, blood_pressure, skin_thickness, insulin, bmi, pedigree, age]],
            columns=FEATURE_COLUMNS,
        )

        model_input = scaler.transform(input_data) if uses_scaled_input else input_data

        raw_pred = model.predict(model_input)[0]
        prediction = int(raw_pred)
        probability = float(model.predict_proba(model_input)[0][1])

        prediction_label = "Higher Risk" if prediction == 1 else "Lower Risk"

        # Persist prediction securely under user's private account
        try:
            save_prediction(
                user_id=st.session_state.user_id,
                user_uid=st.session_state.user_uid,
                features=input_dict,
                prediction=prediction,
                prediction_label=prediction_label,
                probability=probability,
            )

            # Security audit log
            log_audit_event(
                action="PREDICTION_GENERATED",
                details=(
                    f"Generated prediction for Patient {st.session_state.user_uid}: "
                    f"Outcome={prediction_label}, Probability={probability:.1%}"
                ),
                user_uid=st.session_state.user_uid,
                username=st.session_state.username,
            )
        except Exception as e:
            st.warning(f"Could not save prediction to database: {e}")

        st.subheader("Result")

        if prediction == 1:
            st.warning(f"**Higher predicted risk category** — estimated probability: {probability:.1%}")
        else:
            st.success(f"**Lower predicted risk category** — estimated probability: {probability:.1%}")

        st.progress(min(max(probability, 0.0), 1.0))

        with st.expander("See the values used for this prediction"):
            st.dataframe(input_data, use_container_width=True)

        st.caption(
            "Reminder: this is a statistical estimate from a demo model, not a "
            "clinical diagnosis."
        )
        st.success("🔒 Assessment securely recorded in your private medical history.")

    # ---------------------------------------------------------------------
    # Model performance (transparency section - preserved completely)
    # ---------------------------------------------------------------------
    with st.expander("📊 Model performance on test data"):
        res = metrics["results"][best_model_name]
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Accuracy", f"{res['accuracy']:.1%}")
        m2.metric("Precision", f"{res['precision']:.1%}")
        m3.metric("Recall", f"{res['recall']:.1%}")
        m4.metric("ROC-AUC", f"{res['roc_auc']:.3f}")

        st.write("Confusion matrix (rows = actual, cols = predicted):")
        cm = np.array(res["confusion_matrix"])
        st.dataframe(
            pd.DataFrame(
                cm,
                index=["Actual: No Diabetes", "Actual: Diabetes"],
                columns=["Predicted: No Diabetes", "Predicted: Diabetes"],
            ),
            use_container_width=True,
        )


if __name__ == "__main__":
    render_prediction()
