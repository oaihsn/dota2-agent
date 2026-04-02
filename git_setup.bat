@echo off
cd /d "%~dp0"
git init
git add .
git commit -m "Initial commit"
echo Done!
pause
