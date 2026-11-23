@echo off
setlocal

:: Remove any inspector or debugging flags so execution is never interrupted
set PWDEBUG=
set PLAYWRIGHT_INSPECT=
set PW_TEST_DEBUG=
set npm_config_pwdebug=

echo ===========================================================================
echo  ChartApps Regression Suite - PyTest Automated Execution
echo ===========================================================================
echo  Running all steps automatically without recorder or inspector tool...
echo ===========================================================================

set MARKER=%1
if "%MARKER%"=="" set MARKER=regression

call pytest -m %MARKER% -s -v

echo.
echo ===========================================================================
echo  PyTest Execution Completed.
echo ===========================================================================
pause
