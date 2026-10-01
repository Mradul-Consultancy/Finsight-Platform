# src/validation.py
"""
Data Quality Validation & Quarantine Engine for FinSight.
Enforces business rules, quarantines the 342 controlled anomalies,
and populates core ledger and data quality audit tables.
"""

from datetime import datetime
import pandas as pd
from sqlalchemy import text
from src.db import engine, DB_DIALECT
from src.config import HIGH_AMOUNT_THRESHOLD, RAPID_TXN_SECONDS

def run_data_validation(eng=engine) -> dict:
    """
    Executes rule-based validation on raw transactions:
    1. Extracts anomalies into dq.anomalies
    2. Writes clean valid records into core.transactions
    3. Calculates and logs DQ score in dq.validation_runs
    """
    t_raw = "raw.transactions" if DB_DIALECT == "postgresql" else "raw_transactions"
    t_core_txns = "core.transactions" if DB_DIALECT == "postgresql" else "core_transactions"
    t_core_accs = "core.accounts" if DB_DIALECT == "postgresql" else "core_accounts"
    t_core_cust = "core.customers" if DB_DIALECT == "postgresql" else "core_customers"
    t_dq_anom = "dq.anomalies" if DB_DIALECT == "postgresql" else "dq_anomalies"
    t_dq_runs = "dq.validation_runs" if DB_DIALECT == "postgresql" else "dq_validation_runs"
    
    start_time = datetime.now()
    print("[Validation Engine] Commencing automated data quality run...")

    # Load raw records and accounts
    raw_df = pd.read_sql(f"SELECT * FROM {t_raw}", eng)
    valid_accs = set(pd.read_sql(f"SELECT account_id FROM {t_core_accs}", eng)["account_id"])
    cust_state_df = pd.read_sql(
        f"SELECT a.account_id, c.state as home_state FROM {t_core_accs} a JOIN {t_core_cust} c ON a.customer_id = c.customer_id",
        eng
    )
    acc_home_state_map = dict(zip(cust_state_df["account_id"], cust_state_df["home_state"]))

    total_records = len(raw_df)
    if total_records == 0:
        print("[Validation Engine] No raw records to evaluate.")
        return {}

    detected_anomalies = []
    quarantined_ids = set()

    # Sort by account and timestamp for sequential rules
    raw_df["txn_dt"] = pd.to_datetime(raw_df["transaction_timestamp"])
    raw_df = raw_df.sort_values(by=["account_id", "txn_dt"]).reset_index(drop=True)

    # ── Rule 1: High Amount Outliers (> 500,000) ──
    high_mask = raw_df["amount"] > HIGH_AMOUNT_THRESHOLD
    for _, row in raw_df[high_mask].iterrows():
        t_id = row["transaction_id"]
        quarantined_ids.add(t_id)
        detected_anomalies.append({
            "transaction_id": t_id,
            "account_id": row["account_id"],
            "anomaly_type": "HIGH_AMOUNT",
            "severity": "HIGH",
            "description": f"Transaction amount ₹{row['amount']:,.2f} exceeds threshold ₹{HIGH_AMOUNT_THRESHOLD:,.2f}"
        })

    # ── Rule 2: Invalid / Unregistered Account Reference ──
    for _, row in raw_df.iterrows():
        t_id = row["transaction_id"]
        if row["account_id"] not in valid_accs and t_id not in quarantined_ids:
            quarantined_ids.add(t_id)
            detected_anomalies.append({
                "transaction_id": t_id,
                "account_id": row["account_id"],
                "anomaly_type": "INVALID_ACCOUNT",
                "severity": "CRITICAL",
                "description": f"Account reference {row['account_id']} does not exist in core banking master ledger"
            })

    # ── Rule 3: Negative / Impossible Balance ──
    neg_mask = (raw_df["balance_after"] < 0) & (~raw_df["transaction_id"].isin(quarantined_ids))
    for _, row in raw_df[neg_mask].iterrows():
        t_id = row["transaction_id"]
        quarantined_ids.add(t_id)
        detected_anomalies.append({
            "transaction_id": t_id,
            "account_id": row["account_id"],
            "anomaly_type": "NEGATIVE_BALANCE",
            "severity": "HIGH",
            "description": f"Balance after transaction is negative: ₹{row['balance_after']:,.2f}"
        })

    # ── Rule 4: Duplicate Transactions (Same account, timestamp, amount, type) ──
    dup_cols = ["account_id", "transaction_timestamp", "amount", "transaction_type"]
    dup_mask = raw_df.duplicated(subset=dup_cols, keep=False) & (~raw_df["transaction_id"].isin(quarantined_ids))
    for _, row in raw_df[dup_mask].iterrows():
        t_id = row["transaction_id"]
        quarantined_ids.add(t_id)
        detected_anomalies.append({
            "transaction_id": t_id,
            "account_id": row["account_id"],
            "anomaly_type": "DUPLICATE",
            "severity": "MEDIUM",
            "description": "Duplicate payment collision detected across account, timestamp, and amount"
        })

    # ── Rule 5: Rapid Burst / Velocity Transactions (< 5s on same account) ──
    raw_df["time_diff"] = raw_df.groupby("account_id")["txn_dt"].diff().dt.total_seconds()
    rapid_mask = (raw_df["time_diff"] <= RAPID_TXN_SECONDS) & (raw_df["time_diff"] > 0) & (~raw_df["transaction_id"].isin(quarantined_ids))
    for idx, row in raw_df[rapid_mask].iterrows():
        t_id = row["transaction_id"]
        prev_row = raw_df.iloc[idx - 1]
        prev_id = prev_row["transaction_id"]
        
        if prev_id not in quarantined_ids:
            quarantined_ids.add(prev_id)
            detected_anomalies.append({
                "transaction_id": prev_id,
                "account_id": prev_row["account_id"],
                "anomaly_type": "RAPID_TRANSACTIONS",
                "severity": "HIGH",
                "description": f"Rapid velocity burst on account {prev_row['account_id']} within {RAPID_TXN_SECONDS}s"
            })
        if t_id not in quarantined_ids:
            quarantined_ids.add(t_id)
            detected_anomalies.append({
                "transaction_id": t_id,
                "account_id": row["account_id"],
                "anomaly_type": "RAPID_TRANSACTIONS",
                "severity": "HIGH",
                "description": f"Rapid velocity burst on account {row['account_id']} within {RAPID_TXN_SECONDS}s"
            })

    # ── Rule 6: Location Mismatch (ATM/Branch in different state from home state) ──
    for _, row in raw_df.iterrows():
        t_id = row["transaction_id"]
        if t_id in quarantined_ids:
            continue
        if row["channel"] in ("ATM", "BRANCH"):
            home_state = acc_home_state_map.get(row["account_id"])
            if home_state and row["state"] and row["state"] != home_state:
                quarantined_ids.add(t_id)
                detected_anomalies.append({
                    "transaction_id": t_id,
                    "account_id": row["account_id"],
                    "anomaly_type": "LOCATION_MISMATCH",
                    "severity": "MEDIUM",
                    "description": f"Transaction state '{row['state']}' mismatches customer home state '{home_state}'"
                })

    anomaly_count = len(detected_anomalies)
    valid_df = raw_df[~raw_df["transaction_id"].isin(quarantined_ids)].copy()
    valid_count = len(valid_df)
    invalid_count = total_records - valid_count
    
    dq_score = round((valid_count / total_records) * 100, 4)

    # Persist clean records into core.transactions and anomalies into dq.anomalies
    clean_cols = [
        "transaction_id", "account_id", "merchant_id", "transaction_timestamp",
        "transaction_type", "channel", "amount", "balance_after", "city", "state",
        "status", "device_id", "ip_address", "login_attempts"
    ]
    valid_to_insert = valid_df[clean_cols]
    anom_df = pd.DataFrame(detected_anomalies)

    with eng.begin() as conn:
        conn.execute(text(f"DELETE FROM {t_core_txns}"))
        conn.execute(text(f"DELETE FROM {t_dq_anom}"))
        
        valid_to_insert.to_sql(
            t_core_txns if DB_DIALECT == "sqlite" else "transactions",
            conn,
            schema=None if DB_DIALECT == "sqlite" else "core",
            if_exists="append",
            index=False
        )
        
        anom_df.to_sql(
            t_dq_anom if DB_DIALECT == "sqlite" else "anomalies",
            conn,
            schema=None if DB_DIALECT == "sqlite" else "dq",
            if_exists="append",
            index=False
        )
        
        # Log validation run
        conn.execute(text(f"""
            INSERT INTO {t_dq_runs} (
                run_started_at, run_completed_at, source_record_count,
                valid_record_count, invalid_record_count, anomaly_count,
                dq_score, status
            ) VALUES (
                :start_at, :end_at, :total, :valid, :invalid, :anom, :score, :status
            )
        """), {
            "start_at": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total": total_records,
            "valid": valid_count,
            "invalid": invalid_count,
            "anom": anomaly_count,
            "score": dq_score,
            "status": "SUCCESS"
        })

    summary = {
        "source_records": total_records,
        "valid_records": valid_count,
        "invalid_records": invalid_count,
        "anomalies_detected": anomaly_count,
        "dq_score": dq_score,
        "breakdown": anom_df["anomaly_type"].value_counts().to_dict() if not anom_df.empty else {}
    }

    print("\n" + "="*50)
    print("      DATA QUALITY VALIDATION RUN COMPLETED")
    print("="*50)
    print(f"  Source Records:        {total_records:,}")
    print(f"  Valid Records (Core):  {valid_count:,}")
    print(f"  Quarantined Anomalies: {anomaly_count:,}")
    print(f"  Data Quality Score:    {dq_score:.4f}%")
    print("  Category Breakdown:")
    for cat, cnt in summary["breakdown"].items():
        print(f"    - {cat}: {cnt}")
    print("="*50 + "\n")

    return summary

if __name__ == "__main__":
    run_data_validation()
