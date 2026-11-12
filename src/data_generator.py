"""Generate reproducible synthetic payroll input data."""
import json
from datetime import date, timedelta
from decimal import Decimal
import numpy as np
import pandas as pd  # type: ignore[reportMissingModuleSource]
from faker import Faker  # type: ignore[reportMissingImports]
from .config import (
    SEED, EMPLOYEE_COUNT, MONTHS, TARGET_SOURCE_RECORDS,
    DATA_RAW, DATA_GROUND_TRUTH
)

def _period_dates(month):
    year, mon = map(int, month.split("-"))
    start = date(year, mon, 1)
    if mon == 12:
        end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(year, mon + 1, 1) - timedelta(days=1)
    return start, end

def generate_data():
    """Create exactly 100,000 source rows and a separate planted-anomaly manifest."""
    rng = np.random.default_rng(SEED)
    fake = Faker("en_IN")
    Faker.seed(SEED)

    pay_groups = pd.DataFrame([
        {"pay_group_id": "PG-001", "name": "Monthly Salaried", "currency": "INR",
         "standard_hours_per_period": 160.0}
    ])
    employees = []
    for i in range(1, EMPLOYEE_COUNT + 1):
        employees.append({
            "employee_id": f"EMP-{i:05d}",
            "full_name": fake.name(),
            "email": f"employee{i:05d}@example.test",
            "department": str(rng.choice(["Engineering", "Finance", "HR", "Sales", "Operations"])),
            "pay_group_id": "PG-001",
            "active": True,
            "monthly_salary": round(float(rng.integers(22000, 95001)), 2),
        })
    employee_df = pd.DataFrame(employees)

    periods = []
    for idx, month in enumerate(MONTHS, 1):
        start, end = _period_dates(month)
        periods.append({"pay_period_id": f"PP-{idx:03d}", "period_name": month,
                        "start_date": start.isoformat(), "end_date": end.isoformat(),
                        "status": "OPEN"})

    time_rows, leave_rows, allowance_rows, deduction_rows = [], [], [], []
    # 30 time entries per employee over 3 months = 90,000.
    for eidx, emp in enumerate(employees, 1):
        for pidx, month in enumerate(MONTHS, 1):
            start, end = _period_dates(month)
            for day_idx in range(10):
                work_date = start + timedelta(days=min(day_idx * 2, (end-start).days))
                hours = round(float(rng.choice([7.5, 8.0, 8.5])), 2)
                time_rows.append({
                    "time_entry_id": f"TE-{eidx:05d}-{pidx:02d}-{day_idx+1:02d}",
                    "employee_id": emp["employee_id"], "pay_period_id": f"PP-{pidx:03d}",
                    "work_date": work_date.isoformat(), "hours": hours,
                    "approved": True,
                    "source_ref": f"TIMESHEET-{eidx:05d}-{pidx:02d}-{day_idx+1:02d}",
                })

    # 5,000 allowances + 5,000 deductions = exactly 100,000 total source rows.
    for i in range(1, 5001):
        emp_idx = int(rng.integers(1, EMPLOYEE_COUNT + 1))
        period_idx = int(rng.integers(1, 4))
        allowance_rows.append({
            "allowance_id": f"AL-{i:05d}", "employee_id": f"EMP-{emp_idx:05d}",
            "pay_period_id": f"PP-{period_idx:03d}",
            "allowance_type": str(rng.choice(["TRAVEL", "MEAL", "INTERNET"])),
            "amount": round(float(rng.integers(500, 5001)), 2),
            "source_ref": f"ALLOW-SRC-{i:05d}",
        })
        deduction_rows.append({
            "deduction_id": f"DE-{i:05d}", "employee_id": f"EMP-{emp_idx:05d}",
            "pay_period_id": f"PP-{period_idx:03d}",
            "deduction_type": str(rng.choice(["TAX", "PF", "INSURANCE"])),
            "amount": round(float(rng.integers(200, 4001)), 2),
            "source_ref": f"DEDUCT-SRC-{i:05d}",
        })

    time_df = pd.DataFrame(time_rows)
    leave_df = pd.DataFrame(columns=["leave_id", "employee_id", "pay_period_id", "leave_date",
                                     "leave_type", "days", "approved"])
    allowance_df = pd.DataFrame(allowance_rows)
    deduction_df = pd.DataFrame(deduction_rows)

    truth = []
    # 1. Excess hours: 10 time entries in one employee-period total 160+ hours.
    target_emp = "EMP-00001"
    target_period = "PP-001"
    mask = (time_df.employee_id == target_emp) & (time_df.pay_period_id == target_period)
    time_df.loc[mask, "hours"] = 18.0
    truth.append({"anomaly": "EXCESS_HOURS", "record_id": "TE-00001-01-01",
                  "employee_id": target_emp, "pay_period_id": target_period})
    # 2. Duplicate allowance: duplicate one row with a distinct ID but same business key/source.
    duplicate = allowance_df.iloc[0].copy()
    duplicate["allowance_id"] = "AL-DUPLICATE-0001"
    allowance_df = pd.concat([allowance_df, pd.DataFrame([duplicate])], ignore_index=True)
    truth.append({"anomaly": "DUPLICATE_ALLOWANCE", "record_id": "AL-DUPLICATE-0001",
                  "employee_id": duplicate.employee_id, "pay_period_id": duplicate.pay_period_id})
    # 3. Unapproved time entry.
    time_df.loc[0, "approved"] = False
    truth.append({"anomaly": "UNAPPROVED_TIME", "record_id": time_df.loc[0, "time_entry_id"],
                  "employee_id": time_df.loc[0, "employee_id"],
                  "pay_period_id": time_df.loc[0, "pay_period_id"]})
    # 4. Leave deduction applied twice: two same leave deduction entries.
    leave_rows = [
        {"leave_id": "LV-00001", "employee_id": "EMP-00002", "pay_period_id": "PP-001",
         "leave_date": "2026-08-12", "leave_type": "UNPAID", "days": 1.0, "approved": True}
    ]
    leave_df = pd.DataFrame(leave_rows)
    deduction_df = pd.concat([deduction_df, pd.DataFrame([{
        "deduction_id": "DE-LEAVE-0001", "employee_id": "EMP-00002",
        "pay_period_id": "PP-001", "deduction_type": "UNPAID_LEAVE",
        "amount": 1000.0, "source_ref": "LEAVE-LV-00001"
    }, {
        "deduction_id": "DE-LEAVE-0002", "employee_id": "EMP-00002",
        "pay_period_id": "PP-001", "deduction_type": "UNPAID_LEAVE",
        "amount": 1000.0, "source_ref": "LEAVE-LV-00001"
    }])], ignore_index=True)
    truth.append({"anomaly": "DUPLICATE_LEAVE_DEDUCTION", "record_id": "DE-LEAVE-0002",
                  "employee_id": "EMP-00002", "pay_period_id": "PP-001"})
    # 5. Reconciliation failure: deliberately store a bad expected payroll total.
    truth.append({"anomaly": "RECONCILIATION_FAILURE", "record_id": "PAYROLL-EMP-00003-PP-001",
                  "employee_id": "EMP-00003", "pay_period_id": "PP-001"})

    # Source count includes time + allowance + deduction + leave rows.
    # Keep target at 100,000 by reducing one regular deduction after adding anomaly rows.
    # 90,000 time + 5,001 allowance + 5,002 deductions + 1 leave = 100,004.
    # Remove four non-anomalous generated deductions to retain exactly 100,000.
    deduction_df = deduction_df.drop(index=[2, 3, 4, 5]).reset_index(drop=True)

    pay_groups.to_csv(DATA_RAW / "pay_groups.csv", index=False)
    employee_df.to_csv(DATA_RAW / "employees.csv", index=False)
    pd.DataFrame(periods).to_csv(DATA_RAW / "pay_periods.csv", index=False)
    time_df.to_csv(DATA_RAW / "time_entries.csv", index=False)
    leave_df.to_csv(DATA_RAW / "leave_records.csv", index=False)
    allowance_df.to_csv(DATA_RAW / "allowances.csv", index=False)
    deduction_df.to_csv(DATA_RAW / "deductions.csv", index=False)
    with open(DATA_GROUND_TRUTH / "ground_truth.json", "w", encoding="utf-8") as f:
        json.dump({"seed": SEED, "expected_source_records": TARGET_SOURCE_RECORDS,
                   "planted_anomalies": truth}, f, indent=2)
    return {"employees": len(employee_df), "time_entries": len(time_df),
            "leave_records": len(leave_df), "allowances": len(allowance_df),
            "deductions": len(deduction_df),
            "source_records": len(time_df) + len(leave_df) + len(allowance_df) + len(deduction_df)}
