@echo off
chcp 65001 >nul
rem 9話（仮制作）を月灯スタジオに載せる。ダブルクリックで実行。
rem 参照画像のフォルダをこのファイルの上にドラッグ＆ドロップすると、参照画像も一緒に登録する。
cd /d %~dp0
if not exist .venv\Scripts\activate.bat (
  echo 先に setup.bat をダブルクリックしてください。
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat
cd ..
if "%~1"=="" (
  python studio\seeds\EP09_仮制作.py --reset
) else (
  python studio\seeds\EP09_仮制作.py --reset --refs "%~1"
)
echo.
echo 終わりました。start.bat で起動して、話数 → EP09 を開いてください。
pause
