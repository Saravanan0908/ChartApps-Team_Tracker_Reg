@echo off
setlocal

:: ============================================================================
::  DEBUG / CODEGEN MODE  -  Opens Playwright Recorder + Real Chrome
::  Usage:
::    debug_codegen.bat              -> records on https://chartapps.app/dashboard
::    debug_codegen.bat <URL>        -> records on the given URL
::
::  This file is for LOCAL DEVELOPMENT ONLY.
::  Do NOT use in CI/CD pipelines.
:: ============================================================================

:: Enable Playwright Debugger / Inspector
set PWDEBUG=1
set PW_CODEGEN_NO_INSPECTOR=0
set PLAYWRIGHT_INSPECT=1
set PW_TEST_DEBUG=1

:: Default URL (dashboard), override with first argument
set TARGET_URL=%1
if "%TARGET_URL%"=="" set TARGET_URL=https://chartapps.app/dashboard

echo ===========================================================================
echo  ChartApps - Playwright Codegen / Recorder (DEBUG MODE)
echo ===========================================================================
echo  Target URL : %TARGET_URL%
echo  Auth File  : .auth_profile\storage_state.json
echo  Browser    : Google Chrome (channel=chrome)
echo ===========================================================================
echo  Playwright Inspector + Recorder will open in a separate window.
echo  Interact with the browser to generate locator code automatically.
echo ===========================================================================
echo.

:: Launch Playwright Codegen with real Chrome and pre-loaded session
python -m playwright codegen ^
  --channel chrome ^
  --load-storage .auth_profile\storage_state.json ^
  %TARGET_URL%

echo.
echo ===========================================================================
echo  Codegen session ended.
echo ===========================================================================
pause
