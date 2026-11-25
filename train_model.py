"""
train_model.py
Trains a Diabetes Risk Prediction model on the Pima Indians Diabetes dataset.
Cleans data -> splits -> scales -> trains multiple models -> picks the best ->
saves model + scaler + metrics to disk.
"""

import json
import numpy as np
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
)

DATA_PATH = "dataset/diabetes.csv"
MODEL_PATH = "model/diabetes_model.pkl"
SCALER_PATH = "model/scaler.pkl"
METRICS_PATH = "model/metrics.json"

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

# Columns where a 0 is not physiologically valid -> treat as missing
ZERO_AS_MISSING = ["Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI"]


def load_and_clean_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    # Replace invalid zeros with NaN, then fill with the median
    df[ZERO_AS_MISSING] = df[ZERO_AS_MISSING].replace(0, np.nan)
    for col in ZERO_AS_MISSING:
        df[col] = df[col].fillna(df[col].median())

    return df


def train_and_select_best(X_train, X_test, y_train, y_test):
    """Train a few candidate models and return the best one by ROC-AUC."""
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    candidates = {
        "LogisticRegression": (
            LogisticRegression(max_iter=1000),
            X_train_scaled,
            X_test_scaled,
        ),
        "DecisionTree": (
            DecisionTreeClassifier(random_state=42, max_depth=5),
            X_train,
            X_test,
        ),
        "RandomForest": (
            RandomForestClassifier(n_estimators=200, random_state=42, max_depth=6),
            X_train,
            X_test,
        ),
    }

    results = {}
    fitted_models = {}

    for name, (model, X_tr, X_te) in candidates.items():
        model.fit(X_tr, y_train)
        y_pred = model.predict(X_te)
        y_proba = model.predict_proba(X_te)[:, 1]

        results[name] = {
            "accuracy": accuracy_score(y_test, y_pred),
            "precision": precision_score(y_test, y_pred),
            "recall": recall_score(y_test, y_pred),
            "f1_score": f1_score(y_test, y_pred),
            "roc_auc": roc_auc_score(y_test, y_proba),
            "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
            "classification_report": classification_report(
                y_test, y_pred, output_dict=True
            ),
            "uses_scaled_input": name == "LogisticRegression",
        }
        fitted_models[name] = model

        print(f"\n=== {name} ===")
        print(f"Accuracy : {results[name]['accuracy']:.4f}")
        print(f"Precision: {results[name]['precision']:.4f}")
        print(f"Recall   : {results[name]['recall']:.4f}")
        print(f"F1 Score : {results[name]['f1_score']:.4f}")
        print(f"ROC-AUC  : {results[name]['roc_auc']:.4f}")

    best_name = max(results, key=lambda n: results[n]["roc_auc"])
    print(f"\nBest model by ROC-AUC: {best_name}")

    return best_name, fitted_models[best_name], results, scaler


def main():
    df = load_and_clean_data(DATA_PATH)

    X = df[FEATURE_COLUMNS]
    y = df["Outcome"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    best_name, best_model, results, scaler = train_and_select_best(
        X_train, X_test, y_train, y_test
    )

    joblib.dump(best_model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)

    metrics_out = {
        "best_model": best_name,
        "uses_scaled_input": results[best_name]["uses_scaled_input"],
        "feature_columns": FEATURE_COLUMNS,
        "results": results,
    }
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics_out, f, indent=2)

    print(f"\nSaved model to {MODEL_PATH}")
    print(f"Saved scaler to {SCALER_PATH}")
    print(f"Saved metrics to {METRICS_PATH}")


if __name__ == "__main__":
    main()
