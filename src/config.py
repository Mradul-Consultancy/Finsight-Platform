# src/config.py
"""
Central configuration for FinSight Credit & Banking Analytics Platform.
Loads environment variables and sets analytical thresholds.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Database settings
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "finsight")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")

POSTGRES_URI = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
SQLITE_PATH = BASE_DIR / "backend" / "finsight_core.db"
SQLITE_URI = f"sqlite:///{SQLITE_PATH.as_posix()}"

# Anomaly Thresholds
HIGH_AMOUNT_THRESHOLD = 500000.00
RAPID_TXN_SECONDS = 5
MAX_DAILY_FAILED_ATTEMPTS = 3
TARGET_DQ_SCORE = 99.986
TARGET_ANOMALY_COUNT = 342

# Report Directory
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
