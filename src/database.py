"""Database connection, schema creation, and CSV-to-database loading."""
from datetime import date
from decimal import Decimal
import pandas as pd
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker
from .config import DATABASE_URL, DATA_RAW, DATA_PROCESSED, REPORTS
from .models import (
    Base, Employee, PayGroup, PayPeriod, TimeEntry, LeaveRecord, Allowance,
    Deduction, PayrollInput, ValidationRule, ExceptionRecord, Approval, PayrollExport
)

def get_engine(database_url=None):
    url = database_url or DATABASE_URL
    kwargs = {"future": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **kwargs)

def create_schema(engine=None):
    engine = engine or get_engine()
    Base.metadata.create_all(engine)
    return engine

def _records(path):
    return pd.read_csv(path).to_dict(orient="records")

def _dec(value):
    return Decimal(str(round(float(value), 2)))

def load_demo_data(engine=None):
    """Load generated source, payroll, exception, and approval rows into SQL tables.

    This resets the demo schema each run. Never use this reset behavior against
    a production payroll database.
    """
    engine = engine or get_engine()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    groups = _records(DATA_RAW / "pay_groups.csv")
    employees = _records(DATA_RAW / "employees.csv")
    periods = _records(DATA_RAW / "pay_periods.csv")
    times = _records(DATA_RAW / "time_entries.csv")
    leaves = _records(DATA_RAW / "leave_records.csv")
    allowances = _records(DATA_RAW / "allowances.csv")
    deductions = _records(DATA_RAW / "deductions.csv")
    payroll = _records(DATA_PROCESSED / "payroll_inputs.csv")
    exceptions = _records(DATA_PROCESSED / "exceptions.csv")
    approvals = _records(REPORTS / "approvals.csv")

    with engine.begin() as conn:
        conn.execute(PayGroup.__table__.insert(), [{
            "id": r["pay_group_id"], "name": r["name"], "currency": r["currency"],
            "standard_hours_per_period": _dec(r["standard_hours_per_period"])
        } for r in groups])
        conn.execute(PayPeriod.__table__.insert(), [{
            "id": r["pay_period_id"], "period_name": r["period_name"],
            "start_date": date.fromisoformat(r["start_date"]),
            "end_date": date.fromisoformat(r["end_date"]), "status": r["status"]
        } for r in periods])
        conn.execute(Employee.__table__.insert(), [{
            "id": r["employee_id"], "full_name": r["full_name"], "email": r["email"],
            "department": r["department"], "pay_group_id": r["pay_group_id"],
            "active": bool(r["active"])
        } for r in employees])
        conn.execute(TimeEntry.__table__.insert(), [{
            "id": r["time_entry_id"], "employee_id": r["employee_id"],
            "pay_period_id": r["pay_period_id"], "work_date": date.fromisoformat(r["work_date"]),
            "hours": _dec(r["hours"]), "approved": str(r["approved"]).lower() in ("true", "1"),
            "source_ref": r["source_ref"]
        } for r in times])
        if leaves:
            conn.execute(LeaveRecord.__table__.insert(), [{
                "id": r["leave_id"], "employee_id": r["employee_id"],
                "pay_period_id": r["pay_period_id"], "leave_date": date.fromisoformat(r["leave_date"]),
                "leave_type": r["leave_type"], "days": _dec(r["days"]),
                "approved": str(r["approved"]).lower() in ("true", "1")
            } for r in leaves])
        conn.execute(Allowance.__table__.insert(), [{
            "id": r["allowance_id"], "employee_id": r["employee_id"],
            "pay_period_id": r["pay_period_id"], "allowance_type": r["allowance_type"],
            "amount": _dec(r["amount"]), "source_ref": r["source_ref"]
        } for r in allowances])
        conn.execute(Deduction.__table__.insert(), [{
            "id": r["deduction_id"], "employee_id": r["employee_id"],
            "pay_period_id": r["pay_period_id"], "deduction_type": r["deduction_type"],
            "amount": _dec(r["amount"]), "source_ref": r["source_ref"]
        } for r in deductions])
        conn.execute(PayrollInput.__table__.insert(), [{
    "id": r["payroll_input_id"],
    "employee_id": r["employee_id"],
    "pay_period_id": r["pay_period_id"],
    "regular_hours": _dec(r["regular_hours"]),
    "leave_days": Decimal("0"),
    "allowance_total": _dec(r["allowance_total"]),
    "deduction_total": _dec(r["deduction_total"]),
    "gross_pay": _dec(r["gross_pay"]),
    "net_pay": _dec(r["net_pay"]),
    "status": r["approval_status"]
} for r in payroll])
        rules = [
            ("RULE-001", "EXCESS_HOURS", "Working hours exceed 160 in a pay period."),
            ("RULE-002", "DUPLICATE_ALLOWANCE", "Allowance business/source key must be unique."),
            ("RULE-003", "UNAPPROVED_TIME", "Unapproved time entries cannot be exported."),
            ("RULE-004", "DUPLICATE_LEAVE_DEDUCTION", "A leave source can only be deducted once."),
            ("RULE-005", "RECONCILIATION_FAILURE", "Payroll totals must reconcile to source calculations."),
        ]
        conn.execute(ValidationRule.__table__.insert(), [
            {"id": i, "rule_code": code, "description": desc, "enabled": True}
            for i, code, desc in rules
        ])
        payroll_id_map = {(r["employee_id"], r["pay_period_id"]): r["payroll_input_id"] for r in payroll}
        conn.execute(ExceptionRecord.__table__.insert(), [{
            "id": r["exception_id"],
            "payroll_input_id": payroll_id_map.get((r["employee_id"], r["pay_period_id"])),
            "source_record_id": r["source_record_id"], "rule_code": r["rule_code"],
            "severity": r["severity"], "message": r["message"], "status": "OPEN"
        } for r in exceptions])
        conn.execute(Approval.__table__.insert(), [{
            "id": f"APR-{i:06d}", "payroll_input_id": r["payroll_input_id"],
            "approver": r["approver"], "decision": r["approval_status"],
            "comments": r["comments"]
        } for i, r in enumerate(approvals, 1)])
        exports = []
        for period in periods:
            count = sum(1 for r in payroll if r["pay_period_id"] == period["pay_period_id"]
                        and r["approval_status"] == "APPROVED")
            exports.append({
                "id": f"EXP-{period['pay_period_id']}", "pay_period_id": period["pay_period_id"],
                "file_name": f"approved_payroll_export_{period['period_name']}.csv",
                "record_count": count, "status": "COMPLETED"
            })
        conn.execute(PayrollExport.__table__.insert(), exports)

    return {
        "employees_loaded": len(employees), "time_entries_loaded": len(times),
        "leave_records_loaded": len(leaves), "allowances_loaded": len(allowances),
        "deductions_loaded": len(deductions), "payroll_inputs_loaded": len(payroll),
        "exceptions_loaded": len(exceptions), "approvals_loaded": len(approvals),
    }
