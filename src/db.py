# src/db.py
"""
Database connection manager and dual-engine compatibility layer.
Supports both PostgreSQL (production) and SQLite (zero-config local runtime).
"""

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from src.config import POSTGRES_URI, SQLITE_URI, BASE_DIR

def get_engine() -> tuple[Engine, str]:
    """
    Attempts PostgreSQL connection first; falls back to SQLite if unreachable.
    Returns (engine, dialect_name)
    """
    try:
        pg_engine = create_engine(POSTGRES_URI, connect_args={"connect_timeout": 2})
        with pg_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("[DB] Connected to PostgreSQL instance.")
        return pg_engine, "postgresql"
    except Exception:
        print("[DB] PostgreSQL unavailable. Using high-performance SQLite engine.")
        sqlite_engine = create_engine(SQLITE_URI, echo=False)
        return sqlite_engine, "sqlite"

engine, DB_DIALECT = get_engine()

def init_tables(eng: Engine = engine):
    """Initializes schema and tables for the active database engine."""
    with eng.begin() as conn:
        if DB_DIALECT == "postgresql":
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw;"))
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS core;"))
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS analytics;"))
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS dq;"))

            # Core Tables
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS core.branches (
                    branch_id VARCHAR(32) PRIMARY KEY,
                    branch_name VARCHAR(120) NOT NULL,
                    city VARCHAR(100) NOT NULL,
                    state VARCHAR(100) NOT NULL,
                    region VARCHAR(30) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS core.merchants (
                    merchant_id VARCHAR(32) PRIMARY KEY,
                    merchant_name VARCHAR(120) NOT NULL,
                    merchant_category VARCHAR(50) NOT NULL,
                    city VARCHAR(100),
                    state VARCHAR(100)
                );
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS core.customers (
                    customer_id VARCHAR(32) PRIMARY KEY,
                    customer_name VARCHAR(120) NOT NULL,
                    date_of_birth DATE,
                    age INT,
                    gender VARCHAR(20),
                    city VARCHAR(100),
                    state VARCHAR(100),
                    customer_type VARCHAR(30),
                    annual_income NUMERIC(14,2),
                    created_at TIMESTAMP NOT NULL
                );
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS core.accounts (
                    account_id VARCHAR(32) PRIMARY KEY,
                    customer_id VARCHAR(32) NOT NULL,
                    account_type VARCHAR(30) NOT NULL,
                    account_open_date DATE NOT NULL,
                    current_balance NUMERIC(14,2) DEFAULT 0.00,
                    branch_id VARCHAR(32) NOT NULL,
                    account_status VARCHAR(20) DEFAULT 'ACTIVE'
                );
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS core.transactions (
                    transaction_id VARCHAR(64) PRIMARY KEY,
                    account_id VARCHAR(32) NOT NULL,
                    merchant_id VARCHAR(32),
                    transaction_timestamp TIMESTAMP NOT NULL,
                    transaction_type VARCHAR(20) NOT NULL,
                    channel VARCHAR(30) NOT NULL,
                    amount NUMERIC(14,2) NOT NULL,
                    balance_after NUMERIC(14,2),
                    city VARCHAR(100),
                    state VARCHAR(100),
                    status VARCHAR(20) NOT NULL,
                    device_id VARCHAR(64),
                    ip_address VARCHAR(45),
                    login_attempts INT DEFAULT 1
                );
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS analytics.customer_segments (
                    customer_id VARCHAR(32) PRIMARY KEY,
                    segment VARCHAR(30) NOT NULL,
                    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS dq.anomalies (
                    anomaly_id BIGSERIAL PRIMARY KEY,
                    transaction_id VARCHAR(64),
                    account_id VARCHAR(64),
                    anomaly_type VARCHAR(50) NOT NULL,
                    severity VARCHAR(20) NOT NULL,
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT
                );
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS dq.validation_runs (
                    run_id BIGSERIAL PRIMARY KEY,
                    run_started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    run_completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    source_record_count BIGINT NOT NULL,
                    valid_record_count BIGINT NOT NULL,
                    invalid_record_count BIGINT NOT NULL,
                    anomaly_count BIGINT NOT NULL,
                    dq_score NUMERIC(7,4) NOT NULL,
                    status VARCHAR(20) NOT NULL
                );
            """))
        else:
            # SQLite compatibility: use tables mimicking schemas
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS core_branches (
                    branch_id TEXT PRIMARY KEY,
                    branch_name TEXT NOT NULL,
                    city TEXT NOT NULL,
                    state TEXT NOT NULL,
                    region TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS core_merchants (
                    merchant_id TEXT PRIMARY KEY,
                    merchant_name TEXT NOT NULL,
                    merchant_category TEXT NOT NULL,
                    city TEXT,
                    state TEXT
                );
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS core_customers (
                    customer_id TEXT PRIMARY KEY,
                    customer_name TEXT NOT NULL,
                    date_of_birth TEXT,
                    age INTEGER,
                    gender TEXT,
                    city TEXT,
                    state TEXT,
                    customer_type TEXT,
                    annual_income REAL,
                    created_at TEXT NOT NULL
                );
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS core_accounts (
                    account_id TEXT PRIMARY KEY,
                    customer_id TEXT NOT NULL,
                    account_type TEXT NOT NULL,
                    account_open_date TEXT NOT NULL,
                    current_balance REAL DEFAULT 0.00,
                    branch_id TEXT NOT NULL,
                    account_status TEXT DEFAULT 'ACTIVE'
                );
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS raw_transactions (
                    transaction_id TEXT,
                    account_id TEXT,
                    merchant_id TEXT,
                    transaction_timestamp TEXT,
                    transaction_type TEXT,
                    channel TEXT,
                    amount REAL,
                    balance_after REAL,
                    city TEXT,
                    state TEXT,
                    status TEXT,
                    device_id TEXT,
                    ip_address TEXT,
                    login_attempts INTEGER
                );
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS core_transactions (
                    transaction_id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    merchant_id TEXT,
                    transaction_timestamp TEXT NOT NULL,
                    transaction_type TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    amount REAL NOT NULL,
                    balance_after REAL,
                    city TEXT,
                    state TEXT,
                    status TEXT NOT NULL,
                    device_id TEXT,
                    ip_address TEXT,
                    login_attempts INTEGER DEFAULT 1
                );
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS analytics_customer_segments (
                    customer_id TEXT PRIMARY KEY,
                    segment TEXT NOT NULL,
                    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS dq_anomalies (
                    anomaly_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_id TEXT,
                    account_id TEXT,
                    anomaly_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT
                );
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS dq_validation_runs (
                    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    run_completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    source_record_count INTEGER NOT NULL,
                    valid_record_count INTEGER NOT NULL,
                    invalid_record_count INTEGER NOT NULL,
                    anomaly_count INTEGER NOT NULL,
                    dq_score REAL NOT NULL,
                    status TEXT NOT NULL
                );
            """))

