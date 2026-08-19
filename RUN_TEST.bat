@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo [INFO] Creating Python virtual environment...
  py -3 -m venv .venv
  if errorlevel 1 (
    echo [ERROR] Python 3 is required.
    exit /b 1
  )
)
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
if exist "requirements.txt" python -m pip install -r requirements.txt

echo.
echo [1/4] Validate Rule.cmd
python -m src.cli validate-rule
if errorlevel 1 exit /b 1

echo.
echo [2/4] Run simulation
python -m src.cli simulate
if errorlevel 1 exit /b 1

echo.
echo [3/4] Run release gate
python -m src.cli release-gate
if errorlevel 1 (
  echo [INFO] Release gate is expected to block until real hardware/model commissioning is supplied.
)

echo.
echo [4/4] Test completed. Review the output above.
exit /b 0
