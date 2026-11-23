@echo off
echo ===================================================
echo Launching Playwright CodeGen with Saved Auth Profile
echo ===================================================
call python -m playwright codegen --user-data-dir=.auth_profile --viewport-size="1920, 1080" https://chartapps.app/dashboard
pause
