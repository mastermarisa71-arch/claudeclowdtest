"""Premiere Pro との共同編集。

XML を書き出して読み込み直す往復をなくすため、Premiere の中にパネル（studio/premiere/cep）を置く。
- エージェント → Premiere：編集操作（シーケンスを組む、クリップを差し替える、マーカー）をキューに積む。
  パネルが数秒ごとに取り出して ExtendScript で実行する。監督は Premiere の画面でその様子を見られる。
- 監督 → エージェント：Premiere で溜め・詰めなどを手直ししたら、パネルの「AIに渡す」でタイムラインの今の状態を送る。
  ツールはコマの尺に反映し、差分を記録する。エージェントは `pr-state` でそれを読んで続きを作る。
"""
import json
from pathlib import Path

from . import config, core, db


def enqueue(conn, episode: str, command: str, args: dict, host: str = "premiere") -> int:
    """host：premiere / aftereffects。それぞれのアプリの中のパネルが自分宛ての命令だけ取り出す。"""
    qid = db.insert(conn, "premiere_queue", {"ts": db.now(), "episode": episode, "command": command, "host": host,
                                              "args_json": json.dumps(args, ensure_ascii=False)})
    db.log(conn, "agent", "premiere_command", {"episode": episode, "command": command, "queue": qid})
    return qid


def pending(conn, host: str = "premiere") -> list[dict]:
    rows = db.rows(conn.execute("SELECT * FROM premiere_queue WHERE status='pending' AND COALESCE(host,'premiere')=? "
                                "ORDER BY id", (host,)))
    for r in rows:
        conn.execute("UPDATE premiere_queue SET status='running' WHERE id=?", (r["id"],))
        r["args"] = json.loads(r.pop("args_json"))
    return rows


def finish(conn, qid: int, ok: bool, result: dict) -> None:
    db.update(conn, "premiere_queue", qid, {"status": "done" if ok else "failed",
                                            "result_json": json.dumps(result, ensure_ascii=False), "done_at": db.now()})


def build_args(conn, code: str, draft_ok: bool = True) -> dict:
    """上映順のクリップ（映像・声・効果音・劇伴）を秒で並べた、シーケンスの組み立て指示。
    ドラフトの段階でも組めるよう、採用前のドラフトや仮Vコンも入れる（draft_ok）。"""
    clips, audio, t = [], [], 0.0
    for p in core.playlist(conn, code, selected_only=not draft_ok):
        c, secs = p["cut"], p["cut"]["seconds"] or 1.0
        name = f"{c['cut']}{c['panel']}"
        if p["take"] and (not p["shot"] or p["shot_first"]):
            length = p["shot_seconds"] if p["shot"] else secs
            clips.append({"name": p["shot"] or name, "cuts": name, "path": str((config.MEDIA_DIR / p["take"]["file_path"]).resolve()),
                          "start": round(t, 3), "duration": round(length, 3), "take": p["take"]["id"],
                          "tier": p["take"].get("tier") or "", "mute": p["take"]["kind"] == "video"})
        for a in p["audio"]:
            audio.append({"name": name, "track": core.AUDIO_ROLES.get(a.get("role") or "voice", "A1 声"),
                          "path": str((config.MEDIA_DIR / a["file_path"]).resolve()), "start": round(t, 3),
                          "take": a["id"]})
        t += secs
    return {"sequence": f"{code}_studio", "fps": config.FPS, "video": clips, "audio": audio, "total": round(t, 3)}


