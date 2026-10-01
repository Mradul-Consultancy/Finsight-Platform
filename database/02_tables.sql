-- ====================================================================
-- 02_tables.sql: Core Banking Entities & Data Quality Storage
-- ====================================================================

-- ── 1. RAW / STAGING LAYER ──
CREATE TABLE IF NOT EXISTS raw.transactions (
    transaction_id VARCHAR(64),
    account_id VARCHAR(64),
    merchant_id VARCHAR(64),
    transaction_timestamp TIMESTAMP,
    transaction_type VARCHAR(30),
    channel VARCHAR(30),
    amount NUMERIC(14,2),
    balance_after NUMERIC(14,2),
    city VARCHAR(100),
    state VARCHAR(100),
    status VARCHAR(30),
    device_id VARCHAR(64),
    ip_address VARCHAR(45),
    login_attempts INT
);

-- ── 2. CORE MASTER DATA ──
CREATE TABLE IF NOT EXISTS core.branches (
    branch_id VARCHAR(32) PRIMARY KEY,
    branch_name VARCHAR(120) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    region VARCHAR(30) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS core.merchants (
    merchant_id VARCHAR(32) PRIMARY KEY,
    merchant_name VARCHAR(120) NOT NULL,
    merchant_category VARCHAR(50) NOT NULL,
    city VARCHAR(100),
    state VARCHAR(100)
);

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

CREATE TABLE IF NOT EXISTS core.accounts (
    account_id VARCHAR(32) PRIMARY KEY,
    customer_id VARCHAR(32) NOT NULL,
    account_type VARCHAR(30) NOT NULL,
    account_open_date DATE NOT NULL,
    current_balance NUMERIC(14,2) DEFAULT 0.00,
    branch_id VARCHAR(32) NOT NULL,
    account_status VARCHAR(20) DEFAULT 'ACTIVE',
    FOREIGN KEY (customer_id) REFERENCES core.customers(customer_id),
    FOREIGN KEY (branch_id) REFERENCES core.branches(branch_id)
);

-- ── 3. CORE VALIDATED TRANSACTIONS ──
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
    login_attempts INT DEFAULT 1,
    FOREIGN KEY (account_id) REFERENCES core.accounts(account_id),
    FOREIGN KEY (merchant_id) REFERENCES core.merchants(merchant_id)
);

-- ── 4. ANALYTICS SEGMENTATION ──
CREATE TABLE IF NOT EXISTS analytics.customer_segments (
    customer_id VARCHAR(32) PRIMARY KEY,
    segment VARCHAR(30) NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES core.customers(customer_id)
);

-- ── 5. DATA QUALITY & ANOMALIES ──
CREATE TABLE IF NOT EXISTS dq.anomalies (
    anomaly_id BIGSERIAL PRIMARY KEY,
    transaction_id VARCHAR(64),
    account_id VARCHAR(64),
    anomaly_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

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
