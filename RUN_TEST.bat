@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================================
echo GPT_AI Inspection - TEST RUNNER
echo ============================================================
echo.

if not exist ".venv\Scripts\python.exe" (
  echo [INFO] Creating Python virtual environment...
  py -3 -m venv .venv
  if errorlevel 1 goto :PYTHON_ERROR
)

call ".venv\Scripts\activate.bat"
if errorlevel 1 goto :ERROR

python -m pip install --upgrade pip
if errorlevel 1 goto :ERROR
if exist "requirements.txt" (
  python -m pip install -r requirements.txt
  if errorlevel 1 goto :ERROR
)

echo.
echo [1/4] Validate Rule.cmd
python -m src.cli validate-rule
if errorlevel 1 goto :ERROR

echo.
echo [2/4] Run simulation
python -m src.cli simulate
if errorlevel 1 goto :ERROR

echo.
echo [3/4] Run release gate
python -m src.cli release-gate
if errorlevel 1 (
  echo [WARN] Release gate blocked. This is expected until real hardware/model commissioning is supplied.
)

echo.
echo [4/4] TEST COMPLETED
set "RESULT=0"
goto :DONE

:PYTHON_ERROR
echo [ERROR] Python 3 is required. Install Python 3.10+ and try again.
set "RESULT=1"
goto :DONE

:ERROR
echo [ERROR] Test runner stopped because a required step failed.
set "RESULT=1"

goto :DONE

:DONE
echo.
echo ============================================================
if "%RESULT%"=="0" (
  echo RESULT: TEST RUN COMPLETED
) else (
  echo RESULT: TEST FAILED - review the messages above
)
echo ============================================================
echo.
pause
exit /b %RESULT%
