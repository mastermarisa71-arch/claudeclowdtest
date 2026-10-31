"""AI の接続：この PC の Claude（Claude Code）と Codex にログインしているかを見て、ツールの画面からログインを始める。"""
import json
import os
import shutil
import subprocess

TOOLS = {
    "claude": {"label": "Claude（Claude Code）", "exe": ["claude", "claude.cmd"],
               "status": ["auth", "status", "--json"], "login": ["auth", "login", "--claudeai"],
               "install": "Claude のデスクトップアプリを入れて「コード」を一度開くか、https://claude.ai/download から Claude Code を入れる"},
    "codex": {"label": "Codex（ChatGPT）", "exe": ["codex", "codex.cmd"],
              "status": ["login", "status"], "login": ["login"],
              "install": "Node.js を入れてから、黒い画面で npm install -g @openai/codex"},
}


def _exe(tool: str) -> str | None:
    return next((p for n in TOOLS[tool]["exe"] if (p := shutil.which(n))), None)


def status(tool: str) -> dict:
    t, exe = TOOLS[tool], _exe(tool)
    if not exe:
        return {"tool": tool, "label": t["label"], "installed": False, "logged_in": False, "detail": t["install"]}
    try:
        r = subprocess.run([exe, *t["status"]], capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=20, shell=os.name == "nt")
        out = (r.stdout or "") + (r.stderr or "")
        if tool == "claude":
            try:
                j = json.loads(r.stdout)
                ok = bool(j.get("loggedIn"))
                detail = j.get("email") or j.get("authMethod") or ""
            except ValueError:
                ok, detail = False, out.strip()[-200:]
        else:
            ok = r.returncode == 0 and "not logged" not in out.lower()
            detail = out.strip()[-200:]
        return {"tool": tool, "label": t["label"], "installed": True, "logged_in": ok, "detail": detail}
    except Exception as e:
        return {"tool": tool, "label": t["label"], "installed": True, "logged_in": False, "detail": f"確かめられませんでした：{e}"}


def login(tool: str) -> dict:
    """ログインを始める。この PC でブラウザ（または小さな黒いウィンドウ）が開くので、そこで進める。"""
    t, exe = TOOLS[tool], _exe(tool)
    if not exe:
        return {"started": False, "message": f"{t['label']} がこの PC に見つかりません。{t['install']}"}
    flags = subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0
    subprocess.Popen([exe, *t["login"]], creationflags=flags, shell=False)
    return {"started": True, "message": "この PC でログインの画面が開きます。終わったら「確かめる」を押してください"}


def all_status() -> list[dict]:
    return [status(k) for k in TOOLS]
