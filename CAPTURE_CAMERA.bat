@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo [INFO] Creating Python virtual environment...
  py -3 -m venv .venv
  if errorlevel 1 goto :error
)
call ".venv\Scripts\activate.bat"
python -m pip install -r requirements-camera.txt
if errorlevel 1 goto :error
python tools\capture_camera.py --camera 0 --output data\physical_trial
if errorlevel 1 goto :error

echo.
echo Camera capture finished successfully.
echo Images and metadata are under data\physical_trial
pause
exit /b 0

:error
echo.
echo CAMERA TEST FAILED. Keep this window open and send the error text.
pause
exit /b 1
