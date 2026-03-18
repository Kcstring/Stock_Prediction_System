@echo off
setlocal

set "PORT=8000"
set "FOUND=0"

echo [INFO] Stopping web service on port %PORT% ...

for /f "tokens=5" %%P in ('netstat -ano ^| findstr /R /C:":%PORT% .*LISTENING"') do (
  set "FOUND=1"
  echo [INFO] Killing PID %%P
  taskkill /PID %%P /F >nul 2>&1
)

if "%FOUND%"=="0" (
  echo [INFO] No listening process found on port %PORT%.
) else (
  echo [DONE] Web service stopped.
)

endlocal
