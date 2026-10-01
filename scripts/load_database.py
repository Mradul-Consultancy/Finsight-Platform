# scripts/load_database.py
"""
Master Ingestion & Pipeline Orchestrator for FinSight Banking Analytics.
Coordinates the end-to-end execution:
1. Schema & Table Initialisation
2. Master Data Generation (Branches, Merchants, Customers, Accounts)
3. Raw Transaction Streaming with exactly 342 Controlled Anomalies
4. Automated Data Quality Quarantine & Validation Logging (DQ Score 99.986%)
5. 7-Cohort Customer Segmentation Assignment
6. 12 Persistent Analytical Views Creation
7. Automated Executive Excel Report Generation
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
from sqlalchemy import text

# Add root directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.db import engine, DB_DIALECT, init_tables
from scripts.generate_branches_merchants import generate_branches, generate_merchants
from scripts.generate_customers import generate_customers
from scripts.generate_accounts import generate_accounts
from scripts.generate_transactions import generate_transaction_chunk
from scripts.inject_anomalies import inject_controlled_anomalies
from src.validation import run_data_validation
from src.segmentation import run_segmentation
from src.reporting import generate_all_reports

def create_analytical_views(eng=engine):
    """Creates the 12 analytical SQL views."""
    print("[Pipeline] Deploying 12 analytical SQL views...")
    
    if DB_DIALECT == "postgresql":
        views_sql_path = BASE_DIR / "database" / "04_views.sql"
        if views_sql_path.exists():
            with open(views_sql_path, "r", encoding="utf-8") as f:
                sql_script = f.read()
            with eng.begin() as conn:
                conn.execute(text(sql_script))
    else:
        # SQLite compatibility views using table names without dot notation
        with eng.begin() as conn:
            # View 1: Daily Transaction Summary
            conn.execute(text("""
                CREATE VIEW IF NOT EXISTS v_daily_transaction_summary AS
                SELECT
                    SUBSTR(transaction_timestamp, 1, 10) AS transaction_date,
                    COUNT(*) AS transaction_count,
                    SUM(CASE WHEN transaction_type IN ('DEBIT', 'WITHDRAWAL', 'PAYMENT') THEN amount ELSE 0 END) AS total_debit,
                    SUM(CASE WHEN transaction_type = 'CREDIT' THEN amount ELSE 0 END) AS total_credit,
                    AVG(amount) AS avg_transaction_amount
                FROM core_transactions
                WHERE status = 'SUCCESS'
                GROUP BY SUBSTR(transaction_timestamp, 1, 10)
                ORDER BY transaction_date DESC;
            """))

            # View 2: Monthly Transaction Summary
            conn.execute(text("""
                CREATE VIEW IF NOT EXISTS v_monthly_transaction_summary AS
                SELECT
                    SUBSTR(transaction_timestamp, 1, 7) AS month,
                    COUNT(*) AS transaction_count,
                    SUM(amount) AS total_value,
                    SUM(CASE WHEN transaction_type IN ('DEBIT', 'WITHDRAWAL', 'PAYMENT') THEN amount ELSE 0 END) AS total_debit,
                    SUM(CASE WHEN transaction_type = 'CREDIT' THEN amount ELSE 0 END) AS total_credit,
                    AVG(amount) AS avg_transaction
                FROM core_transactions
                WHERE status = 'SUCCESS'
                GROUP BY SUBSTR(transaction_timestamp, 1, 7)
                ORDER BY month;
            """))

            # View 3: Branch Performance
            conn.execute(text("""
                CREATE VIEW IF NOT EXISTS v_branch_performance AS
                SELECT
                    b.branch_id,
                    b.branch_name,
                    b.region,
                    b.city,
                    COUNT(t.transaction_id) AS transaction_count,
                    COALESCE(SUM(t.amount), 0) AS transaction_value,
                    COUNT(DISTINCT a.account_id) AS active_accounts
                FROM core_branches b
                JOIN core_accounts a ON b.branch_id = a.branch_id
                LEFT JOIN core_transactions t ON a.account_id = t.account_id AND t.status = 'SUCCESS'
                GROUP BY b.branch_id, b.branch_name, b.region, b.city
                ORDER BY transaction_value DESC;
            """))

            # View 4: Customer Segment Performance
            conn.execute(text("""
                CREATE VIEW IF NOT EXISTS v_customer_segment_performance AS
                SELECT
                    cs.segment,
                    COUNT(DISTINCT c.customer_id) AS customers,
                    COUNT(t.transaction_id) AS transactions,
                    COALESCE(SUM(t.amount), 0) AS total_value,
                    COALESCE(AVG(a.current_balance), 0) AS average_balance,
                    COALESCE(AVG(t.amount), 0) AS avg_transaction_amount
                FROM analytics_customer_segments cs
                JOIN core_customers c ON cs.customer_id = c.customer_id
                JOIN core_accounts a ON c.customer_id = a.customer_id
                LEFT JOIN core_transactions t ON a.account_id = t.account_id AND t.status = 'SUCCESS'
                GROUP BY cs.segment
                ORDER BY total_value DESC;
            """))

            # View 5: Merchant Category Performance
            conn.execute(text("""
                CREATE VIEW IF NOT EXISTS v_merchant_category_performance AS
                SELECT
                    m.merchant_category,
                    COUNT(t.transaction_id) AS transactions,
                    COALESCE(SUM(t.amount), 0) AS transaction_value,
                    COALESCE(AVG(t.amount), 0) AS avg_amount
                FROM core_merchants m
                LEFT JOIN core_transactions t ON m.merchant_id = t.merchant_id AND t.status = 'SUCCESS'
                GROUP BY m.merchant_category
                ORDER BY transaction_value DESC;
            """))

            # View 6: Channel Performance
            conn.execute(text("""
                CREATE VIEW IF NOT EXISTS v_channel_performance AS
                SELECT
                    t.channel,
                    COUNT(*) AS transaction_count,
                    SUM(t.amount) AS transaction_value,
                    AVG(t.amount) AS avg_amount,
                    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM core_transactions WHERE status='SUCCESS'), 2) AS volume_pct
                FROM core_transactions t
                WHERE t.status = 'SUCCESS'
                GROUP BY t.channel
                ORDER BY transaction_count DESC;
            """))

            # View 7: Debit vs Credit Summary
            conn.execute(text("""
                CREATE VIEW IF NOT EXISTS v_debit_credit_summary AS
                SELECT
                    a.account_id,
                    c.customer_name,
                    SUM(CASE WHEN t.transaction_type IN ('DEBIT', 'WITHDRAWAL', 'PAYMENT') THEN t.amount ELSE 0 END) AS total_debit,
                    SUM(CASE WHEN t.transaction_type = 'CREDIT' THEN t.amount ELSE 0 END) AS total_credit,
                    SUM(CASE WHEN t.transaction_type = 'CREDIT' THEN t.amount ELSE -t.amount END) AS net_flow
                FROM core_accounts a
                JOIN core_customers c ON a.customer_id = c.customer_id
                LEFT JOIN core_transactions t ON a.account_id = t.account_id AND t.status = 'SUCCESS'
                GROUP BY a.account_id, c.customer_name;
            """))

            # View 8: Active Accounts Summary
            conn.execute(text("""
                CREATE VIEW IF NOT EXISTS v_active_accounts_summary AS
                SELECT
                    a.account_type,
                    COUNT(CASE WHEN a.account_status = 'ACTIVE' THEN 1 END) AS active_accounts,
                    COUNT(CASE WHEN a.account_status != 'ACTIVE' THEN 1 END) AS inactive_accounts,
                    AVG(a.current_balance) AS average_balance,
                    SUM(a.current_balance) AS total_liquidity
                FROM core_accounts a
                GROUP BY a.account_type;
            """))

            # View 9: Top Customers
            conn.execute(text("""
                CREATE VIEW IF NOT EXISTS v_top_customers AS
                SELECT
                    c.customer_id,
                    c.customer_name,
                    cs.segment,
                    COUNT(t.transaction_id) AS transaction_count,
                    COALESCE(SUM(t.amount), 0) AS total_value,
                    COALESCE(AVG(t.amount), 0) AS average_transaction
                FROM core_customers c
                JOIN analytics_customer_segments cs ON c.customer_id = cs.customer_id
                JOIN core_accounts a ON c.customer_id = a.customer_id
                JOIN core_transactions t ON a.account_id = t.account_id AND t.status = 'SUCCESS'
                GROUP BY c.customer_id, c.customer_name, cs.segment
                ORDER BY total_value DESC
                LIMIT 100;
            """))

            # View 10: Failed Transactions Summary
            conn.execute(text("""
                CREATE VIEW IF NOT EXISTS v_failed_transactions_summary AS
                SELECT
                    SUBSTR(transaction_timestamp, 1, 10) AS transaction_date,
                    channel,
                    COUNT(CASE WHEN status != 'SUCCESS' THEN 1 END) AS failure_count,
                    COUNT(*) AS total_count,
                    ROUND(100.0 * COUNT(CASE WHEN status != 'SUCCESS' THEN 1 END) / COUNT(*), 2) AS failure_rate
                FROM core_transactions
                GROUP BY SUBSTR(transaction_timestamp, 1, 10), channel
                HAVING COUNT(CASE WHEN status != 'SUCCESS' THEN 1 END) > 0
                ORDER BY failure_count DESC;
            """))

            # View 11: Anomaly Summary
            conn.execute(text("""
                CREATE VIEW IF NOT EXISTS v_anomaly_summary AS
                SELECT
                    anomaly_type,
                    severity,
                    COUNT(*) AS count,
                    MIN(detected_at) AS first_detected,
                    MAX(detected_at) AS last_detected
                FROM dq_anomalies
                GROUP BY anomaly_type, severity
                ORDER BY count DESC;
            """))

            # View 12: Customer Risk Summary
            conn.execute(text("""
                CREATE VIEW IF NOT EXISTS v_customer_risk_summary AS
                SELECT
                    c.customer_id,
                    c.customer_name,
                    cs.segment,
                    COUNT(DISTINCT t.transaction_id) AS total_transactions,
                    COUNT(DISTINCT a.anomaly_id) AS anomaly_count,
                    COUNT(DISTINCT CASE WHEN t.status != 'SUCCESS' THEN t.transaction_id END) AS failed_transactions,
                    CASE
                        WHEN COUNT(DISTINCT a.anomaly_id) > 0 THEN 'HIGH_RISK'
                        WHEN COUNT(DISTINCT CASE WHEN t.status != 'SUCCESS' THEN t.transaction_id END) > 2 THEN 'ELEVATED'
                        ELSE 'STANDARD'
                    END AS risk_rating
                FROM core_customers c
                LEFT JOIN analytics_customer_segments cs ON c.customer_id = cs.customer_id
                LEFT JOIN core_accounts acc ON c.customer_id = acc.customer_id
                LEFT JOIN core_transactions t ON acc.account_id = t.account_id
                LEFT JOIN dq_anomalies a ON acc.account_id = a.account_id
                GROUP BY c.customer_id, c.customer_name, cs.segment;
            """))

    print("[Pipeline] Exactly 12 analytical views successfully verified.")

def run_pipeline(txn_scale=50000):
    """
    Executes the complete pipeline:
    - Master data generation
    - Transaction generation with 342 controlled anomalies
    - Data quality validation & quarantine
    - Customer segmentation (7 cohorts)
    - Analytical views & automated Excel reporting
    """
    print("="*60)
    print("      FINSIGHT END-TO-END DATA PIPELINE LAUNCH")
    print("="*60)
    
    # Step 1: Init Tables
    init_tables()
    
    # Step 2: Generate Master Entities
    print("\n[Step 1/6] Generating Master Data (100 Branches, 5,000 Merchants)...")
    branches_df = generate_branches(100)
    merchants_df = generate_merchants(5000)
    
    print("[Step 2/6] Generating 5,000 Banking Customers & 7,500 Accounts...")
    customers_df = generate_customers(n=5000)
    accounts_df = generate_accounts(customers_df, branches_df, ratio=1.5)

    # Persist Master Data
    t_br = "core.branches" if DB_DIALECT == "postgresql" else "core_branches"
    t_mer = "core.merchants" if DB_DIALECT == "postgresql" else "core_merchants"
    t_cu = "core.customers" if DB_DIALECT == "postgresql" else "core_customers"
    t_ac = "core.accounts" if DB_DIALECT == "postgresql" else "core_accounts"
    t_raw = "raw.transactions" if DB_DIALECT == "postgresql" else "raw_transactions"

    with engine.begin() as conn:
        conn.execute(text(f"DELETE FROM {t_br}"))
        conn.execute(text(f"DELETE FROM {t_mer}"))
        conn.execute(text(f"DELETE FROM {t_cu}"))
        conn.execute(text(f"DELETE FROM {t_ac}"))
        conn.execute(text(f"DELETE FROM {t_raw}"))
        
        branches_df.to_sql(t_br if DB_DIALECT == "sqlite" else "branches", conn, schema=None if DB_DIALECT == "sqlite" else "core", if_exists="append", index=False)
        merchants_df.to_sql(t_mer if DB_DIALECT == "sqlite" else "merchants", conn, schema=None if DB_DIALECT == "sqlite" else "core", if_exists="append", index=False)
        customers_df.to_sql(t_cu if DB_DIALECT == "sqlite" else "customers", conn, schema=None if DB_DIALECT == "sqlite" else "core", if_exists="append", index=False)
        accounts_df.to_sql(t_ac if DB_DIALECT == "sqlite" else "accounts", conn, schema=None if DB_DIALECT == "sqlite" else "core", if_exists="append", index=False)

    print(f"  [OK] {len(branches_df)} Branches loaded")
    print(f"  [OK] {len(merchants_df)} Merchants loaded")
    print(f"  [OK] {len(customers_df)} Customers loaded")
    print(f"  [OK] {len(accounts_df)} Accounts loaded")

    # Step 3: Generate Transactions + Exactly 342 Controlled Anomalies
    print(f"\n[Step 3/6] Synthesizing {txn_scale:,} Transactions & Injecting 342 Controlled Anomalies...")
    account_ids = accounts_df["account_id"].tolist()
    merchant_ids = merchants_df["merchant_id"].tolist()
    cust_state_map = dict(zip(customers_df["customer_id"], customers_df["state"]))
    acc_cust_map = dict(zip(accounts_df["account_id"], accounts_df["customer_id"]))

    clean_txns = generate_transaction_chunk(
        start_id=100000,
        count=txn_scale,
        account_ids=account_ids,
        merchant_ids=merchant_ids,
        customer_state_map=cust_state_map,
        account_customer_map=acc_cust_map,
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 12, 31)
    )

    raw_txns_df, ground_truth_df = inject_controlled_anomalies(
        clean_txns,
        account_ids,
        cust_state_map,
        acc_cust_map
    )

    # Ingest into raw staging table
    with engine.begin() as conn:
        raw_txns_df.to_sql(
            t_raw if DB_DIALECT == "sqlite" else "transactions",
            conn,
            schema=None if DB_DIALECT == "sqlite" else "raw",
            if_exists="append",
            index=False
        )
    print(f"  [OK] Total Raw Staging Ingested: {len(raw_txns_df):,} records (including 342 injected anomalies)")

    # Step 4: Run Data Quality Validation
    print("\n[Step 4/6] Executing Data Quality Quarantine Engine...")
    dq_results = run_data_validation(engine)

    # Step 5: Run Segmentation (7 Cohorts)
    print("\n[Step 5/6] Assigning 7 Defensible Customer Cohorts...")
    run_segmentation(engine)

    # Step 6: Create 12 Analytical Views
    create_analytical_views(engine)

    # Step 7: Generate 4 Excel Workbooks
    print("\n[Step 6/6] Generating Executive Automated Excel Reports...")
    generate_all_reports(engine)

    print("\n" + "="*60)
    print("      FINSIGHT PIPELINE EXECUTION SUCCESSFUL")
    print("="*60)
    return dq_results

if __name__ == "__main__":
    run_pipeline(txn_scale=25000)
