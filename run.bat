@echo off
setlocal

:: Force suppression of Playwright Inspector and Debugger
set PWDEBUG=0
set PW_CODEGEN_NO_INSPECTOR=1
set PLAYWRIGHT_INSPECT=0
set PW_TEST_DEBUG=0
set npm_config_pwdebug=
set npm_package_config_pwdebug=

echo ===========================================================================
echo  ChartApps Regression Suite - Direct Automated Execution
echo ===========================================================================
echo  Running all steps automatically without recorder or inspector tool...
echo ===========================================================================

set TARGET=%1
if "%TARGET%"=="" set TARGET=all

call python tests\test_regression_existing_new_app.py %TARGET%

echo.
echo ===========================================================================
echo  Execution Completed.
echo ===========================================================================
pause
