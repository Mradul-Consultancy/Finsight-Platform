-- ====================================================================
-- 05_validation.sql: Data Quality & Anomaly Extraction Rules
-- ====================================================================

-- ── Rule 1: High Transaction Amount Outliers (> 500,000) ──
INSERT INTO dq.anomalies (transaction_id, account_id, anomaly_type, severity, description)
SELECT
    transaction_id,
    account_id,
    'HIGH_AMOUNT',
    'HIGH',
    'Transaction amount ' || amount || ' exceeds maximum single transaction threshold of 500,000'
FROM raw.transactions
WHERE amount > 500000;

-- ── Rule 2: Invalid / Unregistered Account Reference ──
INSERT INTO dq.anomalies (transaction_id, account_id, anomaly_type, severity, description)
SELECT
    t.transaction_id,
    t.account_id,
    'INVALID_ACCOUNT',
    'CRITICAL',
    'Account ID ' || t.account_id || ' does not exist in core banking accounts ledger'
FROM raw.transactions t
LEFT JOIN core.accounts a ON t.account_id = a.account_id
WHERE a.account_id IS NULL;

-- ── Rule 3: Rapid Burst / Velocity Transactions ──
-- Flagged when multiple transactions occur on the same account within 5 seconds
WITH ordered_txns AS (
    SELECT
        transaction_id,
        account_id,
        transaction_timestamp,
        LAG(transaction_timestamp) OVER (
            PARTITION BY account_id
            ORDER BY transaction_timestamp
        ) AS prev_timestamp
    FROM raw.transactions
)
INSERT INTO dq.anomalies (transaction_id, account_id, anomaly_type, severity, description)
SELECT
    transaction_id,
    account_id,
    'RAPID_TRANSACTIONS',
    'HIGH',
    'Rapid velocity transaction detected within 5 seconds of previous activity'
FROM ordered_txns
WHERE prev_timestamp IS NOT NULL
  AND EXTRACT(EPOCH FROM (transaction_timestamp - prev_timestamp)) <= 5;

-- ── Rule 4: Negative or Impossible Account Balance ──
INSERT INTO dq.anomalies (transaction_id, account_id, anomaly_type, severity, description)
SELECT
    transaction_id,
    account_id,
    'NEGATIVE_BALANCE',
    'HIGH',
    'Balance after transaction is negative (' || balance_after || ') or mathematically impossible'
FROM raw.transactions
WHERE balance_after < 0;

-- ── Rule 5: Duplicate Transactions ──
WITH duplicate_txns AS (
    SELECT
        transaction_id,
        account_id,
        ROW_NUMBER() OVER (
            PARTITION BY account_id, transaction_timestamp, amount, transaction_type
            ORDER BY transaction_id
        ) AS row_num
    FROM raw.transactions
)
INSERT INTO dq.anomalies (transaction_id, account_id, anomaly_type, severity, description)
SELECT
    transaction_id,
    account_id,
    'DUPLICATE',
    'MEDIUM',
    'Duplicate transaction detected with identical account, timestamp, amount, and type'
FROM duplicate_txns
WHERE row_num > 1;

-- ── Rule 6: Location / Geographic Mismatch ──
INSERT INTO dq.anomalies (transaction_id, account_id, anomaly_type, severity, description)
SELECT
    t.transaction_id,
    t.account_id,
    'LOCATION_MISMATCH',
    'MEDIUM',
    'Transaction location state (' || t.state || ') mismatches customer registered home state (' || c.state || ')'
FROM raw.transactions t
JOIN core.accounts a ON t.account_id = a.account_id
JOIN core.customers c ON a.customer_id = c.customer_id
WHERE t.state IS NOT NULL
  AND c.state IS NOT NULL
  AND t.state != c.state
  AND t.channel IN ('ATM', 'BRANCH');
