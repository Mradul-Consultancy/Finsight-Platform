# main.py
"""
FastAPI entry‑point for the FinSight project.
- CORS is enabled for the Vite dev server (`http://localhost:5173`).
- All route modules are imported and mounted under the `/api` prefix.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import os
import sys

# Ensure backend directory is in the import path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Import routers – they will register their own paths.
from .routers import kpis, trends, segment, report, analytics

from fastapi.responses import RedirectResponse

app = FastAPI(
    title="FinSight Credit Decision Engine API",
    version="1.0.0",
    description="FastAPI backend exposing KPI, trend, segment, and PDF‑report endpoints.",
)

@app.get("/", include_in_schema=False)
def read_root():
    """Redirect root requests to the API documentation."""
    return RedirectResponse(url="/docs")

# ---------------------------------------------------------------------------------
# CORS configuration – allow the React dev server to call the API.
# Adjust the `allow_origins` list if you serve the frontend from a different host.
# ---------------------------------------------------------------------------------
allowed_origins_env = os.environ.get("ALLOWED_ORIGINS", "")
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]
if allowed_origins_env:
    origins.extend([o.strip() for o in allowed_origins_env.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if not allowed_origins_env.startswith("*") else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register routers under the `/api` prefix.
app.include_router(kpis.router, prefix="/api")
app.include_router(trends.router, prefix="/api")
app.include_router(segment.router, prefix="/api")
app.include_router(report.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
