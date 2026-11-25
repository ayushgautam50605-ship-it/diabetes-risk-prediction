# Secure Diabetes Risk Prediction System Using Machine Learning

An enterprise-ready, security-hardened healthcare machine learning web application that accurately predicts diabetes risk categories from clinical indicators while enforcing strict **Information Security**, **Patient Confidentiality**, and **Role-Based Access Control (RBAC)**.

Built with **Python**, **scikit-learn**, **SQLite**, and **Streamlit**.

---

## 🔒 Key Security Features

### 1. User Registration & Authentication
- **Secure Password Hashing**: Passwords are cryptographically salted and hashed using **bcrypt** (12 work factor rounds). Passwords are never stored or logged in plain text.
- **Strict Input Validation**:
  - Username: 3–30 characters, alphanumeric and underscores only.
  - Email: RFC-compliant email format validation.
  - Password Complexity: Minimum 8 characters, requiring at least one uppercase letter, one lowercase letter, and one numeric digit.
- **Duplicate Prevention**: Automated duplicate detection prevents registration collisions on usernames and email addresses without disclosing sensitive account metadata.

### 2. Session Management
- **Streamlit-Compatible State Management**: Authenticated state is securely maintained in `st.session_state`.
- **Protected Route Barriers**: Unauthenticated users cannot access the prediction engine, personal health records, or administrative panels.
- **Secure Logout**: Revokes active session tokens, resets state, and prevents back-button / cached session reuse.

### 3. Role-Based Access Control (RBAC)
- **USER Role**:
  - Access to personalized diabetes risk prediction screening.
  - Access to personal historical assessment records.
  - Strictly blocked from accessing admin consoles or other patients' records.
- **ADMIN Role**:
  - Access to the administrative governance dashboard.
  - System-wide prediction metrics and population statistics.
  - Registered user management table (**passwords are strictly excluded**).
  - Searchable and exportable security audit logs.
  - Ability to execute model risk predictions.

### 4. Patient Data Protection & Anonymization
- **Anonymized Identifiers**: Each registered patient is assigned an anonymized Patient ID (e.g., `PID-84729`), decoupling clinical data from real identities.
- **User Record Isolation**: Database queries enforce multi-tenant isolation (`WHERE user_id = ?`). User A can never inspect or modify User B's clinical records.
- **Secret Isolation**: Database file paths, administrative defaults, and secret keys are loaded exclusively from `.env` and kept out of version control via `.gitignore`.

### 5. Security & Audit Logging
- **Comprehensive Event Trail**: Important security lifecycle events are automatically recorded into both the `audit_logs` database table and `logs/security_audit.log`:
  - `USER_REGISTER` — Account creations with assigned Patient IDs.
  - `LOGIN_SUCCESS` — Successful user & admin authentications.
  - `LOGIN_FAILURE` — Failed attempts (without logging attempted passwords).
  - `LOGOUT` — Explicit user session terminations.
  - `PREDICTION_GENERATED` — Clinical risk assessments performed.
  - `UNAUTHORIZED_ACCESS_ATTEMPT` — Blocked attempts to access protected pages.
  - `ADMIN_ACTION` — Administrative dashboard visits and log inspections.
- **No Sensitive Leakage**: Passwords, encryption keys, and raw authentication secrets are strictly scrubbed from logs.

### 6. Defense Against Injection & Malicious Inputs
- **100% Parameterized SQL**: All database operations use SQLite parameter placeholders (`?`). String concatenation is strictly prohibited, neutralizing SQL Injection (SQLi).
- **Clinical Range Verification**: Prediction inputs are guarded against negative values, NaN, Infinite values, out-of-boundary values, and unexpected types.

---

## 🩺 Machine Learning Engine (Preserved & Enhanced)

- **Dataset**: Pima Indians Diabetes Dataset (768 patient samples, 8 diagnostic features).
- **Preprocessing**: Physiologically invalid zero values (Glucose, Blood Pressure, Skin Thickness, Insulin, BMI) are treated as missing and imputed using median values; inputs are normalized using `StandardScaler`.
- **Model Architecture**: Logistic Regression / Random Forest benchmarked and selected by **ROC-AUC** score.
- **Features Evaluated**:
  1. Pregnancies (0 – 20)
  2. Glucose concentration (0 – 300 mg/dL)
  3. Blood Pressure (0 – 200 mm Hg)
  4. Skin Thickness (0 – 100 mm)
  5. Insulin (0 – 900 mu U/mL)
  6. Body Mass Index (BMI: 0 – 70)
  7. Diabetes Pedigree Function (0.000 – 3.000)
  8. Age (1 – 120 years)
- **Model Transparency**: Real-time display of accuracy, precision, recall, ROC-AUC score, and test confusion matrix.

---

## 📁 Project Structure

