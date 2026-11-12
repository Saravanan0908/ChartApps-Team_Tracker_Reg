@echo off
echo ========================================================
echo Opening Google Chrome to complete manual Google login...
echo ========================================================
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%~dp0.auth_profile" "https://chartapps.app/dashboard"
echo.
echo 1. Chrome has opened.
echo 2. Sign in with your Google Email and Password in Chrome.
echo 3. Once you reach the ChartApps dashboard, keep Chrome open!
echo 4. Run 'record_codegen.bat' to start recording your actions with Playwright Codegen.
echo ========================================================
pause

