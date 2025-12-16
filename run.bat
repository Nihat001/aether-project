@echo off
REM Project Aether - Windows Startup Script

REM Set Python path
set PYTHONPATH=src

REM Start the server
echo Starting Project Aether AQMS server...
echo Listening on http://localhost:8000
echo.

python3.11 -m uvicorn aether.main:app ^
  --host 0.0.0.0 ^
  --port 8000 ^
  --reload

pause
