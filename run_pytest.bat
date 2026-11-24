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
echo  ChartApps Regression Suite - PyTest Automated Execution (Allure)
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
