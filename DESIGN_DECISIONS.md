# Design Decisions and Technical Reasoning

## Yottaflex Payroll Validation & Reconciliation System

**Developer:** SRINIVASULA REDDY  
**Project type:** Python-based payroll validation prototype  
**Purpose:** Demonstrate data validation, reconciliation, exception management, approval controls, audit events, and controlled payroll exports.

---

## 1. Problem Understanding

Payroll processing depends on multiple source records, including employee information, time entries, leave records, allowances, and deductions.

Incorrect or duplicate source records can result in inaccurate payroll calculations.

The objective of this project is to build a validation layer before payroll export.

The system should:

1. Generate reproducible employee and payroll source data.
2. Validate source records against defined business rules.
3. Identify and report anomalies.
4. Reconcile calculated payroll amounts.
5. Prevent payroll records with unresolved exceptions from being exported.
6. Maintain approval and correction audit information.
7. Produce controlled payroll exports.

## 2. Architecture Decision

I selected a modular architecture instead of implementing the entire workflow in one Python file.

Each module has a separate responsibility.

| Module | Responsibility |
|---|---|
| `config.py` | Central configuration and project paths |
| `data_generator.py` | Synthetic employee and payroll data generation |
| `validator.py` | Business rule validation and exception detection |
| `reconciliation.py` | Payroll calculation reconciliation |
| `approvals.py` | Approval gate and correction audit helper |
| `exporter.py` | Approved payroll CSV, JSON, and SQL exports |
| `models.py` | SQLAlchemy database models |
| `database.py` | Database creation and data loading |
| `main.py` | End-to-end workflow orchestration |

**Why this design?**

Separating responsibilities makes the application easier to understand, debug, test, and extend.

For example, a validation rule can be modified without rewriting the export logic.

## 3. Technology Selection

| Technology | Reason for selection |
|---|---|
| Python | Main application and business logic |
| Pandas | Reading, grouping, validating, and exporting tabular records |
| NumPy | Reproducible random data generation |
| Faker | Generating realistic synthetic employee information |
| SQLAlchemy | Defining relational database models and loading records |
| SQLite | Simple local database without server setup |
| PostgreSQL | Alternative database through connection configuration |
| Pytest | Automated verification of application behavior |
| CSV and JSON | Portable data exchange formats |
| SQL | Demonstration of controlled database export |

The technology choices prioritize ease of execution, readability, and demonstration of the payroll workflow.

## 4. Deterministic Data Generation

**Decision:** Use a fixed random seed of `20261022`.

The project generates:

- 3,000 synthetic employees.
- Three monthly pay periods: August, September, and October 2026.
- 90,000 time entries.
- 5,001 allowance records.
- 4,998 deduction records.
- 1 leave record.

Total source records:

`90,000 + 5,001 + 4,998 + 1 = 100,000`

**Why deterministic data?**

A fixed seed makes the synthetic dataset reproducible under the same generator and dependency behavior. Stable IDs make individual records easier to trace and compare.

An independent `ground_truth.json` file records the intentionally planted anomaly IDs.

## 5. Validation Rule Decisions

Five anomaly scenarios were selected to demonstrate common payroll control problems.

### Rule 1: Excess working hours

**Business problem:** An employee's recorded hours exceed the monthly standard.

**Implementation approach:** Group time entries by employee and pay period, calculate total hours, and compare the result against the 160-hour threshold.

**Expected exception:** `EXCESS_HOURS`

### Rule 2: Duplicate allowance

**Business problem:** The same allowance source may be included more than once.

**Implementation approach:** Identify repeated allowance business keys using employee, pay period, allowance type, and source reference.

**Expected exception:** `DUPLICATE_ALLOWANCE`

### Rule 3: Unapproved time entry

**Business problem:** Unapproved time must not be treated as approved payroll input.

**Implementation approach:** Check the approval status of time entries and flag entries that are not approved.

**Expected exception:** `UNAPPROVED_TIME`

### Rule 4: Duplicate unpaid-leave deduction

**Business problem:** The same unpaid-leave source may be deducted twice.

**Implementation approach:** Identify repeated unpaid-leave deduction references for the same employee and pay period.

**Expected exception:** `DUPLICATE_LEAVE_DEDUCTION`

### Rule 5: Payroll reconciliation mismatch

**Business problem:** The calculated net pay differs from the expected net pay.

**Implementation approach:** Introduce a controlled INR 1.00 mismatch for a designated payroll input and compare calculated and recorded net pay.

**Expected exception:** `RECONCILIATION_FAILURE`

**Why plant anomalies intentionally?**

A controlled dataset with known anomalies allows the validator and reconciliation process to be tested against expected results instead of relying on random data errors.

## 6. Payroll Calculation and Reconciliation

The demonstration uses the following simplified calculation:

`Hourly rate = Monthly salary / 160`

`Gross pay = Hourly rate × Approved regular hours + Allowances`

`Net pay = Gross pay - Deductions`

The reconciliation module independently recomputes:

`Expected net pay = Gross pay - Deduction total`

It then calculates:

`Difference = Recorded net pay - Expected net pay`

A payroll input is reconciled when the absolute difference is less than 0.005.

**Design decision:** Use a small INR 1.00 planted mismatch to demonstrate that reconciliation can identify an incorrect payroll amount.

