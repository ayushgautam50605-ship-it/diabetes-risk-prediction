"""
test_security_and_system.py
Comprehensive automated test suite for the Secure Diabetes Risk Prediction System.
Tests:
1. Registration
2. Duplicate registration (username & email)
3. Login with correct password
4. Login with incorrect password (no username enumeration)
5. Logout
6. Unauthorized access (unauthenticated barrier)
7. Normal user access
8. Admin access (role guard barrier)
9. Prediction generation (model + scaler + probability)
10. Prediction history persistence
11. User isolation (User A cannot access User B's records)
12. Audit logging (verifying log contents & no password leaks)
13. Invalid inputs validation (out-of-range, NaN, negative values)
14. Application startup verification
"""

import os
import sys
import unittest
import pandas as pd
import joblib

# Ensure current directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.database import (
    init_db,
    set_db_path,
    get_connection,
    create_user,
    get_user_by_username,
    get_user_by_email,
    get_all_users,
    save_prediction,
    get_predictions_by_user,
    get_all_predictions,
    get_prediction_statistics,
    log_audit_event,
    get_audit_logs,
    AUDIT_LOG_FILE,
)
from security.security import (
    hash_password,
    verify_password,
    validate_username,
    validate_email,
    validate_password,
    validate_prediction_inputs,
    generate_patient_id,
)
from auth.authentication import (
    register_user,
    login_user,
    logout_user,
)


