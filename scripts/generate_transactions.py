# scripts/generate_transactions.py
"""
High-throughput synthetic banking transaction generator for FinSight.
Generates realistic multi-channel banking records with realistic amount distributions.
"""

import os
import random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

CHANNELS = ["UPI", "ATM", "NETBANKING", "MOBILE_APP", "POS", "BRANCH"]
TRANSACTION_TYPES = ["DEBIT", "CREDIT", "TRANSFER", "WITHDRAWAL", "PAYMENT"]

# Typical realistic amount boundaries per channel (in INR)
AMOUNT_RANGES = {
    "UPI": (50, 20000),
    "POS": (100, 50000),
    "ATM": (500, 50000),
    "NETBANKING": (500, 200000),
    "MOBILE_APP": (100, 100000),
    "BRANCH": (2000, 400000)
}

def generate_transaction_chunk(
    start_id: int,
    count: int,
    account_ids: list,
    merchant_ids: list,
    customer_state_map: dict,
    account_customer_map: dict,
    start_date: datetime,
    end_date: datetime
) -> pd.DataFrame:
    """Generates a chunk of clean transaction records."""
    total_seconds = int((end_date - start_date).total_seconds())
    
    txns = []
    for i in range(count):
        txn_id = f"TXN_{start_id + i:09d}"
        acc_id = random.choice(account_ids)
        cust_id = account_customer_map.get(acc_id)
        cust_state = customer_state_map.get(cust_id, "Maharashtra")
        
        channel = random.choices(
            CHANNELS,
            weights=[0.35, 0.15, 0.15, 0.20, 0.10, 0.05],
            k=1
        )[0]
        
        # Transaction Type based on channel
        if channel == "ATM":
            ttype = "WITHDRAWAL"
            merch_id = None
        elif channel in ("UPI", "POS"):
            ttype = random.choices(["PAYMENT", "DEBIT", "TRANSFER"], weights=[0.7, 0.2, 0.1])[0]
            merch_id = random.choice(merchant_ids)
        elif channel == "BRANCH":
            ttype = random.choices(["DEBIT", "CREDIT", "TRANSFER"], weights=[0.4, 0.4, 0.2])[0]
            merch_id = None
        else: # NETBANKING / MOBILE_APP
            ttype = random.choices(["TRANSFER", "PAYMENT", "CREDIT", "DEBIT"], weights=[0.4, 0.3, 0.2, 0.1])[0]
            merch_id = random.choice(merchant_ids) if random.random() < 0.6 else None

        min_amt, max_amt = AMOUNT_RANGES[channel]
        # Log-normal distribution skewed towards lower/medium tickets
        amt = round(float(np.random.triangular(min_amt, min_amt * 2.5, max_amt)), 2)
        
        # Timestamp
        offset_sec = random.randint(0, total_seconds)
        txn_time = start_date + timedelta(seconds=offset_sec)
        
        # Balance after transaction (positive normal balance)
        bal_after = round(random.uniform(500, 150000), 2)
        
        # Location state matches customer state in normal circumstances
        txn_state = cust_state
        city = f"{txn_state} City"
        
        status = "SUCCESS" if random.random() < 0.985 else "FAILED"
        
        txns.append({
            "transaction_id": txn_id,
            "account_id": acc_id,
            "merchant_id": merch_id,
            "transaction_timestamp": txn_time.strftime("%Y-%m-%d %H:%M:%S"),
            "transaction_type": ttype,
            "channel": channel,
            "amount": amt,
            "balance_after": bal_after,
            "city": city,
            "state": txn_state,
            "status": status,
            "device_id": f"DEV_{random.randint(1000, 9999)}",
            "ip_address": f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}",
            "login_attempts": 1
        })
        
    return pd.DataFrame(txns)

if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "..", "data", "generated")
    print("generate_transactions module ready.")
