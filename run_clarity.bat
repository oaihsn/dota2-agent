@echo off
cd /d "%~dp0"
echo ====================================
echo   Clarity Parser Runner
echo ====================================
echo.

set DEMO_FILE=%1
if "%DEMO_FILE%"=="" set DEMO_FILE=data\raw\8749329335.dem

echo Parsing: %DEMO_FILE%
echo.

cd ..\clarity-examples-master
gradlew.bat gameeventRun --args="%cd%\..\dota2-agent\%DEMO_FILE%"
