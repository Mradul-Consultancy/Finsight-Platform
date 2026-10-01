-- ====================================================================
-- 04_views.sql: Exactly 12 Analytical SQL Views for FinSight
-- ====================================================================

-- ── View 1: Daily Transaction Summary ──
CREATE OR REPLACE VIEW analytics.v_daily_transaction_summary AS
SELECT
    DATE(transaction_timestamp) AS transaction_date,
    COUNT(*) AS transaction_count,
    SUM(CASE WHEN transaction_type IN ('DEBIT', 'WITHDRAWAL', 'PAYMENT') THEN amount ELSE 0 END) AS total_debit,
    SUM(CASE WHEN transaction_type = 'CREDIT' THEN amount ELSE 0 END) AS total_credit,
    AVG(amount) AS avg_transaction_amount
FROM core.transactions
WHERE status = 'SUCCESS'
GROUP BY DATE(transaction_timestamp)
ORDER BY transaction_date DESC;

-- ── View 2: Monthly Transaction Summary ──
CREATE OR REPLACE VIEW analytics.v_monthly_transaction_summary AS
SELECT
    TO_CHAR(transaction_timestamp, 'YYYY-MM') AS month,
    COUNT(*) AS transaction_count,
    SUM(amount) AS total_value,
    SUM(CASE WHEN transaction_type IN ('DEBIT', 'WITHDRAWAL', 'PAYMENT') THEN amount ELSE 0 END) AS total_debit,
    SUM(CASE WHEN transaction_type = 'CREDIT' THEN amount ELSE 0 END) AS total_credit,
    AVG(amount) AS avg_transaction
FROM core.transactions
WHERE status = 'SUCCESS'
GROUP BY TO_CHAR(transaction_timestamp, 'YYYY-MM')
ORDER BY month;

-- ── View 3: Branch Performance ──
CREATE OR REPLACE VIEW analytics.v_branch_performance AS
SELECT
    b.branch_id,
    b.branch_name,
    b.region,
    b.city,
    COUNT(t.transaction_id) AS transaction_count,
    COALESCE(SUM(t.amount), 0) AS transaction_value,
    COUNT(DISTINCT a.account_id) AS active_accounts
FROM core.branches b
JOIN core.accounts a ON b.branch_id = a.branch_id
LEFT JOIN core.transactions t ON a.account_id = t.account_id AND t.status = 'SUCCESS'
GROUP BY b.branch_id, b.branch_name, b.region, b.city
ORDER BY transaction_value DESC;

-- ── View 4: Customer Segment Performance ──
CREATE OR REPLACE VIEW analytics.v_customer_segment_performance AS
SELECT
    cs.segment,
    COUNT(DISTINCT c.customer_id) AS customers,
    COUNT(t.transaction_id) AS transactions,
    COALESCE(SUM(t.amount), 0) AS total_value,
    COALESCE(AVG(a.current_balance), 0) AS average_balance,
    COALESCE(AVG(t.amount), 0) AS avg_transaction_amount
FROM analytics.customer_segments cs
JOIN core.customers c ON cs.customer_id = c.customer_id
JOIN core.accounts a ON c.customer_id = a.customer_id
LEFT JOIN core.transactions t ON a.account_id = t.account_id AND t.status = 'SUCCESS'
GROUP BY cs.segment
ORDER BY total_value DESC;

-- ── View 5: Merchant-Category Performance ──
CREATE OR REPLACE VIEW analytics.v_merchant_category_performance AS
SELECT
    m.merchant_category,
    COUNT(t.transaction_id) AS transactions,
    COALESCE(SUM(t.amount), 0) AS transaction_value,
    COALESCE(AVG(t.amount), 0) AS avg_amount
FROM core.merchants m
LEFT JOIN core.transactions t ON m.merchant_id = t.merchant_id AND t.status = 'SUCCESS'
GROUP BY m.merchant_category
ORDER BY transaction_value DESC;

-- ── View 6: Channel Performance ──
CREATE OR REPLACE VIEW analytics.v_channel_performance AS
SELECT
    t.channel,
    COUNT(*) AS transaction_count,
    SUM(t.amount) AS transaction_value,
    AVG(t.amount) AS avg_amount,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS volume_pct
