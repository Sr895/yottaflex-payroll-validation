"""Run the end-to-end Yottaflex payroll validation demo."""
import json
from src.data_generator import generate_data
from src.validator import validate_data
from src.reconciliation import run_reconciliation
from src.approvals import create_approvals
from src.exporter import export_approved, export_sql_insert
from src.database import get_engine, load_demo_data

def main():
    print("1/7 Generating reproducible synthetic data...")
    counts = generate_data()
    print(json.dumps(counts, indent=2))

    print("\n2/7 Running validation rules...")
    exceptions, payroll = validate_data()
    print(f"Detected {len(exceptions)} exceptions.")
    print(exceptions.rule_code.value_counts().to_string())

    print("\n3/7 Reconciling payroll...")
    reconciliation = run_reconciliation()
    print(json.dumps(reconciliation, indent=2))

    print("\n4/7 Applying approval gate...")
    approvals = create_approvals()
    print(approvals.approval_status.value_counts().to_string())

    print("\n5/7 Exporting approved payroll only...")
    export_result = export_approved()
    sql_path = export_sql_insert()
    print(json.dumps(export_result, indent=2))
    print(f"SQL export: {sql_path}")

    print("\n6/7 Loading all workflow data into SQLAlchemy database...")
    loaded = load_demo_data(get_engine())
    print(json.dumps(loaded, indent=2))

    print("\n7/7 Complete. Review reports/, data/, and yottaflex_payroll.db.")
    print("WARNING: the demo database is reset and reloaded on each run.")

if __name__ == "__main__":
    main()
