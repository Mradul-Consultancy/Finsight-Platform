# tests/test_validation.py
"""
Data quality and validation unit tests for FinSight banking engine.
"""

import sys
from pathlib import Path
import pytest
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.db import engine, DB_DIALECT

t_core_txns = "core.transactions" if DB_DIALECT == "postgresql" else "core_transactions"
t_core_acc = "core.accounts" if DB_DIALECT == "postgresql" else "core_accounts"

def test_no_negative_transaction_amounts():
    """Rule 1: No valid core transaction has amount <= 0."""
    df = pd.read_sql(f"SELECT COUNT(*) as bad_count FROM {t_core_txns} WHERE amount <= 0", engine)
    assert df["bad_count"].iloc[0] == 0, "Found core transactions with amount <= 0"

def test_no_invalid_account_references():
    """Rule 2: Every core transaction must reference an existing core account."""
    sql = f"""
        SELECT COUNT(*) as orphan_count
        FROM {t_core_txns} t
        LEFT JOIN {t_core_acc} a ON t.account_id = a.account_id
        WHERE a.account_id IS NULL
    """
    df = pd.read_sql(sql, engine)
    assert df["orphan_count"].iloc[0] == 0, "Found core transactions referencing nonexistent accounts"

def test_no_impossible_negative_balances():
    """Rule 3: No valid core transaction leaves a negative balance."""
    df = pd.read_sql(f"SELECT COUNT(*) as bad_count FROM {t_core_txns} WHERE balance_after < 0", engine)
    assert df["bad_count"].iloc[0] == 0, "Found core transactions with negative balance"

def test_no_excessive_high_amounts_in_core():
    """Rule 4: Transactions exceeding 500,000 threshold must be quarantined."""
    df = pd.read_sql(f"SELECT COUNT(*) as bad_count FROM {t_core_txns} WHERE amount > 500000", engine)
    assert df["bad_count"].iloc[0] == 0, "Transactions > 500,000 found in clean core ledger"
