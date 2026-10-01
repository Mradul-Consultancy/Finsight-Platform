-- ====================================================================
-- 01_schemas.sql: Multi-Schema Architecture for FinSight
-- ====================================================================
-- raw:       Incoming untrusted staging transactions and source records
-- core:      Validated and sanitized core banking master & ledger data
-- analytics: Materialized and virtual reporting SQL views
-- dq:        Data quality surveillance, anomalies, and pipeline run logs
-- ====================================================================

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS dq;
