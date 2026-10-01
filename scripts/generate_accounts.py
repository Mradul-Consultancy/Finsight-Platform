# scripts/generate_accounts.py
"""
Generates banking accounts linked to customers and branches.
Supports SAVINGS, CURRENT, SALARY, STUDENT, PREMIUM account types.
"""

import os
import random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

ACCOUNT_TYPES = ["SAVINGS", "CURRENT", "SALARY", "STUDENT", "PREMIUM"]

def generate_accounts(customers_df: pd.DataFrame, branches_df: pd.DataFrame, ratio=1.4) -> pd.DataFrame:
    accounts = []
    branch_ids = branches_df["branch_id"].tolist()
    acc_counter = 1
    
    for _, cust in customers_df.iterrows():
        # Most customers have 1 account, some have 2
        num_accounts = 2 if random.random() < (ratio - 1.0) else 1
        
        for _ in range(num_accounts):
            acc_id = f"ACC_{acc_counter:08d}"
            acc_counter += 1
            
            # Select account type based on customer profile
            if cust["age"] < 24 and cust["annual_income"] < 500000:
                acc_type = "STUDENT" if random.random() < 0.8 else "SAVINGS"
            elif cust["annual_income"] >= 2500000:
                acc_type = "PREMIUM"
            elif cust["customer_type"] == "BUSINESS":
                acc_type = "CURRENT"
            elif cust["customer_type"] == "SALARIED":
                acc_type = "SALARY"
            else:
                acc_type = random.choice(["SAVINGS", "CURRENT"])

            # Realistic balance distribution by account type
            if acc_type == "STUDENT":
                balance = round(random.uniform(500, 25000), 2)
            elif acc_type == "PREMIUM":
                balance = round(random.uniform(300000, 2500000), 2)
            elif acc_type == "CURRENT":
                balance = round(random.uniform(50000, 800000), 2)
            else:
                balance = round(random.uniform(5000, 150000), 2)

            open_date = datetime.strptime(cust["created_at"][:10], "%Y-%m-%d") + timedelta(days=random.randint(1, 30))
            branch_id = random.choice(branch_ids)
            
            accounts.append({
                "account_id": acc_id,
                "customer_id": cust["customer_id"],
                "account_type": acc_type,
                "account_open_date": open_date.strftime("%Y-%m-%d"),
                "current_balance": balance,
                "branch_id": branch_id,
                "account_status": "ACTIVE" if random.random() < 0.96 else "INACTIVE"
            })
            
    return pd.DataFrame(accounts)

if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "..", "data", "generated")
    cust_path = os.path.join(out_dir, "customers.csv")
    branch_path = os.path.join(out_dir, "branches.csv")
    
    if os.path.exists(cust_path) and os.path.exists(branch_path):
        df_c = pd.read_csv(cust_path)
        df_b = pd.read_csv(branch_path)
        df_acc = generate_accounts(df_c, df_b)
        df_acc.to_csv(os.path.join(out_dir, "accounts.csv"), index=False)
        print(f"Generated {len(df_acc)} accounts.")
    else:
        print("Please generate customers and branches first.")
