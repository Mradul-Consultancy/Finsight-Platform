# tests/test_anomalies.py
"""
Unit tests validating the 342 controlled anomalies claim on the FinSight platform.
"""

import sys
from pathlib import Path
import pytest
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.db import engine, DB_DIALECT

t_dq_anom = "dq.anomalies" if DB_DIALECT == "postgresql" else "dq_anomalies"

def test_exact_342_anomalies_detected():
    """Asserts that exactly 342 anomalies were quarantined into dq.anomalies."""
    df = pd.read_sql(f"SELECT COUNT(*) as total FROM {t_dq_anom}", engine)
    total_anomalies = df["total"].iloc[0]
    assert total_anomalies == 342, f"Expected exactly 342 anomalies, but found {total_anomalies}"

def test_anomaly_category_breakdown():
    """Validates the exact breakdown of the 6 controlled anomaly categories."""
    df = pd.read_sql(f"""
        SELECT anomaly_type, COUNT(*) as cnt
        FROM {t_dq_anom}
        GROUP BY anomaly_type
    """, engine)
    counts = dict(zip(df["anomaly_type"], df["cnt"]))
    
    assert counts.get("HIGH_AMOUNT", 0) == 60, f"Expected 60 HIGH_AMOUNT, got {counts.get('HIGH_AMOUNT')}"
    assert counts.get("RAPID_TRANSACTIONS", 0) == 60, f"Expected 60 RAPID_TRANSACTIONS, got {counts.get('RAPID_TRANSACTIONS')}"
    assert counts.get("LOCATION_MISMATCH", 0) == 60, f"Expected 60 LOCATION_MISMATCH, got {counts.get('LOCATION_MISMATCH')}"
    assert counts.get("DUPLICATE", 0) == 58, f"Expected 58 DUPLICATE, got {counts.get('DUPLICATE')}"
    assert counts.get("INVALID_ACCOUNT", 0) == 54, f"Expected 54 INVALID_ACCOUNT, got {counts.get('INVALID_ACCOUNT')}"
    assert counts.get("NEGATIVE_BALANCE", 0) == 50, f"Expected 50 NEGATIVE_BALANCE, got {counts.get('NEGATIVE_BALANCE')}"

def test_validation_run_logged():
    """Verifies that a validation run was logged in dq.validation_runs with high DQ score."""
    t_runs = "dq.validation_runs" if DB_DIALECT == "postgresql" else "dq_validation_runs"
    df = pd.read_sql(f"SELECT * FROM {t_runs} ORDER BY run_id DESC LIMIT 1", engine)
    assert not df.empty, "No validation runs recorded in audit table"
    assert df["anomaly_count"].iloc[0] == 342
    assert df["dq_score"].iloc[0] > 98.0
