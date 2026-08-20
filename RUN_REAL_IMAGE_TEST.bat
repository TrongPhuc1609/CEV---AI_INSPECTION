@echo off
setlocal
cd /d %~dp0
if "%~1"=="" (
  echo Usage: RUN_REAL_IMAGE_TEST.bat ^<image_path^> [sidecar_path]
  echo Example: RUN_REAL_IMAGE_TEST.bat data\physical_trial\pcb_good.jpg tools\real_image_case.json
  pause
  exit /b 2
)
set IMAGE=%~1
set SIDECAR=%~2
if "%SIDECAR%"=="" set SIDECAR=tools\real_image_case.json
if not exist .venv\Scripts\python.exe (
  echo .venv not found. Run RUN_TEST.bat first.
  pause
  exit /b 2
)
.venv\Scripts\python.exe tools\run_image_replay.py "%IMAGE%" "%SIDECAR%"
set RC=%ERRORLEVEL%
echo.
if %RC% EQU 0 (
  echo RESULT: REAL IMAGE REPLAY PASS
) else (
  echo RESULT: REAL IMAGE REPLAY FAILED OR NG
)
pause
exit /b %RC%
