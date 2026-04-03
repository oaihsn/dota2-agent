@echo off
cd /d "%~dp0"
echo.
echo ====================================
echo   Clarity Parser Setup
echo ====================================
echo.

REM Check if .NET is installed
dotnet --version >nul 2>&1
if errorlevel 1 (
    echo .NET SDK not found!
    echo Please install from: https://dotnet.microsoft.com/download
    echo.
    echo Run this script again after installation.
    pause
    exit /b 1
)

echo .NET SDK found:
dotnet --version
echo.

REM Check if Maven is installed
mvn --version >nul 2>&1
if errorlevel 1 (
    echo WARNING: Maven not found. Installing clarity from pre-built JAR...
    echo.
    echo Please download clarity.jar from:
    echo   https://github.com/skadistats/clarity/releases
    echo.
    echo Or use OpenDota API instead.
    pause
    exit /b 1
)

echo Maven found!
echo.
echo Building Clarity from source...

git clone https://github.com/skadistats/clarity.git clarity-src
cd clarity-src
cd examples
mvn package

if exist "target\clarity-examples-*.jar" (
    copy "target\clarity-examples-*.jar" "..\..\lib\clarity.jar"
    echo.
    echo Clarity built and copied to lib\clarity.jar!
    echo.
    echo Usage:
    echo   java -jar lib\clarity.jar data\raw\8749329335.dem
) else (
    echo Build failed. Try downloading from GitHub releases.
)

cd ..\..
pause
