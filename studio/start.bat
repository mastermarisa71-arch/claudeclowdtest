@echo off
chcp 65001 >nul
rem 月灯スタジオを起動して、ブラウザで開く（自分の PC で使うとき）
rem 8765 番がほかのツールに使われていたら、空いている番号を探して開く
cd /d %~dp0
if not exist .venv\Scripts\activate.bat (
  echo 先に setup.bat をダブルクリックしてください。
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat
python launch.py
pause
