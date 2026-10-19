@echo off
chcp 65001 >nul
rem 月灯スタジオを起動して、ブラウザで開く（自分の PC で使うとき）
cd /d %~dp0
call .venv\Scripts\activate.bat
rem 生成物と DB の置き場所（変えたいときだけ）
if "%TSUKI_DATA%"=="" set TSUKI_DATA=%~dp0data
start "" http://localhost:8765
cd ..
python -m uvicorn studio.backend.app:app --port 8765
