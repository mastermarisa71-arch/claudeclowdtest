@echo off
chcp 65001 >nul
rem Start for cloud Claude / other PCs. 1) set TSUKI_TOKEN  2) UI 8765 + MCP 8766  3) tunnel 8766 (cloudflared)
cd /d %~dp0
call .venv\Scripts\activate.bat
if "%TSUKI_TOKEN%"=="" (
  python say.py need_token
  pause
  exit /b 1
)
if "%TSUKI_DATA%"=="" set TSUKI_DATA=%~dp0data
cd ..
start "Tsukiakari UI" cmd /k python -m uvicorn studio.backend.app:app --host 0.0.0.0 --port 8765
start "Tsukiakari MCP" cmd /k python studio\mcp_server.py --http --host 0.0.0.0 --port 8766
python studio\say.py remote_urls
pause
