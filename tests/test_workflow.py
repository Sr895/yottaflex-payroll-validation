from src.data_generator import generate_data
from src.validator import validate_data
from src.reconciliation import run_reconciliation
from src.approvals import create_approvals
from src.exporter import export_approved
from src.config import REPORTS, DATA_PROCESSED
import pandas as pd


def test_correction_audit_is_append_only(tmp_path, monkeypatch):
    import src.approvals as approvals

    monkeypatch.setattr(approvals, "REPORTS", tmp_path)

    approvals.append_correction_audit(
        "TEST-001", "net_pay", "25000.00", "24900.00", "Test Reviewer"
    )
    approvals.append_correction_audit(
        "TEST-002", "allowance_total", "1000.00", "1200.00", "Test Reviewer"
    )

    audit = pd.read_csv(tmp_path / "correction_audit.csv")

    assert len(audit) == 2
    assert audit.iloc[0]["record_id"] == "TEST-001"
    assert audit.iloc[1]["record_id"] == "TEST-002"
    assert audit.iloc[0]["old_value"] == 25000.00
    assert audit.iloc[0]["new_value"] == 24900.00

def test_required_anomalies_and_approval_gate():
    generate_data()
    exceptions, payroll = validate_data()
    rules = set(exceptions.rule_code)
    assert {"EXCESS_HOURS", "DUPLICATE_ALLOWANCE", "UNAPPROVED_TIME",
            "DUPLICATE_LEAVE_DEDUCTION", "RECONCILIATION_FAILURE"} <= rules
    summary = run_reconciliation()
    assert summary["failed_count"] >= 1
    create_approvals()
    result = export_approved()
    exported = pd.read_csv(REPORTS / "approved_payroll_export.csv")
    all_payroll = pd.read_csv(DATA_PROCESSED / "payroll_inputs.csv")
    assert (exported.payroll_input_id.isin(
        all_payroll[all_payroll.approval_status == "APPROVED"].payroll_input_id)).all()
    assert result["approved_records"] == len(exported)
