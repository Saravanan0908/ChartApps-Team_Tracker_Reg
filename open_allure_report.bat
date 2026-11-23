@echo off
setlocal
echo ===========================================================================
echo  Opening Allure Test Report
echo ===========================================================================
echo  Starting Allure server from reports/allure-results...
echo ===========================================================================
call allure serve reports/allure-results
pause