**Trade-off:** This is a simplified demonstration. It does not implement a complete statutory payroll calculation, tax engine, overtime policy, or employer-specific leave calculation.

## 7. Approval Gate

**Decision:** Payroll inputs with unresolved exceptions must not be approved.

The application identifies employee and pay-period combinations associated with exceptions.

These combinations are marked `REJECTED`; other payroll inputs are marked `APPROVED`.

Observed result:

| Approval status | Records |
|---|---:|
| APPROVED | 8,996 |
| REJECTED | 4 |
| Total | 9,000 |

**Why this approach?**

It demonstrates a simple control boundary between payroll calculation and payroll export.

Rejected records remain available in the workflow for investigation rather than being silently discarded.

**Limitation:** This prototype uses a fixed demonstration approver. It does not implement real user authentication, role-based authorization, or a multi-level approval workflow.

## 8. Correction Audit Decision

The project includes an append-only correction audit helper.

It records:

- Record ID.
- Field name.
- Old value.
- New value.
- Person identified as making the correction.

**Why append-only?**

Overwriting an earlier audit event would make it difficult to understand what changed. Appending events preserves the earlier recorded history.

An automated test verifies that two audit events are retained.

**Current limitation:** The helper records audit events but does not yet implement a complete correction workflow that updates payroll data, reruns validation, and obtains approval again. The audit CSV is also a demonstration mechanism, not a tamper-proof production audit store.

## 9. Database Design

SQLAlchemy is used to define and load the relational entities.

The demonstration includes:

1. Employee
2. PayGroup
3. PayPeriod
4. TimeEntry
5. LeaveRecord
6. Allowance
7. Deduction
8. PayrollInput
9. ValidationRule
10. Exception
11. Approval
12. PayrollExport

**Why SQLAlchemy?**

It provides a structured way to represent database entities and work with either SQLite or PostgreSQL.

**Why SQLite by default?**

SQLite makes the project easy for reviewers to execute without installing or configuring a separate database server.

PostgreSQL can be selected using the `DATABASE_URL` environment variable.

**Limitation:** The demo database is dropped and recreated on each run. This is suitable for a disposable demonstration database, not for production data.

## 10. Controlled Export Design

The exporter filters payroll inputs using:

`approval_status == "APPROVED"`

Only approved records are exported.

Supported formats:

- CSV
- JSON
- SQL INSERT statements

**Why filter before export?**

The export process should not include payroll records that failed the approval gate.

Rejected records remain in the internal workflow, while the export contains approved records only.

Observed result: 8,996 approved payroll records exported.

## 11. Testing Strategy

Pytest is used to verify key workflow behavior.

The current tests cover:

| Test | What it verifies |
|---|---|
| Generator test | Expected synthetic data counts |
| Workflow test | Required anomaly detection, reconciliation, approval gate, and approved-only export |
| Audit test | Multiple correction audit events are appended without overwriting earlier events |

Latest observed test result:

`3 passed`

Additional manual verification included:

- Checking CSV record counts.
- Inspecting the ground-truth anomaly manifest.
- Checking reconciliation failures.
- Checking approved and rejected record counts.
- Querying SQLite table counts.
- Checking SQL export statement counts.
- Executing the complete application using `python main.py`.

## 12. Key Trade-offs

| Decision | Benefit | Trade-off |
|---|---|---|
| Synthetic data | Safe and reproducible demonstration | Does not represent actual payroll data |
| Fixed 160-hour threshold | Simple validation rule | Employer policies may differ |
| SQLite default | Easy local execution | Limited production suitability |
| Pandas processing | Clear tabular operations | Large-scale production workloads may need optimization |
| Fixed demonstration approver | Easy to demonstrate approval logic | No real authentication |
| Intentional reconciliation mismatch | Makes failure detection testable | Does not simulate every real reconciliation failure |
| CSV audit helper | Simple append-only demonstration | Not tamper-proof |

## 13. Known Limitations and Future Improvements

The current prototype is not a complete production payroll engine.

Potential improvements include:

1. Calculate and validate approved leave days in payroll inputs.
2. Implement a complete correction, revalidation, and reapproval workflow.
3. Add role-based access control and real approver identities.
4. Add transaction management and stronger database audit controls.
5. Implement employer-specific overtime, tax, and leave policies.
6. Add stronger reconciliation between individual source aggregates and payroll totals.
7. Add more boundary, duplicate, and negative-value test cases.
8. Improve performance for larger payroll datasets.

## 14. How I Know the Solution Works

The solution was executed locally using Python 3.13.

The observed results were:

| Verification | Result |
|---|---:|
| Employees generated | 3,000 |
| Source records generated | 100,000 |
| Payroll inputs generated | 9,000 |
| Anomaly types detected | 5 |
| Reconciliation failures | 1 |
| Approved records | 8,996 |
| Rejected records | 4 |
| Automated tests | 3 passed |

The complete workflow ran through all seven stages, including database loading and approved-only exports.

These results demonstrate the expected behavior of the recruitment-assignment prototype. They do not establish production readiness.

## 15. Final Reflection

The main engineering objective was to build a workflow in which payroll data is validated before it reaches the export stage.

The project demonstrates how data generation, business validation, reconciliation, exception handling, approval controls, database integration, and testing can work together.

The design prioritizes traceability, reproducibility, and clear separation of responsibilities while documenting the limitations that would need to be addressed before production use.