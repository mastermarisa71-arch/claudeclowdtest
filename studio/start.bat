@echo off
chcp 65001 >nul
rem Tsukiakari Studio: start and open in the browser (finds a free port if 8765 is used)
cd /d %~dp0
if not exist .venv\Scripts\activate.bat (
  python say.py need_setup
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat
python launch.py
pause
