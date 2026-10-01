# src/db.py
"""
Database connection manager and dual-engine compatibility layer.
Supports both PostgreSQL (production) and SQLite (zero-config local runtime).
"""

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from src.config import POSTGRES_URI, SQLITE_URI

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

if __name__ == "__main__":
    init_tables()
    print("Database tables initialized successfully.")
