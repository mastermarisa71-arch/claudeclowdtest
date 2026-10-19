@echo off
chcp 65001 >nul
rem 月灯スタジオを、クラウドの Claude や別の PC からも使えるように起動する。
rem 1) TSUKI_TOKEN に長いランダムな文字列を入れる（これが鍵。人に見せない）
rem 2) 画面（8765）と MCP（8766）を起動する
rem 3) トンネル（例：cloudflared tunnel --url http://localhost:8766）で MCP を外に出し、出てきた URL を使う
cd /d %~dp0
call .venv\Scripts\activate.bat
if "%TSUKI_TOKEN%"=="" (
  echo TSUKI_TOKEN が未設定です。例： set TSUKI_TOKEN=ここに長いランダムな文字列
  pause
  exit /b 1
)
if "%TSUKI_DATA%"=="" set TSUKI_DATA=%~dp0data
cd ..
start "月灯スタジオ 画面" cmd /k python -m uvicorn studio.backend.app:app --host 0.0.0.0 --port 8765
start "月灯スタジオ MCP" cmd /k python studio\mcp_server.py --http --host 0.0.0.0 --port 8766
echo 画面 http://localhost:8765 / MCP http://localhost:8766/mcp（Authorization: Bearer TSUKI_TOKEN）
pause
