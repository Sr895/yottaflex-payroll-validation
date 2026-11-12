from src.data_generator import generate_data
from src.config import EMPLOYEE_COUNT, TARGET_SOURCE_RECORDS

def test_generator_counts():
    counts = generate_data()
    assert counts["employees"] == EMPLOYEE_COUNT
    assert counts["source_records"] == TARGET_SOURCE_RECORDS
