"""Central project configuration."""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SEED = 20261022
EMPLOYEE_COUNT = 3000
MONTHS = ["2026-08", "2026-09", "2026-10"]
TARGET_SOURCE_RECORDS = 100_000
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///yottaflex_payroll.db")

DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_GROUND_TRUTH = PROJECT_ROOT / "data" / "ground_truth"
REPORTS = PROJECT_ROOT / "reports"

for folder in [DATA_RAW, DATA_PROCESSED, DATA_GROUND_TRUTH, REPORTS]:
    folder.mkdir(parents=True, exist_ok=True)
