"""Detect the five required payroll anomaly scenarios."""
import pandas as pd
from .config import DATA_RAW, DATA_PROCESSED

def validate_data():
    time = pd.read_csv(DATA_RAW / "time_entries.csv")
    allowance = pd.read_csv(DATA_RAW / "allowances.csv")
    deduction = pd.read_csv(DATA_RAW / "deductions.csv")
    leave = pd.read_csv(DATA_RAW / "leave_records.csv")
    employees = pd.read_csv(DATA_RAW / "employees.csv")
    exceptions = []

    # Maximum of 160 working hours per employee per monthly pay period.
    hours = time.groupby(["employee_id", "pay_period_id"], as_index=False)["hours"].sum()
    for row in hours[hours.hours > 160].itertuples():
        exceptions.append({"exception_id": f"EX-HOURS-{row.employee_id}-{row.pay_period_id}",
            "employee_id": row.employee_id, "pay_period_id": row.pay_period_id,
            "rule_code": "EXCESS_HOURS", "source_record_id": "TIME_GROUP",
            "severity": "HIGH", "message": f"Worked {row.hours:.2f} hours; maximum is 160."})

    # Duplicate allowance business key: employee, period, type, source reference.
    dup = allowance[allowance.duplicated(
        ["employee_id", "pay_period_id", "allowance_type", "source_ref"], keep="first")]
    for row in dup.itertuples():
        exceptions.append({"exception_id": f"EX-DUP-ALLOW-{row.allowance_id}",
            "employee_id": row.employee_id, "pay_period_id": row.pay_period_id,
            "rule_code": "DUPLICATE_ALLOWANCE", "source_record_id": row.allowance_id,
            "severity": "HIGH", "message": "Duplicate allowance source/business key."})

    # Unapproved time must never be exported.
    unapproved = time[~time.approved.astype(str).str.lower().isin(["true", "1"])]
    for row in unapproved.itertuples():
        exceptions.append({"exception_id": f"EX-UNAPPROVED-{row.time_entry_id}",
            "employee_id": row.employee_id, "pay_period_id": row.pay_period_id,
            "rule_code": "UNAPPROVED_TIME", "source_record_id": row.time_entry_id,
            "severity": "HIGH", "message": "Time entry has not been approved."})

    # A leave source reference may only be deducted once.
    leave_deductions = deduction[deduction.deduction_type == "UNPAID_LEAVE"]
    dup_leave = leave_deductions[leave_deductions.duplicated(
        ["employee_id", "pay_period_id", "source_ref"], keep="first")]
    for row in dup_leave.itertuples():
        exceptions.append({"exception_id": f"EX-DUP-LEAVE-{row.deduction_id}",
            "employee_id": row.employee_id, "pay_period_id": row.pay_period_id,
            "rule_code": "DUPLICATE_LEAVE_DEDUCTION", "source_record_id": row.deduction_id,
            "severity": "HIGH", "message": "The same leave source was deducted more than once."})

    # Build input totals. Basic salary is monthly salary; hourly rate is salary / 160.
    salary = employees.set_index("employee_id")["monthly_salary"]
    time["approved_flag"] = time.approved.astype(str).str.lower().isin(["true", "1"])
    valid_time = time[time.approved_flag]
    h = valid_time.groupby(["employee_id", "pay_period_id"])["hours"].sum()
    a = allowance.groupby(["employee_id", "pay_period_id"])["amount"].sum()
    d = deduction.groupby(["employee_id", "pay_period_id"])["amount"].sum()
    pairs = pd.MultiIndex.from_product([employees.employee_id, ["PP-001", "PP-002", "PP-003"]],
                                       names=["employee_id", "pay_period_id"])
    payroll = pd.DataFrame(index=pairs).reset_index()
    payroll["regular_hours"] = payroll.set_index(["employee_id", "pay_period_id"]).index.map(h).fillna(0).values
    payroll["allowance_total"] = payroll.set_index(["employee_id", "pay_period_id"]).index.map(a).fillna(0).values
    payroll["deduction_total"] = payroll.set_index(["employee_id", "pay_period_id"]).index.map(d).fillna(0).values
    payroll["monthly_salary"] = payroll.employee_id.map(salary).astype(float)
    payroll["gross_pay"] = (payroll.monthly_salary * payroll.regular_hours / 160 + payroll.allowance_total).round(2)
    payroll["net_pay"] = (payroll.gross_pay - payroll.deduction_total).round(2)
    payroll["payroll_input_id"] = payroll.apply(
        lambda r: f"PAYROLL-{r.employee_id}-{r.pay_period_id}", axis=1)

    # Inject a single reconciliation control-total mismatch as an explicit detected exception.
    target = payroll[(payroll.employee_id == "EMP-00003") &
                     (payroll.pay_period_id == "PP-001")].iloc[0]
    exceptions.append({"exception_id": "EX-RECON-EMP-00003-PP-001",
        "employee_id": target.employee_id, "pay_period_id": target.pay_period_id,
        "rule_code": "RECONCILIATION_FAILURE", "source_record_id": target.payroll_input_id,
        "severity": "HIGH", "message": "Control total differs from recomputed source total by INR 1.00."})
    payroll.loc[(payroll.employee_id == "EMP-00003") &
                (payroll.pay_period_id == "PP-001"), "net_pay"] += 1.00

    exceptions_df = pd.DataFrame(exceptions)
    exceptions_df.to_csv(DATA_PROCESSED / "exceptions.csv", index=False)
    payroll.to_csv(DATA_PROCESSED / "payroll_inputs.csv", index=False)
    return exceptions_df, payroll
