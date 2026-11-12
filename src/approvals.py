"""Simple approval gate and append-only correction audit helper."""
import pandas as pd
from .config import DATA_PROCESSED, REPORTS

def create_approvals():
    payroll = pd.read_csv(DATA_PROCESSED / "payroll_inputs.csv")
    exceptions = pd.read_csv(DATA_PROCESSED / "exceptions.csv")
    blocked = set(zip(exceptions.employee_id, exceptions.pay_period_id))
    payroll["approval_status"] = payroll.apply(
        lambda r: "REJECTED" if (r.employee_id, r.pay_period_id) in blocked else "APPROVED",
        axis=1)
    payroll.to_csv(DATA_PROCESSED / "payroll_inputs.csv", index=False)
    approvals = payroll[["payroll_input_id", "employee_id", "pay_period_id", "approval_status"]].copy()
    approvals["approver"] = "Payroll Control Reviewer"
    approvals["comments"] = approvals.approval_status.map({
        "APPROVED": "Passed validation controls.",
        "REJECTED": "Blocked due to open payroll exception."
    })
    approvals.to_csv(REPORTS / "approvals.csv", index=False)
    return approvals

def append_correction_audit(record_id, field_name, old_value, new_value, corrected_by):
    """Append an audit event; do not overwrite prior audit events."""
    path = REPORTS / "correction_audit.csv"
    row = pd.DataFrame([{
        "record_id": record_id, "field_name": field_name,
        "old_value": str(old_value), "new_value": str(new_value),
        "corrected_by": corrected_by,
    }])
    row.to_csv(path, mode="a", header=not path.exists(), index=False)
