@echo off
chcp 65001 >nul
rem Tsukiakari Studio: run once. Needs Python 3.10+ and ffmpeg.
cd /d %~dp0
py -3 -m venv .venv || python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install -U pip
python -m pip install -r requirements.txt
python cli.py bible
echo.
python say.py setup_done
pause
