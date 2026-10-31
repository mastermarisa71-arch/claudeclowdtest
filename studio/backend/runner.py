"""見張り番を月灯スタジオの中に入れる：会議の枠や、役のついた依頼が空いたら、その役の AI を起こす。

これまでの staff_watch.bat（AI ごとに黒いウィンドウ）は要らない。月灯スタジオ（start.bat）を起動していれば、
AIスタッフ.json の agents.<名前>.command で、それぞれの AI（Claude・Codex）を順に起こす。止めるときは rules.run_agents を false に。
"""
import os
import subprocess
import threading
import time
from pathlib import Path

from . import config, core, db, staff

STATE: dict = {}          # agent → {"running": bool, "since": str, "last": str}
PROMPT = ("月灯スタジオの工程を進める。あなたの名前は {agent}、役は {roles}。手順は studio/docs/AIスタッフ会議.md。"
          "1) python studio/cli.py staff-claim --agent {agent} で会議の枠を取り、ブリーフの書き方に沿って JSON を書き、"
          "staff-post（まとめ役なら staff-summarize）で出す。取れる枠がなくなるまで繰り返す。"
          "2) 次に python studio/cli.py request-claim --agent {agent} で自分の役の依頼を取り、依頼の手順どおりに作って request-done で終える。"
          "作品のルールは CLAUDE.md（Codex は AGENTS.md）。")


def waiting(conn, agent: str, roles: list[str]) -> int:
    slots = [s for s in staff.open_slots(conn) if s["role"] in roles and not (s["role"] == "見る" and s["made_by"] == agent)]
    reqs = [r for r in core.list_requests(conn, "open") if r.get("role") and r["role"] in roles]
    return len(slots) + len(reqs)


def _run(agent: str, cmd: str, roles: list[str]) -> None:
    STATE[agent] = {"running": True, "since": db.now(), "last": STATE.get(agent, {}).get("last", "")}
    log = config.DATA_DIR / "logs" / f"{agent}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    line = cmd.replace("{prompt}", PROMPT.format(agent=agent, roles="・".join(roles)))
    try:
        with open(log, "a", encoding="utf-8") as f:
            f.write(f"\n===== {db.now()} {line[:200]}\n")
            f.flush()
            subprocess.run(line, shell=True, cwd=config.REPO_ROOT, stdout=f, stderr=f, timeout=45 * 60)
        STATE[agent]["last"] = "済み"
    except Exception as e:     # 起動できない・時間切れ。画面に出す
        STATE[agent]["last"] = f"起こせませんでした：{e}"
    STATE[agent]["running"] = False


def loop(every: int = 30) -> None:
    while True:
        try:
            st = staff.settings()
            if st.get("rules", {}).get("run_agents", True) and not os.environ.get("TSUKI_NO_AGENTS"):
                with db.session() as conn:
                    for agent, a in st.get("agents", {}).items():
                        roles = staff.roles_of(agent)
                        if not roles or not a.get("command") or STATE.get(agent, {}).get("running"):
                            continue
                        if waiting(conn, agent, roles):
                            threading.Thread(target=_run, args=(agent, a["command"], roles), daemon=True).start()
        except Exception:
            pass
        time.sleep(every)


def start() -> None:
    threading.Thread(target=loop, daemon=True).start()


def status() -> dict:
    st = staff.settings()
    return {a: {"label": v.get("label", a), "roles": staff.roles_of(a), **STATE.get(a, {"running": False})}
            for a, v in st.get("agents", {}).items()}
