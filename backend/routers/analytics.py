# routers/analytics.py
"""
/api/analytics/* – enhanced analytics endpoints for the premium dashboard.
Provides channel distribution, monthly volume, top locations, and transaction details.
"""

from fastapi import APIRouter, Query
from sqlalchemy import text
from api_client import engine

router = APIRouter()


@router.get("/analytics/channel-distribution", summary="Transaction count by channel")
def get_channel_distribution():
    """Returns the number of transactions per channel (ATM, Online, Branch)."""
    with engine.connect() as conn:
        sql = text("""
            SELECT channel, COUNT(*) as count, SUM(transaction_amount) as total_amount
            FROM fact_transactions
            GROUP BY channel
            ORDER BY count DESC;
        """)
        rows = conn.execute(sql).fetchall()

    return {
        "channels": [
            {
                "channel": row[0],
                "count": int(row[1]),
                "total_amount": round(float(row[2]), 2)
            }
            for row in rows
        ]
    }


@router.get("/analytics/monthly-volume", summary="Monthly transaction volume and spend")
def get_monthly_volume():
    """Returns monthly aggregated transaction count, total spend, and avg amount."""
    with engine.connect() as conn:
        if engine.dialect.name == "postgresql":
            sql = text("""
                SELECT
                    DATE_TRUNC('month', transaction_date) AS month,
                    COUNT(*) as txn_count,
                    SUM(transaction_amount) as total_spend,
                    AVG(transaction_amount) as avg_amount
                FROM fact_transactions
                GROUP BY month
                ORDER BY month;
            """)
        else:
            sql = text("""
                SELECT
                    strftime('%Y-%m-01', transaction_date) AS month,
                    COUNT(*) as txn_count,
                    SUM(transaction_amount) as total_spend,
                    AVG(transaction_amount) as avg_amount
                FROM fact_transactions
                GROUP BY strftime('%Y-%m-01', transaction_date)
                ORDER BY month;
            """)
        rows = conn.execute(sql).fetchall()

    return {
        "months": [
            {
                "month": str(row[0])[:7] if row[0] else None,
                "txn_count": int(row[1]),
                "total_spend": round(float(row[2]), 2),
                "avg_amount": round(float(row[3]), 2)
            }
            for row in rows
        ]
    }


@router.get("/analytics/top-locations", summary="Top 10 locations by transaction volume")
def get_top_locations():
    """Returns the top 10 locations by number of transactions."""
    with engine.connect() as conn:
        sql = text("""
            SELECT location, COUNT(*) as txn_count, SUM(transaction_amount) as total_amount
            FROM fact_transactions
            GROUP BY location
            ORDER BY txn_count DESC
            LIMIT 10;
        """)
        rows = conn.execute(sql).fetchall()

    return {
        "locations": [
            {
                "location": row[0],
                "txn_count": int(row[1]),
                "total_amount": round(float(row[2]), 2)
            }
            for row in rows
        ]
    }


@router.get("/analytics/transactions", summary="Paginated transaction list with search")
def get_transactions(
    search: str = Query("", description="Search by account, merchant, location"),
    page: int = Query(1, ge=1),
    per_page: int = Query(15, ge=5, le=100),
    sort_by: str = Query("transaction_date", description="Column to sort by"),
    sort_dir: str = Query("desc", description="asc or desc"),
):
    """Returns paginated transaction records with optional search and sorting."""
    valid_sort_cols = {
        "transaction_date", "transaction_amount", "account_balance",
        "customer_id", "location", "channel", "transaction_type"
    }
    if sort_by not in valid_sort_cols:
        sort_by = "transaction_date"
    if sort_dir not in ("asc", "desc"):
        sort_dir = "desc"

    offset = (page - 1) * per_page

    with engine.connect() as conn:
        # Count total matching rows
        if search:
            count_sql = text("""
                SELECT COUNT(*) FROM fact_transactions
                WHERE customer_id LIKE :q OR merchant_id LIKE :q OR location LIKE :q OR channel LIKE :q
            """)
            total = conn.execute(count_sql, {"q": f"%{search}%"}).scalar()

            data_sql = text(f"""
                SELECT transaction_id, customer_id, merchant_id, transaction_amount,
                       transaction_date, transaction_type, location, channel,
                       account_balance, login_attempts
                FROM fact_transactions
                WHERE customer_id LIKE :q OR merchant_id LIKE :q OR location LIKE :q OR channel LIKE :q
                ORDER BY {sort_by} {sort_dir}
                LIMIT :limit OFFSET :offset
            """)
            rows = conn.execute(data_sql, {"q": f"%{search}%", "limit": per_page, "offset": offset}).fetchall()
        else:
            count_sql = text("SELECT COUNT(*) FROM fact_transactions")
            total = conn.execute(count_sql).scalar()

            data_sql = text(f"""
                SELECT transaction_id, customer_id, merchant_id, transaction_amount,
                       transaction_date, transaction_type, location, channel,
                       account_balance, login_attempts
                FROM fact_transactions
                ORDER BY {sort_by} {sort_dir}
                LIMIT :limit OFFSET :offset
            """)
            rows = conn.execute(data_sql, {"limit": per_page, "offset": offset}).fetchall()

    transactions = []
    for row in rows:
        transactions.append({
            "transaction_id": row[0],
            "customer_id": row[1],
            "merchant_id": row[2],
            "transaction_amount": round(float(row[3]), 2) if row[3] else 0,
            "transaction_date": str(row[4]) if row[4] else None,
            "transaction_type": row[5],
            "location": row[6],
            "channel": row[7],
            "account_balance": round(float(row[8]), 2) if row[8] else 0,
            "login_attempts": int(row[9]) if row[9] else 0,
        })

    return {
        "transactions": transactions,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": max(1, (total + per_page - 1) // per_page),
    }


@router.get("/analytics/segment-overview", summary="All segments overview")
def get_segment_overview():
    """Returns spend totals and transaction counts per demographic segment."""
    with engine.connect() as conn:
        sql = text("""
            SELECT c.segment,
                   COUNT(*) as txn_count,
                   SUM(f.transaction_amount) as total_spend,
                   AVG(f.transaction_amount) as avg_amount,
                   AVG(c.age) as avg_age
            FROM fact_transactions f
            JOIN dim_customers c ON f.customer_id = c.customer_id
            GROUP BY c.segment
            ORDER BY total_spend DESC;
        """)
        rows = conn.execute(sql).fetchall()

    return {
        "segments": [
            {
                "segment": row[0],
                "txn_count": int(row[1]),
                "total_spend": round(float(row[2]), 2),
                "avg_amount": round(float(row[3]), 2),
                "avg_age": round(float(row[4]), 1)
            }
            for row in rows
        ]
    }
