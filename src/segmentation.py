# src/segmentation.py
"""
Defensible Customer Segmentation Engine for FinSight.
Partitions banking customers into exactly 7 business-driven segments:

1. STUDENT: Age < 25 and annual_income < 500,000
2. SENIOR: Age >= 60
3. PREMIUM: Annual income >= 2,500,000
4. AFFLUENT: Annual income >= 1,500,000 and < 2,500,000
5. SMALL_BUSINESS: Business/commercial accounts with high transaction turnover
6. SALARIED: Regular salaried corporate workforce
7. MASS_MARKET: General consumer retail cohort
"""

import pandas as pd
from sqlalchemy import text
from src.db import engine, DB_DIALECT

SEGMENT_NAMES = [
    "STUDENT",
    "SALARIED",
    "MASS_MARKET",
    "AFFLUENT",
    "PREMIUM",
    "SENIOR",
    "SMALL_BUSINESS"
]

def classify_customer_segment(row: pd.Series) -> str:
    """Classifies a customer into one of the 7 banking cohorts."""
    age = row.get("age", 30)
    income = row.get("annual_income", 600000)
    cust_type = str(row.get("customer_type", "")).upper()
    
    if age >= 60:
        return "SENIOR"
    if age < 25 and income < 500000:
        return "STUDENT"
    if income >= 2500000 or cust_type == "HIGH_NET_WORTH":
        return "PREMIUM"
    if income >= 1500000:
        return "AFFLUENT"
    if cust_type == "BUSINESS":
        return "SMALL_BUSINESS"
    if cust_type == "SALARIED":
        return "SALARIED"
    
    return "MASS_MARKET"

def run_segmentation(eng=engine):
    """Assigns the 7 segments to all registered customers and stores in analytics."""
    table_cust = "core.customers" if DB_DIALECT == "postgresql" else "core_customers"
    table_seg = "analytics.customer_segments" if DB_DIALECT == "postgresql" else "analytics_customer_segments"
    
    customers_df = pd.read_sql(f"SELECT customer_id, age, annual_income, customer_type FROM {table_cust}", eng)
    if customers_df.empty:
        print("[Segmentation] No customers found in database.")
        return
        
    customers_df["segment"] = customers_df.apply(classify_customer_segment, axis=1)
    
    seg_records = customers_df[["customer_id", "segment"]].copy()
    
    with eng.begin() as conn:
        conn.execute(text(f"DELETE FROM {table_seg}"))
        seg_records.to_sql(
            table_seg if DB_DIALECT == "sqlite" else "customer_segments",
            conn,
            schema=None if DB_DIALECT == "sqlite" else "analytics",
            if_exists="append",
            index=False
        )
        
    print(f"[Segmentation] Successfully categorized {len(seg_records)} customers into 7 cohorts:")
    breakdown = seg_records["segment"].value_counts().to_dict()
    for seg, cnt in breakdown.items():
        print(f"  - {seg}: {cnt:,} customers")
    return breakdown

if __name__ == "__main__":
    run_segmentation()
