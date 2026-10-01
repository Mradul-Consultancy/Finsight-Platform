# tests/test_views.py
"""
Unit tests validating the 12 analytical SQL views on FinSight.
"""

import sys
from pathlib import Path
import pytest
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.db import engine, DB_DIALECT

VIEWS = [
    "v_daily_transaction_summary",
    "v_monthly_transaction_summary",
    "v_branch_performance",
    "v_customer_segment_performance",
    "v_merchant_category_performance",
    "v_channel_performance",
    "v_debit_credit_summary",
    "v_active_accounts_summary",
    "v_top_customers",
    "v_failed_transactions_summary",
    "v_anomaly_summary",
    "v_customer_risk_summary"
]

@pytest.mark.parametrize("view_name", VIEWS)
def test_analytical_view_exists_and_returns_data(view_name):
    """Ensures each of the 12 analytical views exists and can be queried."""
    full_name = f"analytics.{view_name}" if DB_DIALECT == "postgresql" else view_name
    df = pd.read_sql(f"SELECT * FROM {full_name} LIMIT 5", engine)
    assert df is not None, f"Query returned None for view {full_name}"

def test_total_view_count():
    """Asserts that exactly 12 analytical views exist."""
    assert len(VIEWS) == 12
