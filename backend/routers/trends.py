# routers/trends.py
"""
/api/trends – returns any spending anomalies detected by the analytics engine.
Each record contains the month, segment, total spent, Z‑score and a boolean flag.
"""

from fastapi import APIRouter
import pandas as pd
from api_client import engine
from analytics_engine import detect_spending_anomalies

router = APIRouter()


@router.get("/trends", summary="Spending anomalies (Z‑score > 2)")
def get_trends():
    # The analytics function returns a full DataFrame; we only need flagged rows.
    df = detect_spending_anomalies()
    flagged = df[df["flag"]].copy()

    # Convert to JSON‑serialisable dicts
    records = flagged.to_dict(orient="records")
    # Round numeric fields for nicer output
    for rec in records:
        rec["total_spent"] = round(rec["total_spent"], 2)
        rec["z_score"] = round(rec["z_score"], 2)
        rec["month"] = rec["month"].strftime("%Y-%m")
    return {"anomalies": records}
