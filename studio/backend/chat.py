"""月灯スタジオの中のチャット：監督が話しかける相手は「制作進行」の AI ひとり（どの AI に頼むかは選ばない）。

監督の PC に入っている Claude（Claude Code の `claude` コマンド）を、月灯スタジオが裏で呼び出して返事をする（契約のまま、API キーは要らない）。
返事の中に「やること」の提案（JSON）があれば、画面にボタンで出し、監督が OK するとその話数に積む：
  fix     … その話数・シーンの修正項目（未対応のレビュー）に積む（作る係が次の作業で読む）
  request … 制作進行の仕事として依頼に積む（月灯スタジオが制作進行の AI を起こして進める）
  flow    … シーンの工程（字コンテ会議 → 480p → 映像会議）を始める
"""
import json
import re
import shutil
import subprocess
import threading

from . import config, core, db, overview

LOCK = threading.Lock()
RUNNING: dict = {"busy": False, "partial": ""}

SYSTEM = """あなたは月灯スタジオの「制作進行」。『月灯りスピークイージー』の制作全体（構成管理・進行・まとめ・制作）を担い、監督のチャットに答える。
- 監督は日本語しか読めない。返事は日本語で短く、結論から。専門用語は避ける。
- このリポジトリの CLAUDE.md・vault（月灯_vault）を正として答える。必要ならファイルを読んでよい（Read / Grep）。ファイルは書き換えない。
- 監督の言葉が「直し・作業の頼みごと」なら、返事の最後に、やることの提案を JSON で1つだけつける（監督が OK すると積まれる）：
```actions
[{"type": "fix", "episode": "EP09", "scene": "S3", "text": "あかねがノートを棚に戻すのを、もっとはっきり見せる"},
 {"type": "request", "episode": "EP09", "text": "S1〜S3 の字コンテを、監督の指示どおりに直して 480p まで作る"},
 {"type": "flow", "episode": "EP09", "scene": "S2"}]
```
  fix＝その話数・シーンの修正項目に積む ／ request＝制作進行の仕事として積む（裏で AI が進める）／ flow＝シーンの工程（字コンテ会議 → 480p → 映像会議）を始める。
  ただの質問や相談なら actions はつけない。どの話数か分からないときは聞き返す。
- 芝居・演出・見る の AI には、工程の会議で自動で回る。監督に「どの AI に頼むか」を選ばせない。"""


def claude_exe() -> str | None:
    return shutil.which("claude") or shutil.which("claude.cmd")


def _state(conn) -> dict:
    row = db.one(conn.execute("SELECT value FROM settings WHERE key='chat_session'"))
    return {"session": row["value"] if row else ""}


