@echo off
setlocal
cd /d "%~dp0\.."

python utils\copy_auth.py

pause
