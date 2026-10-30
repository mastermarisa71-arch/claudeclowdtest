@echo off
chcp 65001 >nul
rem AI スタッフ会議の見張り番。例： staff_watch.bat codex / staff_watch.bat claude-b
rem 役と起こすコマンドは 月灯_vault\04_制作ルール\AIスタッフ.json
cd /d %~dp0
if "%1"=="" (
  echo 使い方： staff_watch.bat codex （または claude-a / claude-b）
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat
cd ..
python studio\staff_watch.py %1
pause