def receive_state(conn, code: str, state: dict, actor: str = "human") -> dict:
    """パネルから届いたタイムライン。クリップ名がコマ名（S1-02①）のものは尺をコマに反映する。
    ショット（SH03）のクリップは長さの変化だけ記録し、どのコマを詰めたかはエージェントが判断する。"""
    ep = db.episode_by_code(conn, code)
    cuts = {f"{c['cut']}{c['panel']}": c for c in db.rows(conn.execute(
        "SELECT id, cut, panel, seconds FROM cuts WHERE episode_id=?", (ep["id"],)))}
    shots = {s["code"]: s for s in db.rows(conn.execute("SELECT code, seconds FROM shots WHERE episode_id=?", (ep["id"],)))}
    diff = []
    for clip in state.get("video", []):
        name, dur = clip.get("name", ""), round(float(clip.get("end", 0)) - float(clip.get("start", 0)), 3)
        if name in cuts and abs((cuts[name]["seconds"] or 0) - dur) > 1 / config.FPS:
            diff.append({"clip": name, "before": cuts[name]["seconds"], "after": dur})
            core.update_cut(conn, cuts[name]["id"], actor, seconds=dur)
        elif name in shots and abs((shots[name]["seconds"] or 0) - dur) > 1 / config.FPS:
            diff.append({"clip": name, "before": shots[name]["seconds"], "after": dur, "note": "ショットの長さ。どのコマか要確認"})
    db.insert(conn, "premiere_states", {"ts": db.now(), "episode": code, "actor": actor,
                                        "state_json": json.dumps(state, ensure_ascii=False),
                                        "diff_json": json.dumps(diff, ensure_ascii=False)})
    db.log(conn, actor, "premiere_sync", {"episode": code, "changes": len(diff), "note": state.get("note", "")})
    note = (state.get("note") or "").strip()
    if note and actor == "human" and note != "AI が読み取り":
        core.add_review(conn, target_type="episode", target_id=ep["id"], verdict="修正", tags=["尺・テンポ"],
                        comment=f"[Premiere から] {note}" + (f"（尺の変更 {len(diff)} 件）" if diff else ""))
    return {"changes": diff}


def last_state(conn, code: str) -> dict | None:
    r = db.one(conn.execute("SELECT * FROM premiere_states WHERE episode=? ORDER BY id DESC LIMIT 1", (code,)))
    if r:
        r["state"] = json.loads(r.pop("state_json"))
        r["diff"] = json.loads(r.pop("diff_json"))
    return r


def ae_comp_args(conn, take_id: int, texts: list[dict] | None = None, zoom: dict | None = None,
                 render: bool = False) -> dict:
    """After Effects：テイク1本からコンポを作る。黒板・メモの文字（texts）、編集での小さな寄り引き（zoom）、
    書き出し（render）。書き出したものは、そのテイクの子（kind=video, tier=comp）として戻す。"""
    t = db.one(conn.execute("SELECT t.*, e.code FROM takes t JOIN episodes e ON e.id=t.episode_id WHERE t.id=?", (take_id,)))
    params = json.loads(t["params_json"] or "{}")
    out = config.MEDIA_DIR / t["code"] / f"take{take_id:05d}_comp.mov"
    return {"name": f"{t['code']}_take{take_id}", "path": str((config.MEDIA_DIR / t["file_path"]).resolve()),
            "duration": params.get("duration") or 5, "fps": config.FPS, "texts": texts or [], "zoom": zoom or {},
            "render": render, "out": str(out.resolve()), "take": take_id}


def ae_rendered(conn, take_id: int, path: str) -> int:
    """AE の書き出しをテイクとして登録する（パネルの render 結果から呼ぶ）。"""
    t = db.one(conn.execute("SELECT t.*, e.code FROM takes t JOIN episodes e ON e.id=t.episode_id WHERE t.id=?", (take_id,)))
    rel = Path(path).resolve().relative_to(config.MEDIA_DIR.resolve()).as_posix()
    nid = core.add_take(conn, episode=t["code"], cut_id=t["cut_id"], kind="video", provider="aftereffects",
                        prompt="After Effects で合成", parent_take_id=take_id, file_path=rel, agent_note="AE 合成")
    db.update(conn, "takes", nid, {"tier": "comp", "shot_id": t.get("shot_id")})
    return nid
