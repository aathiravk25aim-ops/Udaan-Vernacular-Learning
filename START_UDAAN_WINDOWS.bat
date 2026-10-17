@echo off
setlocal
set "ROOT=%~dp0"
echo ==============================================
echo   UDAAN - Primary Learning Platform (Local)
echo ==============================================
where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Install Python 3.10+ and select "Add Python to PATH".
  pause
  exit /b 1
)
where node >nul 2>nul
if errorlevel 1 (
  echo Node.js was not found. Install Node.js 18+ and restart this script.
  pause
  exit /b 1
)
if not exist "%ROOT%backend\.venv\Scripts\python.exe" (
  echo Creating Python virtual environment...
  python -m venv "%ROOT%backend\.venv"
  if errorlevel 1 goto failed
)
echo Installing backend dependencies...
"%ROOT%backend\.venv\Scripts\python.exe" -m pip install -r "%ROOT%backend\requirements.txt"
if errorlevel 1 goto failed
echo Installing frontend dependencies...
cd /d "%ROOT%frontend"
call npm install
if errorlevel 1 goto failed
echo Starting API at http://127.0.0.1:8000 ...
start "Udaan Backend API" /D "%ROOT%backend" cmd /k ""%ROOT%backend\.venv\Scripts\python.exe" -m uvicorn app:app --reload --host 127.0.0.1 --port 8000"
echo Waiting for API to be ready (up to 30 seconds)...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$until=(Get-Date).AddSeconds(30); do { try { $r=Invoke-WebRequest -Uri 'http://127.0.0.1:8000/api/health' -TimeoutSec 2 -UseBasicParsing; if ($r.StatusCode -eq 200) { exit 0 } } catch {}; Start-Sleep -Seconds 1 } while ((Get-Date) -lt $until); exit 1"
if errorlevel 1 echo WARNING: API health check did not respond. Check the Udaan Backend API window for an error.
echo Starting website at http://localhost:5173 ...
start "Udaan Website" /D "%ROOT%frontend" cmd /k "npm run dev"
timeout /t 3 /nobreak >nul
start "" "http://localhost:5173"
echo Udaan is starting. Keep both black server windows open.
echo If login fails, check the backend window and visit http://127.0.0.1:8000/api/health
pause
exit /b 0
:failed
echo Setup failed. Check the message above, internet connection and installed Python/Node versions.
pause
exit /b 1
