@echo off
setlocal
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