```
diabetes-risk-prediction/
│
├── app.py                      # Main application entry point & router
├── train_model.py              # ML model training, benchmarking & serialization
├── test_security_and_system.py # Automated security & unit test suite
├── requirements.txt            # Python dependencies
├── .env                        # Environment secrets & configuration
├── .env.example                # Template for environment configuration
├── .gitignore                  # Git ignore rules for secrets, DBs, and logs
│
├── model/
│   ├── diabetes_model.pkl      # Trained scikit-learn classifier
│   ├── scaler.pkl              # Fitted StandardScaler
│   └── metrics.json            # Model benchmark evaluation metrics
│
├── dataset/
│   └── diabetes.csv            # Pima Indians Diabetes dataset
│
├── database/
│   ├── __init__.py
│   ├── database.py             # SQLite parameterized persistence layer
│   └── diabetes_secure.db      # SQLite database file (auto-generated)
│
├── security/
│   ├── __init__.py
│   └── security.py             # Bcrypt hashing, input validation & sanitization
│
├── auth/
│   ├── __init__.py
│   └── authentication.py       # Authentication, session state & RBAC barriers
│
├── pages/
│   ├── __init__.py
│   ├── login.py                # User & Admin login interface
│   ├── register.py             # User registration with password complexity
│   ├── dashboard.py            # User dashboard with patient metrics
│   ├── prediction.py           # Diabetes prediction interface (ML preserved)
│   ├── history.py              # Personal prediction history with CSV download
│   ├── admin.py                # Admin dashboard (users, stats, audit trail)
│   └── about.py                # System architecture & clinical disclaimer
│
├── logs/
│   └── security_audit.log      # Persistent security audit trail log file
│
└── .streamlit/
    └── config.toml             # Streamlit security and navigation configuration
```

---

## ⚙️ Installation & Setup

### 1. Prerequisites
- **Python 3.9+** (Tested on Python 3.9, 3.10, 3.11, 3.12, 3.13, 3.14)
- Git (optional)

### 2. Install Dependencies
Open your terminal in the project directory and install the required packages:

```bash
pip install -r requirements.txt
```

Required packages:
- `streamlit`
- `scikit-learn`
- `pandas`
- `numpy`
- `joblib`
- `bcrypt`
- `python-dotenv`

### 3. Environment Configuration
Copy `.env.example` to `.env` (if not already present):

```bash
cp .env.example .env
```

Configuration parameters inside `.env`:
```ini
DATABASE_PATH=database/diabetes_secure.db
SECRET_KEY=e83bf699478f7e34c2ab1e90bc41d2f9281efcb06385a528652d5b62b1a89c3e
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@securehealth.local
ADMIN_INITIAL_PASSWORD=Admin@Secure2026!
PASSWORD_MIN_LENGTH=8
```

### 4. Database Initialization
The database initializes automatically on first run. To manually seed or verify the database, run:
```bash
python -c "from database.database import init_db; init_db(); print('Database ready.')"
```

---

## 🚀 Running the Application

Launch the Streamlit web application with:

```bash
streamlit run app.py
```

The app will start and open automatically in your browser at:
`http://localhost:8501`

---

## 🔑 Test Accounts for Evaluation

You can test the system immediately using either existing accounts or by registering a new user:

| Account Type | Username | Password | Role | Description |
|---|---|---|---|---|
| **Administrator** | `admin` | `Admin@Secure2026!` | `admin` | Full governance dashboard, user list, audit logs, analytics |
| **Normal Patient** | `john_doe` | `Pass1234!` | `user` | Patient dashboard, diabetes prediction, personal history |
| **New User** | *(Register your own)* | *(Choose min 8 chars with uppercase, lowercase, digit)* | `user` | Test end-to-end registration and patient ID assignment |

---

## 🧪 Automated Test Suite

A comprehensive automated test suite covers all 14 functional and security specifications:

```bash
python test_security_and_system.py
```

### Verified Test Cases:
1. `test_01_registration`: New user account creation and password hashing verification.
2. `test_02_duplicate_registration`: Duplicate username and email collision prevention.
3. `test_03_login_correct_password`: Bcrypt verification and session initialization.
4. `test_04_login_incorrect_password`: Generic error messaging without username enumeration.
5. `test_05_logout`: Clean session reset and credential wipe.
6. `test_06_unauthorized_access`: Halting unauthenticated requests to protected pages.
7. `test_07_normal_user_access`: User role boundary verification.
8. `test_08_admin_access_barrier`: Regular users blocked from admin governance console.
9. `test_09_prediction_generation`: ML model inference with feature scaling and probability.
10. `test_10_prediction_history_persistence`: Secure SQLite persistence of patient records.
11. `test_11_user_isolation`: Strict isolation (User A cannot view User B's records).
12. `test_12_audit_logging`: File and database audit trail with zero credential leakage.
13. `test_13_input_validation`: Rejection of out-of-boundary, negative, or NaN health values.
14. `test_14_admin_views_no_passwords`: Strict exclusion of password hashes from admin tables.

---

## 🛡️ Threat Mitigation & Security Standards

| Security Concern | Risk / Threat | Implemented Mitigation |
|---|---|---|
| **Broken Authentication** | Credential stuffing, brute force | Passwords hashed with salted bcrypt (12 rounds); generic login error messages prevent enumeration. |
| **SQL Injection (SQLi)** | Data exfiltration or tampering | 100% Parameterized queries using SQLite `?` markers. Zero string concatenation. |
| **Broken Access Control** | Privilege escalation | Guard functions (`require_auth()`, `require_role("admin")`) enforce page barriers and log violations. |
| **Sensitive Data Exposure** | Exposure of PII and health records | Anonymized Patient IDs (`PID-XXXXX`); strict multi-tenant isolation (`WHERE user_id = ?`); `.env` isolation. |
| **Security Misconfiguration** | Leakage of stack traces / passwords | Passwords scrubbed from logs and admin queries; Streamlit XSRF protection enabled. |
| **Data Integrity & Validation** | ML model crash / adversarial inputs | Strict range, type, and NaN checks on all 8 clinical parameters prior to model inference. |

---

## 📜 Disclaimer
This system is an academic, educational demonstration of securing machine learning systems. Risk categories and probabilities are statistical estimates and **do not constitute clinical diagnosis**. Always consult qualified medical practitioners for medical evaluation.
