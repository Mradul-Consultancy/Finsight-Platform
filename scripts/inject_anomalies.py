# scripts/inject_anomalies.py
"""
Injects exactly 342 controlled, mathematically identifiable data anomalies
across 6 distinct risk and data quality categories into the raw dataset:

1. HIGH_AMOUNT: 60 records (amount > ₹500,000)
2. RAPID_TRANSACTIONS: 60 records (velocity bursts within 5 seconds on same account)
3. INVALID_ACCOUNT: 54 records (orphaned account_id not in core accounts)
4. NEGATIVE_BALANCE: 50 records (balance_after < 0)
5. DUPLICATE: 58 records (exact duplicate of existing transactions)
6. LOCATION_MISMATCH: 60 records (state mismatch against customer registered home state)
Total = 60 + 60 + 54 + 50 + 58 + 60 = 342
"""

import random
from datetime import datetime, timedelta
import pandas as pd

def inject_controlled_anomalies(
    valid_txns_df: pd.DataFrame,
    valid_account_ids: list,
    customer_state_map: dict,
    account_customer_map: dict
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Returns:
      (raw_txns_with_anomalies, ground_truth_anomalies_df)
    """
    anomalies_truth = []
    injected_records = []
    
    base_id = 900000000

    # ─────────────────────────────────────────────────────────────
    # 1. HIGH_AMOUNT: 60 records (amount between ₹650,000 and ₹4,500,000)
    # ─────────────────────────────────────────────────────────────
    for i in range(60):
        t_id = f"ANOM_HIGH_{i+1:04d}"
        acc_id = random.choice(valid_account_ids)
        amt = round(random.uniform(650000, 4500000), 2)
        rec = {
            "transaction_id": t_id,
            "account_id": acc_id,
            "merchant_id": "MERCH_000001",
            "transaction_timestamp": "2023-11-15 14:22:10",
            "transaction_type": "TRANSFER",
            "channel": "NETBANKING",
            "amount": amt,
            "balance_after": 25000.00,
            "city": "Mumbai",
            "state": "Maharashtra",
            "status": "SUCCESS",
            "device_id": "DEV_ANOM",
            "ip_address": "192.168.1.100",
            "login_attempts": 1
        }
        injected_records.append(rec)
        anomalies_truth.append({
            "transaction_id": t_id,
            "account_id": acc_id,
            "anomaly_type": "HIGH_AMOUNT",
            "severity": "HIGH",
            "description": f"Transaction amount {amt} exceeds configured threshold of 500000"
        })

    # ─────────────────────────────────────────────────────────────
    # 2. RAPID_TRANSACTIONS: 60 records (30 pairs of transactions 2 seconds apart)
    # ─────────────────────────────────────────────────────────────
    for i in range(30):
        acc_id = random.choice(valid_account_ids)
        t_base = datetime(2023, 10, 20, 11, 0, 0) + timedelta(minutes=i * 10)
        
        # Txn 1
        t_id1 = f"ANOM_RAPID_A_{i+1:04d}"
        rec1 = {
            "transaction_id": t_id1,
            "account_id": acc_id,
            "merchant_id": "MERCH_000002",
            "transaction_timestamp": t_base.strftime("%Y-%m-%d %H:%M:%S"),
            "transaction_type": "DEBIT",
            "channel": "UPI",
            "amount": 250.00,
            "balance_after": 5000.00,
            "city": "Delhi",
            "state": "Delhi",
            "status": "SUCCESS",
            "device_id": "DEV_RAPID",
            "ip_address": "192.168.1.101",
            "login_attempts": 1
        }
        
        # Txn 2 (3 seconds later on same account)
        t_id2 = f"ANOM_RAPID_B_{i+1:04d}"
        rec2 = {
            "transaction_id": t_id2,
            "account_id": acc_id,
            "merchant_id": "MERCH_000003",
            "transaction_timestamp": (t_base + timedelta(seconds=3)).strftime("%Y-%m-%d %H:%M:%S"),
            "transaction_type": "DEBIT",
            "channel": "UPI",
            "amount": 499.00,
            "balance_after": 4501.00,
            "city": "Delhi",
            "state": "Delhi",
            "status": "SUCCESS",
            "device_id": "DEV_RAPID",
            "ip_address": "192.168.1.101",
            "login_attempts": 1
        }
        
        injected_records.extend([rec1, rec2])
        anomalies_truth.append({
            "transaction_id": t_id1,
            "account_id": acc_id,
            "anomaly_type": "RAPID_TRANSACTIONS",
            "severity": "HIGH",
            "description": "Rapid burst velocity transaction detected within 5 seconds"
        })
        anomalies_truth.append({
            "transaction_id": t_id2,
            "account_id": acc_id,
            "anomaly_type": "RAPID_TRANSACTIONS",
            "severity": "HIGH",
            "description": "Rapid burst velocity transaction detected within 5 seconds"
        })

    # ─────────────────────────────────────────────────────────────
    # 3. INVALID_ACCOUNT: 54 records (orphaned accounts e.g. ACC_INVALID_xxxx)
    # ─────────────────────────────────────────────────────────────
    for i in range(54):
        t_id = f"ANOM_INVAL_{i+1:04d}"
        fake_acc = f"ACC_GHOST_{i+9999:05d}"
        rec = {
            "transaction_id": t_id,
            "account_id": fake_acc,
            "merchant_id": "MERCH_000005",
            "transaction_timestamp": "2023-09-10 18:30:00",
            "transaction_type": "WITHDRAWAL",
            "channel": "ATM",
            "amount": 2000.00,
            "balance_after": 15000.00,
            "city": "Bengaluru",
            "state": "Karnataka",
            "status": "FAILED",
            "device_id": "DEV_ATM",
            "ip_address": "192.168.2.1",
            "login_attempts": 3
        }
        injected_records.append(rec)
        anomalies_truth.append({
            "transaction_id": t_id,
            "account_id": fake_acc,
            "anomaly_type": "INVALID_ACCOUNT",
            "severity": "CRITICAL",
            "description": f"Account {fake_acc} does not exist in core banking master tables"
        })

    # ─────────────────────────────────────────────────────────────
    # 4. NEGATIVE_BALANCE: 50 records (balance_after < 0)
    # ─────────────────────────────────────────────────────────────
    for i in range(50):
        t_id = f"ANOM_NEGBAL_{i+1:04d}"
        acc_id = random.choice(valid_account_ids)
        neg_bal = round(random.uniform(-50000, -100), 2)
        rec = {
            "transaction_id": t_id,
            "account_id": acc_id,
            "merchant_id": "MERCH_000010",
            "transaction_timestamp": "2023-08-14 09:15:22",
            "transaction_type": "DEBIT",
            "channel": "POS",
            "amount": 12000.00,
            "balance_after": neg_bal,
            "city": "Chennai",
            "state": "Tamil Nadu",
            "status": "FAILED",
            "device_id": "DEV_POS",
            "ip_address": "192.168.3.15",
            "login_attempts": 1
        }
        injected_records.append(rec)
        anomalies_truth.append({
            "transaction_id": t_id,
            "account_id": acc_id,
            "anomaly_type": "NEGATIVE_BALANCE",
            "severity": "HIGH",
            "description": f"Transaction leaves account in negative balance: {neg_bal}"
        })

    # ─────────────────────────────────────────────────────────────
    # 5. DUPLICATE: 58 records (29 distinct pairs of identical transactions)
    # ─────────────────────────────────────────────────────────────
    for i in range(29):
        acc_id = random.choice(valid_account_ids)
        ts = f"2023-07-0{random.randint(1, 9)} 16:45:00"
        amt = round(random.uniform(500, 4500), 2)
        
        t_id1 = f"ANOM_DUP_ORIG_{i+1:04d}"
        rec1 = {
            "transaction_id": t_id1,
            "account_id": acc_id,
            "merchant_id": "MERCH_000020",
            "transaction_timestamp": ts,
            "transaction_type": "PAYMENT",
            "channel": "UPI",
            "amount": amt,
            "balance_after": 8000.00,
            "city": "Jaipur",
            "state": "Rajasthan",
            "status": "SUCCESS",
            "device_id": "DEV_DUP",
            "ip_address": "192.168.4.1",
            "login_attempts": 1
        }
        
        t_id2 = f"ANOM_DUP_CLONE_{i+1:04d}"
        rec2 = rec1.copy()
        rec2["transaction_id"] = t_id2
        
        injected_records.extend([rec1, rec2])
        anomalies_truth.append({
            "transaction_id": t_id1,
            "account_id": acc_id,
            "anomaly_type": "DUPLICATE",
            "severity": "MEDIUM",
            "description": "Duplicate payment collision detected"
        })
        anomalies_truth.append({
            "transaction_id": t_id2,
            "account_id": acc_id,
            "anomaly_type": "DUPLICATE",
            "severity": "MEDIUM",
            "description": "Duplicate payment collision detected"
        })

    # ─────────────────────────────────────────────────────────────
    # 6. LOCATION_MISMATCH: 60 records (Physical ATM/Branch in different state)
    # ─────────────────────────────────────────────────────────────
    for i in range(60):
        t_id = f"ANOM_LOC_{i+1:04d}"
        acc_id = random.choice(valid_account_ids)
        cust_id = account_customer_map.get(acc_id)
        home_state = customer_state_map.get(cust_id, "Maharashtra")
        # Ensure far-away different state
        diff_state = "Kerala" if home_state != "Kerala" else "Punjab"
        
        rec = {
            "transaction_id": t_id,
            "account_id": acc_id,
            "merchant_id": None,
            "transaction_timestamp": "2023-06-18 21:05:40",
            "transaction_type": "WITHDRAWAL",
            "channel": "ATM",
            "amount": 10000.00,
            "balance_after": 45000.00,
            "city": f"{diff_state} Outpost",
            "state": diff_state,
            "status": "SUCCESS",
            "device_id": "DEV_ATM_REMOTE",
            "ip_address": "10.0.0.55",
            "login_attempts": 2
        }
        injected_records.append(rec)
        anomalies_truth.append({
            "transaction_id": t_id,
            "account_id": acc_id,
            "anomaly_type": "LOCATION_MISMATCH",
            "severity": "MEDIUM",
            "description": f"ATM transaction in {diff_state} mismatches customer home state {home_state}"
        })

    assert len(anomalies_truth) == 342, f"Expected exactly 342 anomalies, got {len(anomalies_truth)}"
    assert len(injected_records) == 342, f"Expected 342 records, got {len(injected_records)}"

    df_anom = pd.DataFrame(injected_records)
    df_truth = pd.DataFrame(anomalies_truth)
    
    # Combine with valid txns
    combined_raw = pd.concat([valid_txns_df, df_anom], ignore_index=True)
    return combined_raw, df_truth

if __name__ == "__main__":
    print("inject_anomalies module ready (342 controlled anomalies).")
