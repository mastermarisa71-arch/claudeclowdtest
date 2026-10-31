"""見張り番を月灯スタジオの中に入れる：会議の枠や、役のついた依頼が空いたら、その役の AI を起こす。

AI の作業は、その場で画面に流す（進み具合のページ）。書いている文章・使った道具・結果を1行ずつ取り、
終わったら使用量（トークン・時間・目安の金額）とエラーを agent_runs に残す。
AIスタッフ.json の agents.<名前>.command で、それぞれの AI（Claude・Codex）を起こす。止めるときは rules.run_agents を false に。
"""
import json
import os
import subprocess
import threading
import time

from . import config, core, db, staff

STATE: dict = {}          # agent → {"running", "since", "last", "live": [行], "run_id"}
PROMPT = ("月灯スタジオの工程を進める。あなたの名前は {agent}、役は {roles}。手順は studio/docs/AIスタッフ会議.md。"
          "1) python studio/cli.py staff-claim --agent {agent} で会議の枠を取り、ブリーフの書き方に沿って JSON を書き、"
          "staff-post（まとめ役なら staff-summarize）で出す。取れる枠がなくなるまで繰り返す。"
          "2) 次に python studio/cli.py request-claim --agent {agent} で自分の役の依頼を取り、依頼の手順どおりに作って request-done で終える。"
          "作品のルールは CLAUDE.md（Codex は AGENTS.md）。")
LIVE_MAX = 400


def waiting(conn, agent: str, roles: list[str]) -> int:
    slots = [s for s in staff.open_slots(conn) if s["role"] in roles and not (s["role"] == "見る" and s["made_by"] == agent)]
    reqs = [r for r in core.list_requests(conn, "open") if r.get("role") and r["role"] in roles]
    return len(slots) + len(reqs)


def _say(agent: str, line: str) -> None:
    live = STATE[agent].setdefault("live", [])
    live.append(f"{time.strftime('%H:%M:%S')} {line}")
    del live[:-LIVE_MAX]


def _parse(agent: str, raw: str, usage: dict) -> None:
    """Claude の stream-json（1行1イベント）を、人が読める1行にする。JSON でなければそのまま。"""
    try:
        ev = json.loads(raw)
    except ValueError:
        if raw.strip():
            _say(agent, raw.rstrip()[:500])
        return
    t = ev.get("type")
    if t == "assistant":
        for c in ev.get("message", {}).get("content", []):
            if c.get("type") == "text" and c["text"].strip():
                _say(agent, "💬 " + c["text"].strip()[:800])
            elif c.get("type") == "tool_use":
                inp = c.get("input", {})
                what = inp.get("command") or inp.get("file_path") or inp.get("pattern") or json.dumps(inp, ensure_ascii=False)[:200]
                _say(agent, f"🔧 {c.get('name')}：{str(what)[:300]}")
    elif t == "user":
        for c in ev.get("message", {}).get("content", []) if isinstance(ev.get("message", {}).get("content"), list) else []:
            if c.get("type") == "tool_result":
                txt = c.get("content")
                txt = txt if isinstance(txt, str) else json.dumps(txt, ensure_ascii=False)
                _say(agent, ("⚠ " if c.get("is_error") else "↳ ") + (txt or "").strip().replace("\n", " ")[:300])
    elif t == "result":
        u = ev.get("usage", {})
        usage.update(tokens_in=u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0),
                     tokens_out=u.get("output_tokens", 0), cost=ev.get("total_cost_usd") or 0,
                     is_error=bool(ev.get("is_error")), result=(ev.get("result") or "")[:2000])
        _say(agent, ("✖ 終わり（エラー）：" if ev.get("is_error") else "✔ 終わり：") + (ev.get("result") or "")[:400])
    elif t == "system" and ev.get("subtype") == "init":
        _say(agent, "▶ 起動しました")


def run_logged(agent: str, line: str, kind: str = "agent") -> dict:
    """コマンドを動かし、出力をその場で STATE と記録に流す。終わったら agent_runs に使用量とエラーを残す。"""
    STATE.setdefault(agent, {}).update(running=True, since=db.now(), live=[])
    usage: dict = {}
    log = config.DATA_DIR / "logs" / f"{agent}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    with db.session() as conn:
        rid = db.insert(conn, "agent_runs", {"agent": agent, "kind": kind, "started_at": db.now(), "status": "running", "command": line[:500]})
    STATE[agent]["run_id"] = rid
    err, code, t0 = "", None, time.time()
    try:
        p = subprocess.Popen(line, shell=True, cwd=config.REPO_ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True, encoding="utf-8", errors="replace")
        with open(log, "a", encoding="utf-8") as f:
            f.write(f"\n===== {db.now()} {line[:200]}\n")
            for raw in p.stdout:
                f.write(raw)
                _parse(agent, raw, usage)
                if time.time() - t0 > 45 * 60:
                    p.kill()
                    err = "45分で打ち切りました"
                    break
        code = p.wait(timeout=60)
    except Exception as e:     # 起動できない・時間切れ。画面に出す
        err = f"起こせませんでした：{e}"
    if not err and (code or usage.get("is_error")):
        tail = [l for l in STATE[agent].get("live", []) if "⚠" in l or "✖" in l or "rror" in l][-5:] or STATE[agent].get("live", [])[-5:]
        err = f"終了コード {code}：" + " ／ ".join(tail)
    status = "error" if err else "ok"
    with db.session() as conn:
        db.update(conn, "agent_runs", rid, {"ended_at": db.now(), "status": status, "error": err[:4000],
                                            "seconds": round(time.time() - t0), "tokens_in": usage.get("tokens_in", 0),
                                            "tokens_out": usage.get("tokens_out", 0), "cost_usd": usage.get("cost", 0),
                                            "result": usage.get("result", "")})
    # エラーのあとは10分休ませる（ログイン切れなどで起こし直しを繰り返さない）。うまくいっても、仕事が残ったままなら3分あける
    STATE[agent].update(running=False, last="済み" if status == "ok" else f"エラー：{err[:120]}",
                        rest_until=time.time() + (600 if err else 180))
    if err:
        _say(agent, "✖ " + err[:400])
    return {"status": status, "error": err}


