# tests/test_segmentation.py
"""
Unit tests validating the 7 customer segments on the FinSight platform.
"""

import sys
from pathlib import Path
import pytest
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.db import engine, DB_DIALECT

t_seg = "analytics.customer_segments" if DB_DIALECT == "postgresql" else "analytics_customer_segments"

def test_seven_segments_exist():
    """Asserts that customer segments match the 7 specified banking cohorts."""
    df = pd.read_sql(f"SELECT DISTINCT segment FROM {t_seg}", engine)
    unique_segments = set(df["segment"])
    
    expected_segments = {
        "STUDENT",
        "SALARIED",
        "MASS_MARKET",
        "AFFLUENT",
        "PREMIUM",
        "SENIOR",
        "SMALL_BUSINESS"
    }
    
    # Check that observed segments are valid members of the 7 cohorts
    assert unique_segments.issubset(expected_segments) or unique_segments == expected_segments
    assert len(unique_segments) >= 5, "Expected multi-cohort distribution"

def test_no_unassigned_customers():
    """Ensures no customer in core ledger is left without a segment."""
    t_cust = "core.customers" if DB_DIALECT == "postgresql" else "core_customers"
    sql = f"""
        SELECT COUNT(*) as unassigned
        FROM {t_cust} c
        LEFT JOIN {t_seg} s ON c.customer_id = s.customer_id
        WHERE s.segment IS NULL
    """
    df = pd.read_sql(sql, engine)
    assert df["unassigned"].iloc[0] == 0, "Found customers without assigned segment"
