# routers/kpis.py
"""
/api/kpis – returns the three core KPI values:
1️⃣ Total spend for the latest month
2️⃣ Average transaction amount (latest month)
3️⃣ Latest 7‑day fraud‑rate (percentage)
"""

from fastapi import APIRouter
from sqlalchemy import text
from api_client import engine

router = APIRouter()


@router.get("/kpis", summary="Current KPI snapshot")
def get_kpis():
    with engine.connect() as conn:
        # 1️⃣ Total spend & avg txn amount – use the fact table aggregated by month.
        if engine.dialect.name == "postgresql":
            kpi_sql = text(
                """
                SELECT
                    DATE_TRUNC('month', transaction_date) AS month,
                    SUM(transaction_amount) AS total_spend,
                    AVG(transaction_amount) AS avg_txn
                FROM fact_transactions
                GROUP BY month
                ORDER BY month DESC
                LIMIT 1;
                """
            )
        else:
            kpi_sql = text(
                """
                SELECT
                    strftime('%Y-%m-01', transaction_date) AS month,
                    SUM(transaction_amount) AS total_spend,
                    AVG(transaction_amount) AS avg_txn
                FROM fact_transactions
                GROUP BY strftime('%Y-%m-01', transaction_date)
                ORDER BY month DESC
                LIMIT 1;
                """
            )
        kpi_row = conn.execute(kpi_sql).fetchone()

        # 2️⃣ 7‑day fraud rate – latest row from the view.
        fraud_sql = text(
            """
            SELECT fraud_rate_percent
            FROM vw_rolling_7d_fraud_rate
            ORDER BY transaction_date DESC
            LIMIT 1;
            """
        )
        fraud_row = conn.execute(fraud_sql).fetchone()

    total_spend = float(kpi_row[1]) if kpi_row and kpi_row[1] is not None else 0.0
    avg_txn = float(kpi_row[2]) if kpi_row and kpi_row[2] is not None else 0.0
    fraud_rate = float(fraud_row[0]) if fraud_row and fraud_row[0] is not None else 0.0

    month_val = None
    if kpi_row and kpi_row[0]:
        raw_month = kpi_row[0]
        if hasattr(raw_month, "strftime"):
            month_val = raw_month.strftime("%Y-%m")
        else:
            month_val = str(raw_month)[:7]

    return {
        "month": month_val,
        "total_spend": round(total_spend, 2),
        "avg_transaction_amount": round(avg_txn, 2),
        "fraud_rate_percent": round(fraud_rate, 2),
    }
