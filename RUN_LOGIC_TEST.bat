@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] .venv not found. Run RUN_TEST.bat first.
  echo.
  pause
  exit /b 1
)
call ".venv\Scripts\activate.bat"

echo ============================================================
echo PCB LOGIC TEST - REAL IMAGE EVIDENCE / NO AI / NO PLC
echo ============================================================
echo.
python tools\run_logic_test.py
set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" (
  echo RESULT: LOGIC TEST PASS
) else (
  echo RESULT: LOGIC TEST FAIL
)
echo.
pause
exit /b %RC%
