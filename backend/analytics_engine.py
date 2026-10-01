# analytics_engine.py
"""
Analytics engine for credit-risk and transaction anomaly detection.
Provides spending anomalies detection and board-ready PDF generation.
"""
import pandas as pd
import numpy as np
from sqlalchemy import text
from datetime import datetime
import matplotlib.pyplot as plt
from io import BytesIO
from reportlab.lib.pagesizes import LETTER
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image

# Import the shared database engine
from api_client import engine

# Helper: fetch a view into a pandas DataFrame
def fetch_view(view_name: str) -> pd.DataFrame:
    """Execute ``SELECT * FROM <view_name>`` and return a DataFrame."""
    with engine.connect() as conn:
        df = pd.read_sql_query(text(f"SELECT * FROM {view_name}"), conn)
    return df

# 1️⃣ Trend detection – Z‑score against a 90‑day rolling window
def detect_spending_anomalies() -> pd.DataFrame:
    """Identify segments whose *monthly* spend deviates > 2 σ from the
    previous 3‑month (≈90 days) rolling statistics.

    Returns a DataFrame containing:
        - month (datetime)
        - segment (str)
        - total_spent (float)
        - rolling_mean (float)
        - rolling_std (float)
        - z_score (float)
        - flag (bool) – True when |z| > 2
    """
    df = fetch_view("vw_monthly_spending_by_segment")
    
    # Ensure proper datetime handling
    df["month"] = pd.to_datetime(df["month"])

    # Sort for rolling calculations
    df = df.sort_values(["segment", "month"]).reset_index(drop=True)

    # Compute rolling statistics per segment (window=3 months)
    df["rolling_mean"] = (
        df.groupby("segment")["total_spent"].transform(lambda s: s.rolling(window=3, min_periods=1).mean())
    )
    df["rolling_std"] = (
        df.groupby("segment")["total_spent"].transform(lambda s: s.rolling(window=3, min_periods=1).std(ddof=0))
    )
    # If std is zero (no variance) set to a tiny epsilon to avoid division‑by‑zero
    df["rolling_std"] = df["rolling_std"].replace(0, np.finfo(float).eps)
    df["z_score"] = (df["total_spent"] - df["rolling_mean"]) / df["rolling_std"]
    df["flag"] = df["z_score"].abs() > 2
    return df

# 2️⃣ PDF report generator – one‑page executive brief
def _create_spending_chart(df_latest: pd.DataFrame) -> BytesIO:
    """Generate a horizontal bar chart of segment spend for the latest month.
    Returns the image as an in‑memory PNG suitable for ReportLab.
    """
    fig, ax = plt.subplots(figsize=(6, 3))
    segments = df_latest["segment"]
    amounts = df_latest["total_spent"]
    ax.barh(segments, amounts, color="#4a90e2")
    ax.set_xlabel("Spend ($)")
    ax.set_title("Spending by Segment – Latest Month")
    plt.tight_layout()
    img_bytes = BytesIO()
    fig.savefig(img_bytes, format="png", dpi=150)
    plt.close(fig)
    img_bytes.seek(0)
    return img_bytes

def generate_executive_report(pdf_path: str = "executive_report.pdf") -> None:
    """Produce a one‑page PDF summarising key KPIs, a spend chart and any risk flags.

    The function:
    1. Pulls the latest month of ``vw_monthly_spending_by_segment``.
    2. Computes overall KPIs (total spend, avg transaction amount, latest fraud rate).
    3. Runs ``detect_spending_anomalies`` to obtain any flagged segments.
    4. Assembles the data into a polished ReportLab document.
    """
    # 1️⃣ Gather data
    monthly_df = fetch_view("vw_monthly_spending_by_segment")
    monthly_df["month"] = pd.to_datetime(monthly_df["month"])
    latest_month = monthly_df["month"].max()
    latest_spend = monthly_df[monthly_df["month"] == latest_month]

    # Overall KPIs – total spend (last month) & avg transaction amount
    total_spend = latest_spend["total_spent"].sum()
    
    # Average transaction amount across all transactions (latest month)
    txn_df = fetch_view("fact_transactions")
    txn_df["transaction_date"] = pd.to_datetime(txn_df["transaction_date"])
    
    # Get average for the latest month
    # Support both datetime and period comparison
    latest_period = latest_month.to_period("M")
    avg_txn_amount = (
        txn_df[txn_df["transaction_date"].dt.to_period("M") == latest_period]["transaction_amount"].mean()
    )
    
    # Latest fraud‑rate (most recent row in the view)
    fraud_df = fetch_view("vw_rolling_7d_fraud_rate")
    fraud_df["transaction_date"] = pd.to_datetime(fraud_df["transaction_date"])
    latest_fraud_rate = fraud_df.sort_values("transaction_date", ascending=False).iloc[0]["fraud_rate_percent"]

    # Risk flags – segments where spending deviated >2σ
    anomalies = detect_spending_anomalies()
    flagged = anomalies[anomalies["flag"] & (anomalies["month"] == latest_month)]

    # 2️⃣ Build PDF with ReportLab
    doc = SimpleDocTemplate(pdf_path, pagesize=LETTER, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph("<b>Executive Credit‑Transaction Summary</b>", styles["Title"]))
    story.append(Spacer(1, 12))

    # KPI Table
    kpi_data = [
        ["Latest Month", latest_month.strftime("%b %Y")],
        ["Total Spend", f"${total_spend:,.2f}"],
        ["Avg Transaction", f"${avg_txn_amount:,.2f}"],
        ["7‑Day Fraud Rate", f"{latest_fraud_rate:.2f}%"],
    ]
    kpi_table = Table(kpi_data, colWidths=[150, 200])
    kpi_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )
    )
    story.append(kpi_table)
    story.append(Spacer(1, 16))

    # Bar chart – spend by segment (latest month)
    chart_img = _create_spending_chart(latest_spend)
    story.append(Image(chart_img, width=400, height=200))
    story.append(Spacer(1, 16))

    # Risk flags table (if any)
    if not flagged.empty:
        story.append(Paragraph("<b>Spending Anomalies (Z‑score > 2)</b>", styles["Heading2"]))
        flagged_display = flagged[["segment", "total_spent", "z_score"]].copy()
        flagged_display["total_spent"] = flagged_display["total_spent"].apply(lambda x: f"${x:,.2f}")
        flagged_display["z_score"] = flagged_display["z_score"].apply(lambda z: f"{z:.2f}")
        risk_data = [
            ["Segment", "Spend", "Z‑Score"]
        ] + flagged_display.values.tolist()
        risk_table = Table(risk_data, colWidths=[150, 150, 100])
        risk_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightcoral),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ]
            )
        )
        story.append(risk_table)
    else:
        story.append(Paragraph("No spending anomalies detected for the latest month.", styles["Normal"]))

    # Build PDF
    doc.build(story)
    print(f"Executive report written to {pdf_path}")
