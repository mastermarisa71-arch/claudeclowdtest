@echo off
chcp 65001 >nul
rem 月灯スタジオ：最初に1回だけ。Python 3.11 以上と ffmpeg が入っていること。
cd /d %~dp0
py -3 -m venv .venv || python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install -U pip
python -m pip install -r requirements.txt
python cli.py bible
echo.
echo 準備できました。start.bat で起動します。
pause
