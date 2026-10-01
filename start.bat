@echo off
title FinSight Banking Analytics Platform
echo ============================================================
echo          FinSight Banking Platform Launcher
echo ============================================================
echo.

echo [1/3] Starting Python FastAPI Backend on port 8002...
start "FinSight API (FastAPI)" cmd /k "python -m uvicorn backend.main:app --port 8002 --reload"

echo [2/3] Starting Streamlit 5-Page Dashboard on port 8501...
start "FinSight Streamlit Dashboard" cmd /k "streamlit run dashboard/app.py --server.port 8501"

echo [3/3] Starting React Vite Dashboard on port 5173...
start "FinSight React Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ============================================================
echo  FinSight services are running:
echo  - Streamlit Dashboard: http://localhost:8501 (5-Page Console)
echo  - React Dashboard:     http://localhost:5173 (Web App)
echo  - FastAPI Backend:     http://localhost:8002/docs (Swagger UI)
echo ============================================================
echo.
timeout /t 3 >nul
start http://localhost:8501
exit
