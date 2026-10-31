@echo off
chcp 65001 >nul
rem Load EP09 (trial). Drop a reference-image folder on this file to register references too.
cd /d %~dp0
if not exist .venv\Scripts\activate.bat (
  python say.py need_setup
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat
cd ..
if "%~1"=="" (
  python studio\seeds\ep09.py --reset
) else (
  python studio\seeds\ep09.py --reset --refs "%~1"
)
echo.
python studio\say.py ep09_done
pause