def _cmd(a: dict) -> str:
    cmd = a["command"]
    if cmd.strip().startswith("claude") and "--output-format" not in cmd:
        cmd += " --output-format stream-json --verbose"       # 書いている流れをその場で見るため
    return cmd


def _run(agent: str, a: dict, roles: list[str]) -> None:
    line = _cmd(a).replace("{prompt}", PROMPT.format(agent=agent, roles="・".join(roles)))
    run_logged(agent, line)


def loop(every: int = 30) -> None:
    while True:
        try:
            st = staff.settings()
            if st.get("rules", {}).get("run_agents", True) and not os.environ.get("TSUKI_NO_AGENTS"):
                with db.session() as conn:
                    for agent, a in st.get("agents", {}).items():
                        roles = staff.roles_of(agent)
                        s = STATE.get(agent, {})
                        if not roles or not a.get("command") or s.get("running") or time.time() < s.get("rest_until", 0):
                            continue
                        if waiting(conn, agent, roles):
                            STATE.setdefault(agent, {})["running"] = True
                            threading.Thread(target=_run, args=(agent, a, roles), daemon=True).start()
        except Exception:
            pass
        time.sleep(every)


def wake(agent: str | None = None) -> None:
    """休ませている AI をすぐ起こせるようにする（ログインし直したとき）。"""
    for a, s in STATE.items():
        if agent in (None, a):
            s["rest_until"] = 0


def start() -> None:
    threading.Thread(target=loop, daemon=True).start()


def status() -> dict:
    st = staff.settings()
    return {a: {"label": v.get("label", a), "roles": staff.roles_of(a),
                **{k: x for k, x in STATE.get(a, {"running": False}).items() if k != "live"}}
            for a, v in st.get("agents", {}).items()}


def progress(conn) -> dict:
    """進み具合：いま動いている AI と、その仕事・その場の流れ、順番待ち、最近の記録、使用量。"""
    st = staff.settings()
    running = []
    for a, v in st.get("agents", {}).items():
        s = STATE.get(a, {})
        jobs = db.rows(conn.execute("SELECT id, episode, text FROM requests WHERE status='claimed' AND claimed_by=?", (a,)))
        slots = db.rows(conn.execute("""SELECT s.id, s.role, s.pass, r.id AS round, r.target, e.code AS episode FROM round_slots s
            JOIN rounds r ON r.id=s.round_id JOIN episodes e ON e.id=r.episode_id WHERE s.status='claimed' AND s.agent=?""", (a,)))
        rest = max(0, int(s.get("rest_until", 0) - time.time()))
        running.append({"agent": a, "label": v.get("label", a), "roles": staff.roles_of(a), "running": bool(s.get("running")),
                        "rest": rest,
                        "since": s.get("since"), "last": s.get("last", ""), "live": s.get("live", [])[-120:],
                        "jobs": [{"id": j["id"], "episode": j["episode"], "text": j["text"].splitlines()[0][:120]} for j in jobs],
                        "slots": slots})
    queue = [{"n": k + 1, "kind": "仕事", "id": r["id"], "episode": r["episode"], "role": r.get("role") or "だれでも",
              "text": r["text"].splitlines()[0][:140], "since": r["ts"]} for k, r in enumerate(core.list_requests(conn, "open"))]
    for s in staff.open_slots(conn):
        queue.append({"n": len(queue) + 1, "kind": "会議の枠", "id": s["id"], "episode": "", "role": s["role"],
                      "text": f"会議 #{s['round_id']} の {s['role']}（{s['pass']}周目）", "since": ""})
    runs = db.rows(conn.execute("SELECT * FROM agent_runs ORDER BY id DESC LIMIT 30"))
    today = db.now()[:10]
    usage = db.rows(conn.execute("""SELECT agent, COUNT(*) n, SUM(tokens_in) tin, SUM(tokens_out) tout, ROUND(SUM(cost_usd), 3) cost,
        SUM(seconds) secs, SUM(status='error') errors FROM agent_runs WHERE started_at>=? GROUP BY agent""", (today,)))
    return {"running": running, "queue": queue, "runs": runs, "usage_today": usage}
