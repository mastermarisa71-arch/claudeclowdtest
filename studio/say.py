""".bat から日本語の案内を出す（Windows の黒い画面は .bat の中の日本語を読み違えることがあるので、.bat は英数字だけにする）。"""
import sys

MSG = {
    "need_setup": "先に setup.bat をダブルクリックしてください。",
    "setup_done": "準備できました。start.bat で起動します。",
    "ep09_done": "終わりました。start.bat で起動して、話数 → EP09 を開いてください。",
    "watch_usage": "使い方： staff_watch.bat claude-a （または claude-b / codex）",
    "need_token": "TSUKI_TOKEN が未設定です。例： set TSUKI_TOKEN=ここに長いランダムな文字列",
    "remote_urls": "画面 http://localhost:8765 / MCP http://localhost:8766/mcp（Authorization: Bearer TSUKI_TOKEN）",
}
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
print(MSG.get(sys.argv[1] if len(sys.argv) > 1 else "", ""))