FROM core.transactions t
WHERE t.status = 'SUCCESS'
GROUP BY t.channel
ORDER BY transaction_count DESC;

-- ── View 7: Debit vs Credit Summary ──
CREATE OR REPLACE VIEW analytics.v_debit_credit_summary AS
SELECT
    a.account_id,
    c.customer_name,
    SUM(CASE WHEN t.transaction_type IN ('DEBIT', 'WITHDRAWAL', 'PAYMENT') THEN t.amount ELSE 0 END) AS total_debit,
    SUM(CASE WHEN t.transaction_type = 'CREDIT' THEN t.amount ELSE 0 END) AS total_credit,
    SUM(CASE WHEN t.transaction_type = 'CREDIT' THEN t.amount ELSE -t.amount END) AS net_flow
FROM core.accounts a
JOIN core.customers c ON a.customer_id = c.customer_id
LEFT JOIN core.transactions t ON a.account_id = t.account_id AND t.status = 'SUCCESS'
GROUP BY a.account_id, c.customer_name;

-- ── View 8: Active-Account Summary ──
CREATE OR REPLACE VIEW analytics.v_active_accounts_summary AS
SELECT
    a.account_type,
    COUNT(CASE WHEN a.account_status = 'ACTIVE' THEN 1 END) AS active_accounts,
    COUNT(CASE WHEN a.account_status != 'ACTIVE' THEN 1 END) AS inactive_accounts,
    AVG(a.current_balance) AS average_balance,
    SUM(a.current_balance) AS total_liquidity
FROM core.accounts a
GROUP BY a.account_type;

-- ── View 9: Top Customers ──
CREATE OR REPLACE VIEW analytics.v_top_customers AS
SELECT
    c.customer_id,
    c.customer_name,
    cs.segment,
    COUNT(t.transaction_id) AS transaction_count,
    COALESCE(SUM(t.amount), 0) AS total_value,
    COALESCE(AVG(t.amount), 0) AS average_transaction
FROM core.customers c
JOIN analytics.customer_segments cs ON c.customer_id = cs.customer_id
JOIN core.accounts a ON c.customer_id = a.customer_id
JOIN core.transactions t ON a.account_id = t.account_id AND t.status = 'SUCCESS'
GROUP BY c.customer_id, c.customer_name, cs.segment
ORDER BY total_value DESC
LIMIT 100;

-- ── View 10: Failed Transaction Summary ──
CREATE OR REPLACE VIEW analytics.v_failed_transactions_summary AS
SELECT
    DATE(transaction_timestamp) AS transaction_date,
    channel,
    COUNT(CASE WHEN status != 'SUCCESS' THEN 1 END) AS failure_count,
    COUNT(*) AS total_count,
    ROUND(100.0 * COUNT(CASE WHEN status != 'SUCCESS' THEN 1 END) / COUNT(*), 2) AS failure_rate
FROM core.transactions
GROUP BY DATE(transaction_timestamp), channel
HAVING COUNT(CASE WHEN status != 'SUCCESS' THEN 1 END) > 0
ORDER BY failure_count DESC;

-- ── View 11: Anomaly Summary ──
CREATE OR REPLACE VIEW analytics.v_anomaly_summary AS
SELECT
    anomaly_type,
    severity,
    COUNT(*) AS count,
    MIN(detected_at) AS first_detected,
    MAX(detected_at) AS last_detected
FROM dq.anomalies
GROUP BY anomaly_type, severity
ORDER BY count DESC;

-- ── View 12: Customer Risk & Quality Summary ──
CREATE OR REPLACE VIEW analytics.v_customer_risk_summary AS
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
FROM core.customers c
LEFT JOIN analytics.customer_segments cs ON c.customer_id = cs.customer_id
LEFT JOIN core.accounts acc ON c.customer_id = acc.customer_id
LEFT JOIN core.transactions t ON acc.account_id = t.account_id
LEFT JOIN dq.anomalies a ON acc.account_id = a.account_id
GROUP BY c.customer_id, c.customer_name, cs.segment;
