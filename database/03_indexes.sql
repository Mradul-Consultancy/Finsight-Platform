-- ====================================================================
-- 03_indexes.sql: Performance Indexes for High-Volume Analytics
-- ====================================================================

-- Core Transactions
CREATE INDEX IF NOT EXISTS idx_transactions_account
ON core.transactions(account_id);

CREATE INDEX IF NOT EXISTS idx_transactions_timestamp
ON core.transactions(transaction_timestamp);

CREATE INDEX IF NOT EXISTS idx_transactions_channel
ON core.transactions(channel);

CREATE INDEX IF NOT EXISTS idx_transactions_state
ON core.transactions(state);

CREATE INDEX IF NOT EXISTS idx_transactions_merchant
ON core.transactions(merchant_id);

CREATE INDEX IF NOT EXISTS idx_transactions_status
ON core.transactions(status);

-- Core Accounts & Customers
CREATE INDEX IF NOT EXISTS idx_accounts_customer
ON core.accounts(customer_id);

CREATE INDEX IF NOT EXISTS idx_accounts_branch
ON core.accounts(branch_id);

-- Data Quality
CREATE INDEX IF NOT EXISTS idx_anomalies_type
ON dq.anomalies(anomaly_type);

CREATE INDEX IF NOT EXISTS idx_anomalies_txn
ON dq.anomalies(transaction_id);
