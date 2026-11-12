# Yottaflex Payroll Validation & Reconciliation System

A beginner-friendly Python demonstration of payroll input validation, reconciliation, exception handling, approval gating, audit events, and controlled exports.

## 1. Business Objective

Validate employee time, leave, allowances, and deductions before payroll export.

The system identifies exceptions, reconciles payroll calculations, blocks records with unresolved exceptions, and exports only approved payroll inputs.

## 2. Technology Stack

- Python 3.13
- Pandas and NumPy
- Faker for synthetic data
- SQLAlchemy for database integration
- SQLite as the default database
- PostgreSQL support through `DATABASE_URL`
- Pytest for automated testing
- CSV, JSON, and SQL exports

## 3. Project Requirements

- 3,000 synthetic employees.
- Three monthly pay periods: August, September, and October 2026.
- Exactly 100,000 source records.
- Fixed random seed: `20261022`.
- Stable record IDs.
- Independent anomaly manifest in `data/ground_truth/ground_truth.json`.
- Five planted anomaly scenarios:
  1. Excess working hours.
  2. Duplicate allowance.
  3. Unapproved time entry.
  4. Duplicate unpaid-leave deduction.
  5. Payroll reconciliation mismatch.
- Exception reporting and reconciliation.
- Approval and rejection decisions.
- Approved-only CSV, JSON, and SQL exports.
- Append-only correction audit helper.

## 4. Project Setup

Requirements: Python 3.13 recommended.

Open the project folder in VS Code and run these commands in PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## 5. Execute the Project

Run:

```powershell
python main.py
```

The application executes the following seven stages:

1. Generate synthetic employee and payroll source data.
2. Validate records and identify anomalies.
3. Reconcile payroll calculations.
4. Apply the approval gate.
5. Export approved payroll records.
6. Load workflow data into the SQLAlchemy database.
7. Display completion status.

The default database is SQLite. No external database server or API key is required for the default demonstration.

## 6. Run Automated Tests

Execute:

```powershell
python -m pytest -v
```

The tests cover:

- Synthetic data generation.
- Required anomaly detection.
- Reconciliation failure detection.
- Approval-only exports.
- Append-only correction audit events.

Latest verified result: **3 tests passed**.

## 7. Expected Demonstration Results

| Metric | Expected result |
|---|---:|
| Employees | 3,000 |
| Source records | 100,000 |
| Payroll inputs | 9,000 |
| Detected anomaly types | 5 |
| Reconciliation failures | 1 |
| Approved payroll records | 8,996 |
| Rejected payroll records | 4 |

## 8. Project Structure

```text
yottaflex-payroll-validation/
│
├── main.py
├── requirements.txt
├── README.md
├── PROMPT_HISTORY.md
├── SUBMISSION_CHECKLIST.md
│
├── src/
│   ├── config.py
│   ├── data_generator.py
│   ├── validator.py
│   ├── reconciliation.py
│   ├── approvals.py
│   ├── exporter.py
│   ├── database.py
│   └── models.py
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── ground_truth/
│       └── ground_truth.json
│
├── reports/
│
└── tests/
    ├── test_generator.py
    └── test_workflow.py
```

## 9. Database Configuration

SQLite is the default database.

To use PostgreSQL, create a database and configure the connection string:

```powershell
$env:DATABASE_URL="postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/yottaflex"
python main.py
```

Do not commit real passwords or credentials. Keep secrets in environment variables or an ignored local `.env` file.

The demo database is reset and reloaded on each execution. Never point this demonstration at a production database.

## 10. Important Assumptions and Limitations

- The demonstration uses 160 hours as the monthly working-hours threshold.
- Monthly salary is converted to an hourly rate using salary divided by 160.
- The reconciliation mismatch is intentionally planted as an INR 1.00 difference.
- Synthetic data is used instead of real employee information.
- The correction audit helper records correction events, but a complete correction-and-revalidation workflow is not implemented.
- This is a recruitment-assignment prototype, not a production payroll engine.

Actual payroll systems require employer-specific overtime, leave, tax, pay-period, and approval policies.

## 11. AI Usage

AI tools were used during development for technical explanations, debugging assistance, test improvements, and documentation.

See `PROMPT_HISTORY.md` for the development prompt history and details of personal review and validation.
