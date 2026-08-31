@echo off
echo ==============================================
echo OpsNexus Backend Startup Script (Windows)
echo ==============================================
echo.

echo [1/3] Starting Docker services (Postgres + Redis)...
docker compose up -d db redis
if %ERRORLEVEL% neq 0 (
    echo ERROR: Docker failed to start. Is Docker Desktop running?
    pause
    exit /b 1
)

echo Waiting 3 seconds for services to be ready...
timeout /t 3 /nobreak > nul

echo Stopping any stale rqworker processes...
taskkill /F /FI "WINDOWTITLE eq OpsNexus - Background Worker*" >nul 2>&1

echo [2/3] Starting Django Development Server...
start "OpsNexus - Django Server" cmd /k "cd /d %~dp0backend && .venv\Scripts\activate && python manage.py runserver"

echo [3/3] Starting Background RQ Worker (SimpleWorker)...
start "OpsNexus - Background Worker" cmd /k "cd /d %~dp0backend && .venv\Scripts\activate && python manage.py rqworker default --worker-class rq.worker.SimpleWorker"

echo.
echo All services started!
echo - Docker (Postgres + Redis): running in background
echo - Django Server: running in a new window
echo - RQ Worker: running in a new window
echo.
echo Keep the Django and RQ Worker windows open while developing.
echo ==============================================
