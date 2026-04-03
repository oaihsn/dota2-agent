@echo off
echo ====================================
echo   Clarity Parser Downloader
echo ====================================
echo.
echo Trying to download clarity JAR...
echo.

REM Try different download methods
echo Method 1: GitHub Release...
powershell -Command "Invoke-WebRequest -Uri 'https://github.com/skadistats/clarity/releases/download/clarity-2.2.0/clarity-2.2.0-jar-with-dependencies.jar' -OutFile 'lib\clarity.jar'" 

if exist "lib\clarity.jar" (
    echo SUCCESS: clarity.jar downloaded!
    java -jar lib\clarity.jar --version
) else (
    echo Method 1 failed, trying Maven...
    powershell -Command "Invoke-WebRequest -Uri 'https://repo1.maven.org/maven2/com/skadistats/clarity/2.2.0/clarity-2.2.0-jar-with-dependencies.jar' -OutFile 'lib\clarity.jar'"
)

if exist "lib\clarity.jar" (
    echo SUCCESS: clarity.jar downloaded!
) else (
    echo.
    echo ====================================
    echo   MANUAL INSTRUCTIONS
    echo ====================================
    echo.
    echo 1. Open browser and go to:
    echo    https://github.com/skadistats/clarity/releases
    echo.
    echo 2. Download: clarity-2.2.0-jar-with-dependencies.jar
    echo.
    echo 3. Save it to: lib\clarity.jar
    echo.
    echo 4. Run: java -jar lib\clarity.jar data\raw\*.dem
    echo.
    pause
)