def _save_session(conn, sid: str) -> None:
    conn.execute("INSERT INTO settings(key, value) VALUES('chat_session', ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (sid,))


def history(conn, after: int = 0) -> dict:
    rows = db.rows(conn.execute("SELECT * FROM chat_messages WHERE id>? ORDER BY id", (after,)))
    for r in rows:
        r["actions"] = json.loads(r.pop("actions_json") or "[]")
    return {"messages": rows, "busy": RUNNING["busy"], "partial": RUNNING["partial"], "ready": bool(claude_exe())}


def _context(conn, episode: str) -> str:
    """いま開いている話数の要点（制作進行がすぐ答えられるように）。"""
    eps = db.rows(conn.execute("SELECT code, title, target_seconds FROM episodes ORDER BY code"))
    out = ["月灯スタジオにある話数：" + "、".join(f"{e['code']} {e['title']}" for e in eps) or "（まだない）"]
    if episode and db.episode_by_code(conn, episode):
        o = overview.overview(conn, episode)
        out.append(f"監督がいま開いている話数：{episode}")
        out += [f"- 監督の番：{t['what']}" for t in o["todo"]]
        out += [f"- AI が作業中：{w['what']}" for w in o["working"]]
        out += [f"- シーンの工程：{f['scene']} {f['label']}（{f['cycle']}周目）" for f in o["flows"]]
    return "\n".join(out)


def send(conn, text: str, episode: str = "") -> int:
    mid = db.insert(conn, "chat_messages", {"role": "user", "text": text, "episode": episode, "created_at": db.now()})
    exe = claude_exe()
    if not exe:
        db.insert(conn, "chat_messages", {"role": "assistant", "episode": episode, "created_at": db.now(),
                                          "text": "この PC で Claude（Claude Code）が見つかりません。Claude のデスクトップアプリの「コード」を一度開くか、"
                                                  "`claude` コマンドを入れてから、月灯スタジオ（start.bat）を開き直してください。"})
        return mid
    ctx, sess = _context(conn, episode), _state(conn)["session"]
    threading.Thread(target=_run, args=(exe, text, ctx, sess, episode), daemon=True).start()
    return mid


def _run(exe: str, text: str, ctx: str, session: str, episode: str) -> None:
    with LOCK:
        RUNNING.update(busy=True, partial="")
        args = [exe, "-p", f"{ctx}\n\n監督：{text}", "--output-format", "stream-json", "--verbose",
                "--append-system-prompt", SYSTEM, "--allowedTools", "Read", "Glob", "Grep",
                "Bash(python studio/cli.py brief:*)", "Bash(python studio/cli.py flows:*)"]
        if session:
            args += ["--resume", session]
        reply, sid, err = "", session, ""
        try:
            p = subprocess.Popen(args, cwd=config.REPO_ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 text=True, encoding="utf-8", errors="replace")
            for line in p.stdout:
                try:
                    ev = json.loads(line)
                except ValueError:
                    continue
                if ev.get("type") == "assistant":
                    for c in ev.get("message", {}).get("content", []):
                        if c.get("type") == "text":
                            RUNNING["partial"] += c["text"]
                elif ev.get("type") == "result":
                    reply = ev.get("result") or RUNNING["partial"]
                    sid = ev.get("session_id") or sid
            p.wait(timeout=600)
            if p.returncode and not reply:
                err = (p.stderr.read() or "")[-500:]
        except Exception as e:      # 起動できない・時間切れなど。黙らずに画面に出す
            err = str(e)
        if not reply and re.search(r"login|log in|auth|ログイン|API key", err or "", re.I):
            reply = "制作進行の AI がログインしていません。上のメニューの「AI の接続」で、Claude の「ログインする」を押してください。"
        reply = reply or RUNNING["partial"] or f"（制作進行の AI が返事できませんでした：{err or '原因不明'}）"
        m = re.search(r"```actions\s*(\[.*?\])\s*```", reply, re.S)
        actions = []
        if m:
            try:
                actions = json.loads(m.group(1))
            except ValueError:
                actions = []
            reply = reply.replace(m.group(0), "").strip()
        with db.session() as conn:
            if sid and sid != session:
                _save_session(conn, sid)
            db.insert(conn, "chat_messages", {"role": "assistant", "text": reply, "episode": episode,
                                              "actions_json": json.dumps(actions, ensure_ascii=False), "created_at": db.now()})
        RUNNING.update(busy=False, partial="")


def act(conn, message_id: int, index: int) -> str:
    """監督が提案の「積む」を押した。"""
    m = db.one(conn.execute("SELECT * FROM chat_messages WHERE id=?", (message_id,)))
    acts = json.loads(m["actions_json"] or "[]")
    a = acts[index]
    if a.get("done"):
        return "もう積んであります"
    ep = a.get("episode") or m["episode"]
    e = db.episode_by_code(conn, ep) if ep else None
    if not e:
        return f"話数 {ep or '（未指定）'} がありません"
    if a["type"] == "fix":
        core.add_review(conn, target_type="episode", target_id=e["id"], verdict="修正", tags=["意図"],
                        comment=f"[{a.get('scene') or '全体'}・チャットから] {a['text']}")
        msg = f"{ep} {a.get('scene') or ''} の修正項目に積みました"
    elif a["type"] == "request":
        rid = core.add_request(conn, a["text"], ep)
        db.update(conn, "requests", rid, {"role": "まとめ"})
        msg = f"制作進行の仕事 #{rid} として積みました（裏で AI が進めます）"
    elif a["type"] == "flow":
        from . import pipeline
        pipeline.start(conn, ep, a["scene"])
        msg = f"{ep} {a['scene']} の工程を始めました（字コンテ会議から）"
    else:
        return "知らない種類の提案です"
    a["done"] = msg
    db.update(conn, "chat_messages", message_id, {"actions_json": json.dumps(acts, ensure_ascii=False)})
    return msg
