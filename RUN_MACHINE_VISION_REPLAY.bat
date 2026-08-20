@echo off
setlocal
cd /d %~dp0
if "%~1"=="" (
  echo Usage: RUN_MACHINE_VISION_REPLAY.bat path\to\pcb.jpg
  echo Example: RUN_MACHINE_VISION_REPLAY.bat data\physical_trial\frame_0001.jpg
  pause
  exit /b 2
)
if not exist .venv\Scripts\python.exe (
  echo Python environment not found. Run runtest.bat first.
  pause
  exit /b 2
)
.venv\Scripts\python.exe -m src.vision.image_inspection_runner "%~1"
if errorlevel 1 (
  echo.
  echo Machine-vision replay returned NG/ERROR.
) else (
  echo.
  echo Machine-vision replay PASS.
)
pause
