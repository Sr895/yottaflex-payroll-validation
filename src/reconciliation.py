"""Reconcile source totals to payroll calculation totals."""
import pandas as pd
from .config import DATA_RAW, DATA_PROCESSED, REPORTS

def run_reconciliation():
    payroll = pd.read_csv(DATA_PROCESSED / "payroll_inputs.csv")
    # Recompute the net amount from the calculated gross and deductions.
    expected = (payroll.gross_pay - payroll.deduction_total).round(2)
    payroll["recomputed_net_pay"] = expected
    payroll["difference"] = (payroll.net_pay - expected).round(2)
    payroll["reconciled"] = payroll.difference.abs() < 0.005
    payroll.to_csv(DATA_PROCESSED / "payroll_inputs.csv", index=False)
    summary = {
        "payroll_input_count": int(len(payroll)),
        "reconciled_count": int(payroll.reconciled.sum()),
        "failed_count": int((~payroll.reconciled).sum()),
        "net_pay_difference_total": round(float(payroll.difference.sum()), 2),
    }
    pd.DataFrame([summary]).to_csv(REPORTS / "reconciliation_summary.csv", index=False)
    return summary
