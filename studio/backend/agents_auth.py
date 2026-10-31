"""AI の接続：この PC の Claude（Claude Code）と Codex にログインしているかを見て、ツールの画面からログインを始める。"""
import json
import os
import re
import time
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


def status(tool: str, config_dir: str = "") -> dict:
    t, exe = TOOLS[tool], _exe(tool)
    if not exe:
        return {"tool": tool, "label": t["label"], "installed": False, "logged_in": False, "detail": t["install"]}
    try:
        r = subprocess.run([exe, *t["status"]], capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=20, shell=os.name == "nt", env=_env(config_dir))
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
            detail = "ChatGPT のアカウントでログイン中" if ok else out.strip()[-200:]
        return {"tool": tool, "label": t["label"], "installed": True, "logged_in": ok, "detail": detail}
    except Exception as e:
        return {"tool": tool, "label": t["label"], "installed": True, "logged_in": False, "detail": f"確かめられませんでした：{e}"}


def _env(config_dir: str = "") -> dict:
    env = dict(os.environ)
    if config_dir:
        env["CLAUDE_CONFIG_DIR"] = config_dir
    return env


def of_agent(command: str) -> tuple[str, str]:
    """AIスタッフ.json の command から、どの道具（claude / codex）と、どのログインの置き場所を使うかを読む。"""
    tool = "codex" if re.search(r"(^|&&\s*)codex(\s|$)", command.strip()) else "claude"
    m = re.search(r"CLAUDE_CONFIG_DIR=([^&\s\"]+)", command)
    d = os.path.expandvars(m.group(1).replace("%USERPROFILE%", os.path.expanduser("~"))) if m else ""
    return tool, d


_CACHE: dict = {}


def agent_status(command: str, fresh: bool = False) -> dict:
    """その AI のログイン状態（1分だけ覚えておく。調べるのに数秒かかるため）。"""
    key = of_agent(command)
    c = _CACHE.get(key)
    if c and not fresh and time.time() - c[0] < 60:
        return c[1]
    st = status(*key)
    st["config_dir"] = key[1]
    _CACHE[key] = (time.time(), st)
    return st


def login(tool: str, config_dir: str = "") -> dict:
    """ログインを始める。この PC でブラウザ（または小さな黒いウィンドウ）が開くので、そこで進める。"""
    t, exe = TOOLS[tool], _exe(tool)
    if not exe:
        return {"started": False, "message": f"{t['label']} がこの PC に見つかりません。{t['install']}"}
    flags = subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0
    if config_dir:
        os.makedirs(config_dir, exist_ok=True)
    subprocess.Popen([exe, *t["login"]], creationflags=flags, shell=False, env=_env(config_dir))
    _CACHE.clear()
    msg = "この PC でログインの画面が開きます。終わったら「確かめる」を押してください"
    if config_dir:
        msg += "。別のアカウントにするときは、ブラウザの claude.ai で先にそのアカウントに切り替えて（またはログアウトして）から「許可」を押してください"
    return {"started": True, "message": msg}


def all_status() -> list[dict]:
    return [status(k) for k in TOOLS]
