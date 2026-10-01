# api_client.py
"""
Utility module that creates a single SQLAlchemy engine shared by all FastAPI routers.
It attempts to connect to the PostgreSQL database defined in `db_config.py`.
If the PostgreSQL connection fails, it automatically falls back to a local SQLite database
(credit_engine.db) and auto-seeds it from the local CSV data.
"""

import os
import sys
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text

# Import DB credentials
DB_CONFIG_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "config", "db_config.py")
)

import importlib.util
spec = importlib.util.spec_from_file_location("db_config", DB_CONFIG_PATH)
db_config = importlib.util.module_from_spec(spec)  # type: ignore
spec.loader.exec_module(db_config)  # type: ignore

POSTGRES_DSN = (
    f"postgresql+psycopg2://"
    f"{db_config.POSTGRES_USER}:{db_config.POSTGRES_PASSWORD}"
    f"@{db_config.POSTGRES_HOST}:{db_config.POSTGRES_PORT}/{db_config.POSTGRES_DB}"
)

SQLITE_DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "credit_engine.db")
)
SQLITE_DSN = f"sqlite:///{SQLITE_DB_PATH.replace(os.sep, '/')}"

CSV_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "bank_transactions_data_2.csv")
)

def test_connection(dsn: str) -> bool:
    """Test if a database connection can be established."""
    try:
        temp_engine = create_engine(dsn, connect_args={"connect_timeout": 2} if "postgres" in dsn else {})
        with temp_engine.connect() as conn:
            conn.execute(text("SELECT 1")).fetchone()
        temp_engine.dispose()
        return True
    except Exception:
        return False

# Initialize the appropriate engine
is_postgres = False
if test_connection(POSTGRES_DSN):
    print("[DB Connection] Successfully connected to PostgreSQL.")
    engine = create_engine(POSTGRES_DSN, echo=False, future=True)
    is_postgres = True
else:
    print(f"[DB Warning] PostgreSQL connection failed. Falling back to local SQLite database: {SQLITE_DB_PATH}")
    engine = create_engine(SQLITE_DSN, echo=False, future=True)
    is_postgres = False

# Auto-seed logic for SQLite if SQLite is active and tables don't exist
def seed_sqlite_if_empty():
    if is_postgres:
        return
        
    # Check if fact_transactions table exists
    table_exists = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1 FROM fact_transactions LIMIT 1")).fetchone()
            table_exists = True
    except Exception:
        pass

    if not table_exists:
        print("[DB Seed] Seeding SQLite database from CSV data...")
        if not os.path.exists(CSV_PATH):
            print(f"[DB Error] CSV file not found at {CSV_PATH}. Seeding aborted.")
            return

        try:
            # Load and clean data
            df = pd.read_csv(CSV_PATH)
            
            # Simple clean data logic
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            categorical_cols = df.select_dtypes(exclude=[np.number, "datetime"]).columns.tolist()
            for col in numeric_cols:
                df[col] = df[col].fillna(df[col].median())
                q1 = df[col].quantile(0.25)
                q3 = df[col].quantile(0.75)
                iqr = q3 - q1
                df[col] = np.clip(df[col], q1 - 1.5 * iqr, q3 + 1.5 * iqr)
            for col in categorical_cols:
                df[col] = df[col].fillna(df[col].mode().iloc[0] if not df[col].mode().empty else "UNKNOWN")

            with engine.begin() as conn:
                # Create schema
                conn.execute(text("""
                CREATE TABLE IF NOT EXISTS dim_customers (
                    customer_id VARCHAR PRIMARY KEY,
                    age INTEGER,
                    occupation VARCHAR,
                    segment VARCHAR
                );
                """))
                conn.execute(text("""
                CREATE TABLE IF NOT EXISTS dim_merchants (
                    merchant_id VARCHAR PRIMARY KEY,
                    merchant_category VARCHAR
                );
                """))
                conn.execute(text("""
                CREATE TABLE IF NOT EXISTS dim_categories (
                    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_name VARCHAR UNIQUE
                );
                """))
                conn.execute(text("""
                CREATE TABLE IF NOT EXISTS fact_transactions (
                    transaction_id VARCHAR PRIMARY KEY,
                    customer_id VARCHAR,
                    merchant_id VARCHAR,
                    transaction_amount NUMERIC,
                    transaction_date TIMESTAMP,
                    transaction_type VARCHAR,
                    location VARCHAR,
                    device_id VARCHAR,
                    ip_address VARCHAR,
                    channel VARCHAR,
                    transaction_duration INTEGER,
                    login_attempts INTEGER,
                    account_balance NUMERIC,
                    previous_transaction_date TIMESTAMP
                );
                """))

            # Save customers
            customers = df[["AccountID", "CustomerAge", "CustomerOccupation"]].drop_duplicates()
            customers = customers.rename(columns={"AccountID": "customer_id", "CustomerAge": "age", "CustomerOccupation": "occupation"})
            def age_segment(age):
                if age < 30: return "Young"
                elif age < 55: return "Mid"
                else: return "Senior"
            customers["segment"] = customers["age"].apply(age_segment)
            customers.to_sql("dim_customers", engine, if_exists="replace", index=False)

            # Save merchants
            merchants = df[["MerchantID", "Location"]].drop_duplicates()
            merchants = merchants.rename(columns={"MerchantID": "merchant_id", "Location": "merchant_category"})
            merchants.to_sql("dim_merchants", engine, if_exists="replace", index=False)

            # Save transactions
            fact = df[[
                "TransactionID", "AccountID", "MerchantID", "TransactionAmount",
                "TransactionDate", "TransactionType", "Location", "DeviceID",
                "IP Address", "Channel", "TransactionDuration", "LoginAttempts",
                "AccountBalance", "PreviousTransactionDate"
            ]].copy()
            fact = fact.rename(columns={
                "TransactionID": "transaction_id", "AccountID": "customer_id",
                "MerchantID": "merchant_id", "TransactionAmount": "transaction_amount",
                "TransactionDate": "transaction_date", "TransactionType": "transaction_type",
                "Location": "location", "DeviceID": "device_id", "IP Address": "ip_address",
                "Channel": "channel", "TransactionDuration": "transaction_duration",
                "LoginAttempts": "login_attempts", "AccountBalance": "account_balance",
                "PreviousTransactionDate": "previous_transaction_date"
            })
            fact.to_sql("fact_transactions", engine, if_exists="replace", index=False)

            # Create analytical views for SQLite
            with engine.begin() as conn:
                conn.execute(text("""
                CREATE VIEW IF NOT EXISTS vw_monthly_spending_by_segment AS
                SELECT
                    strftime('%Y-%m-01', transaction_date) AS month,
                    c.segment,
                    SUM(transaction_amount) AS total_spent
                FROM fact_transactions f
                JOIN dim_customers c ON f.customer_id = c.customer_id
                GROUP BY strftime('%Y-%m-01', transaction_date), c.segment;
                """))

                conn.execute(text("""
                CREATE VIEW IF NOT EXISTS vw_rolling_7d_fraud_rate AS
                SELECT
                    transaction_date,
                    100.0 * SUM(CASE WHEN transaction_type = 'Credit' THEN 1 ELSE 0 END) OVER (
                        ORDER BY transaction_date
                        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
                    ) / COUNT(*) OVER (
                        ORDER BY transaction_date
                        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
                    ) AS fraud_rate_percent
                FROM fact_transactions;
                """))

            print("[DB Success] SQLite database successfully seeded.")
        except Exception as e:
            print(f"[DB Error] SQLite Seeding failed: {e}")

# Run seed check
seed_sqlite_if_empty()
