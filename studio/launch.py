"""月灯スタジオを起動して、ブラウザで開く（start.bat から呼ばれる）。

- 8765 番が別のツールに使われていたら、空いている番号を探して使う（8765〜8799）。
- すでに月灯スタジオが動いていれば、新しく起動せず、そのページを開くだけ。
- サーバーの準備ができてからブラウザを開く（早すぎて別の画面やエラーが出るのを防ぐ）。
- 使った番号は studio/data/port.txt に残す（パネルやエージェントが見る）。
"""
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get("TSUKI_DATA", ROOT / "studio" / "data"))


def is_studio(port: int) -> bool:
    """その番号で動いているのが月灯スタジオか（/api/meta が月灯スタジオの形で返るか）。"""
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/meta", timeout=1.5) as r:
            return "verdicts" in json.loads(r.read() or b"{}")
    except Exception:
        return False


def in_use(port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def main() -> None:
    first = int(os.environ.get("TSUKI_PORT", "8765"))
    for port in range(first, first + 35):
        if port == 8766:         # start_remote.bat の MCP 用に空けておく
            continue
        if is_studio(port):
            print(f"月灯スタジオはもう動いています：http://localhost:{port}")
            webbrowser.open(f"http://localhost:{port}")
            return
        if not in_use(port):
            break
        print(f"{port} 番はほかのツールが使っています。次の番号を試します")
    else:
        print("空いている番号が見つかりませんでした。TSUKI_PORT で別の番号を指定してください")
        sys.exit(1)

    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "port.txt").write_text(str(port), encoding="utf-8")
    proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "studio.backend.app:app", "--port", str(port)], cwd=ROOT)
    for _ in range(60):          # 準備ができるまで最大30秒待つ
        if proc.poll() is not None:
            print("月灯スタジオの起動に失敗しました。上に出ているエラーをエージェントに貼ってください")
            sys.exit(1)
        if is_studio(port):
            break
        time.sleep(0.5)
    url = f"http://localhost:{port}"
    print(f"\n月灯スタジオ：{url}\nこのウィンドウを閉じると止まります\n")
    webbrowser.open(url)
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()


if __name__ == "__main__":
    main()
