@echo off
setlocal

:: ============================================================================
::  DEBUG INSPECT MODE  -  Runs Regression Suite with Playwright Inspector
::  Usage:
::    run_debug_inspect.bat              -> runs all regression tests
::    run_debug_inspect.bat existing     -> runs only existing-app scenario
::    run_debug_inspect.bat new          -> runs only new-app scenario
::
::  This file is for LOCAL DEBUGGING ONLY.
::  PWDEBUG=1 will PAUSE execution at every Playwright action.
::  Do NOT use in CI/CD pipelines.
:: ============================================================================

:: Enable Playwright Inspector (pauses on each step)
set PWDEBUG=1
set PW_CODEGEN_NO_INSPECTOR=0
set PLAYWRIGHT_INSPECT=1
set PW_TEST_DEBUG=1

echo ===========================================================================
echo  ChartApps Regression Suite - INSPECTOR / DEBUG MODE
echo ===========================================================================
echo  PWDEBUG=1  -  Playwright Inspector will open and PAUSE on each action.
echo  Use the Inspector window to step through, resume, or set breakpoints.
echo ===========================================================================
echo.

set TARGET=%1
if "%TARGET%"=="" set TARGET=all

echo  Target scenario : %TARGET%
echo.

:: Run via pytest with verbose + no capture so Inspector can interact
set MARKER=regression
if "%TARGET%"=="existing" set MARKER=existing_app
if "%TARGET%"=="new"      set MARKER=new_app

echo  Pytest marker: %MARKER%
echo ===========================================================================
echo.

call pytest -m %MARKER% -s -v --no-header

echo.
echo ===========================================================================
echo  Debug session completed.
echo ===========================================================================
pause
