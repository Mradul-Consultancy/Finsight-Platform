# routers/segment.py
"""
/api/segment/{segment_id} – returns the monthly spend history for a single customer segment.
The `segment_id` corresponds to the `segment` column created in the view
`vw_monthly_spending_by_segment` (e.g., "Young", "Mid", "Senior").
"""

from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from api_client import engine

router = APIRouter()


@router.get("/segment/{segment_id}", summary="Monthly spend for a segment")
def get_segment(segment_id: str):
    with engine.connect() as conn:
        sql = text(
            """
            SELECT
                month,
                total_spent
            FROM vw_monthly_spending_by_segment
            WHERE segment = :seg
            ORDER BY month;
            """
        )
        rows = conn.execute(sql, {"seg": segment_id}).fetchall()

    if not rows:
        raise HTTPException(status_code=404, detail=f"Segment '{segment_id}' not found")

    data = []
    for row in rows:
        m = row[0]
        month_str = m.strftime("%Y-%m") if hasattr(m, "strftime") else str(m)[:7]
        data.append({
            "month": month_str,
            "total_spent": round(row[1], 2)
        })
    return {"segment": segment_id, "history": data}