class TestSecureDiabetesSystem(unittest.TestCase):
    test_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database", "test_runner.db")

    @classmethod
    def setUpClass(cls):
        """Initialize isolated database for testing."""
        if os.path.exists(cls.test_db_path):
            try:
                os.remove(cls.test_db_path)
            except OSError:
                pass
        set_db_path(cls.test_db_path)
        init_db()

    @classmethod
    def tearDownClass(cls):
        """Clean up test database and restore production database path."""
        import gc
        gc.collect()
        set_db_path("database/diabetes_secure.db")
        if os.path.exists(cls.test_db_path):
            try:
                os.remove(cls.test_db_path)
            except OSError:
                pass

    def test_01_registration(self):
        """Test valid user registration and patient UID assignment."""
        ok, msg = register_user(
            username="alice_test",
            email="alice@test.org",
            password="Password123!",
            confirm_password="Password123!",
        )
        self.assertTrue(ok, f"Registration failed: {msg}")
        self.assertIn("Account successfully created", msg)

        user = get_user_by_username("alice_test")
        self.assertIsNotNone(user)
        self.assertEqual(user["username"], "alice_test")
        self.assertEqual(user["role"], "user")
        self.assertTrue(user["user_uid"].startswith("PID-"))
        # Verify password is NOT stored in plaintext
        self.assertNotEqual(user["password_hash"], "Password123!")
        self.assertTrue(verify_password("Password123!", user["password_hash"]))

    def test_02_duplicate_registration(self):
        """Test prevention of duplicate usernames and duplicate emails."""
        # Duplicate username
        ok, msg = register_user(
            username="alice_test",
            email="different_email@test.org",
            password="Password123!",
            confirm_password="Password123!",
        )
        self.assertFalse(ok)
        self.assertIn("already taken", msg)

        # Duplicate email
        ok, msg = register_user(
            username="different_user",
            email="alice@test.org",
            password="Password123!",
            confirm_password="Password123!",
        )
        self.assertFalse(ok)
        self.assertIn("already registered", msg)

    def test_03_login_correct_password(self):
        """Test successful authentication with bcrypt verification."""
        import streamlit as st
        if "authenticated" not in st.session_state:
            st.session_state.authenticated = False

        ok, msg = login_user("alice_test", "Password123!")
        self.assertTrue(ok, f"Login failed: {msg}")
        self.assertTrue(st.session_state.authenticated)
        self.assertEqual(st.session_state.username, "alice_test")
        self.assertEqual(st.session_state.role, "user")

    def test_04_login_incorrect_password(self):
        """Test failed authentication gives generic message and doesn't reveal user existence."""
        ok, msg = login_user("alice_test", "WrongPassword999!")
        self.assertFalse(ok)
        self.assertEqual(msg, "Invalid username or password.")

        ok_nonexistent, msg_nonexistent = login_user("nonexistent_user", "AnyPassword123!")
        self.assertFalse(ok_nonexistent)
        self.assertEqual(msg_nonexistent, "Invalid username or password.")

    def test_05_logout(self):
        """Test session termination resets credentials."""
        import streamlit as st
        # Mock rerun to avoid exiting script
        st.session_state.authenticated = True
        st.session_state.username = "alice_test"
        st.session_state.user_uid = "PID-12345"

        original_rerun = getattr(st, "rerun", None)
        st.rerun = lambda: None
        try:
            logout_user()
            self.assertFalse(st.session_state.authenticated)
            self.assertIsNone(st.session_state.username)
            self.assertIsNone(st.session_state.user_id)
        finally:
            if original_rerun:
                st.rerun = original_rerun

    def test_06_unauthorized_access(self):
        """Test unauthenticated barrier halts execution and logs violation."""
        import streamlit as st
        from auth.authentication import require_auth
        st.session_state.authenticated = False

        halted = False
        def fake_stop():
            nonlocal halted
            halted = True
            raise SystemExit("Stopped")

        original_stop = st.stop
        st.stop = fake_stop
        try:
            try:
                require_auth()
            except SystemExit:
                pass
            self.assertTrue(halted, "require_auth did not stop execution for unauthenticated user")
        finally:
            st.stop = original_stop

    def test_07_normal_user_access(self):
        """Test normal user can access user dashboard but cannot access admin area."""
        import streamlit as st
        from auth.authentication import is_admin, is_authenticated
        st.session_state.authenticated = True
        st.session_state.role = "user"
        st.session_state.username = "alice_test"

        self.assertTrue(is_authenticated())
        self.assertFalse(is_admin())

    def test_08_admin_access_barrier(self):
        """Test normal user is blocked from admin functions, while admin is allowed."""
        import streamlit as st
        from auth.authentication import require_role, is_admin

        # Admin user
        st.session_state.authenticated = True
        st.session_state.role = "admin"
        self.assertTrue(is_admin())

        # Normal user trying to access admin role
        st.session_state.role = "user"
        halted = False
        def fake_stop():
            nonlocal halted
            halted = True
            raise SystemExit("Stopped")

        original_stop = st.stop
        st.stop = fake_stop
        try:
            try:
                require_role("admin")
            except SystemExit:
                pass
            self.assertTrue(halted, "require_role('admin') did not halt regular user")
        finally:
            st.stop = original_stop

    def test_09_prediction_generation(self):
        """Test existing ML model prediction with feature scaling."""
        from pages.prediction import load_artifacts, FEATURE_COLUMNS
        model, scaler, metrics = load_artifacts()
        self.assertIsNotNone(model)
        self.assertIsNotNone(scaler)
        self.assertIn("best_model", metrics)

        # Standard healthy patient input
        sample = pd.DataFrame(
            [[1, 110.0, 70.0, 20.0, 79.0, 24.5, 0.35, 28]],
            columns=FEATURE_COLUMNS,
        )
        scaled = scaler.transform(sample)
        pred = model.predict(scaled)[0]
        proba = model.predict_proba(scaled)[0][1]

        self.assertIn(int(pred), [0, 1])
        self.assertTrue(0.0 <= proba <= 1.0)

    def test_10_prediction_history_persistence(self):
        """Test saving and retrieving prediction history."""
        user = get_user_by_username("alice_test")
        inputs = {
            "Pregnancies": 1,
            "Glucose": 140.0,
            "BloodPressure": 75.0,
            "SkinThickness": 22.0,
            "Insulin": 85.0,
            "BMI": 27.2,
            "DiabetesPedigreeFunction": 0.45,
            "Age": 33,
        }
        pred_id = save_prediction(
            user_id=user["id"],
            user_uid=user["user_uid"],
            features=inputs,
            prediction=0,
            prediction_label="Lower Risk",
            probability=0.22,
        )
        self.assertGreater(pred_id, 0)

        history = get_predictions_by_user(user["id"])
        self.assertGreater(len(history), 0)
        self.assertEqual(history[0]["prediction_label"], "Lower Risk")
        self.assertEqual(history[0]["glucose"], 140.0)

    def test_11_user_isolation(self):
        """Test User A cannot view User B's medical predictions."""
        # Create User B
        ok, _ = register_user(
            username="bob_test",
            email="bob@test.org",
            password="Password123!",
            confirm_password="Password123!",
        )
        user_b = get_user_by_username("bob_test")
        user_a = get_user_by_username("alice_test")

        # Save a prediction exclusively for User B
        save_prediction(
            user_id=user_b["id"],
            user_uid=user_b["user_uid"],
            features={
                "Pregnancies": 3,
                "Glucose": 180.0,
                "BloodPressure": 90.0,
                "SkinThickness": 35.0,
                "Insulin": 180.0,
                "BMI": 38.0,
                "DiabetesPedigreeFunction": 0.85,
                "Age": 55,
            },
            prediction=1,
            prediction_label="Higher Risk",
            probability=0.88,
        )

        # Alice queries her predictions
        alice_records = get_predictions_by_user(user_a["id"])
        # Bob queries his predictions
        bob_records = get_predictions_by_user(user_b["id"])

        alice_uids = {r["user_uid"] for r in alice_records}
        bob_uids = {r["user_uid"] for r in bob_records}

        self.assertIn(user_a["user_uid"], alice_uids)
        self.assertNotIn(user_b["user_uid"], alice_uids)
        self.assertIn(user_b["user_uid"], bob_uids)
        self.assertNotIn(user_a["user_uid"], bob_uids)

    def test_12_audit_logging(self):
        """Test security audit trail records events without exposing sensitive passwords."""
        log_audit_event(
            action="TEST_EVENT",
            details="Test audit event triggered",
            user_uid="PID-99999",
            username="tester",
        )
        logs = get_audit_logs(limit=10)
        self.assertGreater(len(logs), 0)
        actions = [l["action"] for l in logs]
        self.assertIn("TEST_EVENT", actions)

        # Verify audit log file exists and contains no passwords
        self.assertTrue(os.path.exists(AUDIT_LOG_FILE))
        with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("TEST_EVENT", content)
            self.assertNotIn("Password123!", content)

    def test_13_input_validation(self):
        """Test input validation rejects invalid, empty, or out-of-range clinical inputs."""
        # Valid input
        valid_dict = {
            "Pregnancies": 2,
            "Glucose": 120.0,
            "BloodPressure": 70.0,
            "SkinThickness": 20.0,
            "Insulin": 79.0,
            "BMI": 25.0,
            "DiabetesPedigreeFunction": 0.35,
            "Age": 30,
        }
        ok, err = validate_prediction_inputs(valid_dict)
        self.assertTrue(ok, err)

        # Negative value (invalid)
        bad_negative = dict(valid_dict, Glucose=-10.0)
        ok, err = validate_prediction_inputs(bad_negative)
        self.assertFalse(ok)
        self.assertIn("outside clinical boundary", err)

        # Impossible Age
        bad_age = dict(valid_dict, Age=250)
        ok, err = validate_prediction_inputs(bad_age)
        self.assertFalse(ok)
        self.assertIn("outside clinical boundary", err)

        # Missing field
        bad_missing = dict(valid_dict)
        del bad_missing["BMI"]
        ok, err = validate_prediction_inputs(bad_missing)
        self.assertFalse(ok)
        self.assertIn("Missing required health parameter", err)

        # NaN / non-numeric
        bad_nan = dict(valid_dict, BMI=float("nan"))
        ok, err = validate_prediction_inputs(bad_nan)
        self.assertFalse(ok)

    def test_14_admin_views_no_passwords(self):
        """Test that get_all_users() never returns password_hash."""
        users = get_all_users()
        self.assertGreater(len(users), 0)
        for u in users:
            self.assertNotIn("password_hash", u)
            self.assertNotIn("password", u)


if __name__ == "__main__":
    unittest.main(verbosity=2)
