@echo off
chcp 65001 >nul
rem AI staff watcher. Example: staff_watch.bat claude-a / claude-b / codex
cd /d %~dp0
if "%1"=="" (
  python say.py watch_usage
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat
cd ..
python studio\staff_watch.py %1
pause
