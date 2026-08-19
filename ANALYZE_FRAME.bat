@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] Run CAPTURE_CAMERA.bat first so the camera environment is created.
  pause
  exit /b 1
)
call ".venv\Scripts\activate.bat"
if "%~1"=="" (
  echo Usage: ANALYZE_FRAME.bat data\physical_trial\frame_xxx.jpg
  echo.
  echo Example:
  echo ANALYZE_FRAME.bat data\physical_trial\frame_123.jpg
  pause
  exit /b 1
)
python tools\analyze_frame.py "%~1" --json
if errorlevel 1 (
  echo.
  echo FRAME ANALYSIS FAILED.
  pause
  exit /b 1
)
echo.
echo Frame analysis complete. Metrics are diagnostic only.
pause
