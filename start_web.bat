@echo off
setlocal

set "ROOT=%~dp0"
set "HOST=127.0.0.1"
set "PORT=8000"
set "URL=http://%HOST%:%PORT%"

echo [INFO] Project root: %ROOT%
echo [INFO] Starting web service on %URL%

start "Stock Web Server" cmd /k "cd /d ""%ROOT%"" && python -m uvicorn app.main:app --host %HOST% --port %PORT%"
timeout /t 2 >nul
start "" "%URL%"

echo [DONE] Server window launched and browser opened.
endlocal
