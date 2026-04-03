@echo off
cd /d "%~dp0"
echo.
echo ====================================
echo   Dota 2 GSI Server
echo ====================================
echo.
echo Server starting on http://localhost:1337
echo.
echo After starting:
echo 1. Open Dota 2
echo 2. Settings -^> Game -^> Enable Developer Console = Yes
echo 3. Open console (~) and type: dota_dev connect localhost
echo.
echo Press Ctrl+C to stop the server
echo.
python src\gsi_server.py
pause