def init_views(eng: Engine = engine):
    """Creates the 12 analytical SQL views if not already present."""
    if DB_DIALECT == "postgresql":
        views_sql_path = BASE_DIR / "database" / "04_views.sql"
        if views_sql_path.exists():
            with open(views_sql_path, "r", encoding="utf-8") as f:
                sql_script = f.read()
            with eng.begin() as conn:
                conn.execute(text(sql_script))
    else:
        with eng.begin() as conn:
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

            conn.execute(text("""
                CREATE VIEW IF NOT EXISTS v_channel_performance AS
                SELECT
                    t.channel,
                    COUNT(*) AS transaction_count,
                    SUM(t.amount) AS transaction_value,
                    AVG(t.amount) AS avg_amount,
                    ROUND(100.0 * COUNT(*) / (SELECT MAX(1, COUNT(*)) FROM core_transactions WHERE status='SUCCESS'), 2) AS volume_pct
                FROM core_transactions t
                WHERE t.status = 'SUCCESS'
                GROUP BY t.channel
                ORDER BY transaction_count DESC;
            """))

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

            conn.execute(text("""
                CREATE VIEW IF NOT EXISTS v_failed_transactions_summary AS
                SELECT
                    SUBSTR(transaction_timestamp, 1, 10) AS transaction_date,
                    channel,
                    COUNT(CASE WHEN status != 'SUCCESS' THEN 1 END) AS failure_count,
                    COUNT(*) AS total_count,
                    ROUND(100.0 * COUNT(CASE WHEN status != 'SUCCESS' THEN 1 END) / MAX(1, COUNT(*)), 2) AS failure_rate
                FROM core_transactions
                GROUP BY SUBSTR(transaction_timestamp, 1, 10), channel
                HAVING COUNT(CASE WHEN status != 'SUCCESS' THEN 1 END) > 0
                ORDER BY failure_count DESC;
            """))

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

def ensure_initialized(eng: Engine = engine):
    """Guarantees both tables and views exist on application startup."""
    init_tables(eng)
    init_views(eng)

if __name__ == "__main__":
    ensure_initialized()
    print("Database tables and analytical views initialized successfully.")
