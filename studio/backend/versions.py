"""案（バージョン）：AI が「こう直したらどうか」を、文章ではなく“並べ直した版”として作る。監督は今の版と並べて再生して決める。

案はコマの並び（entries）で持つ。生成の前でも、仮Vコンの絵（なければ字コンテの文字）とカメラの動きで再生できる。
  {"cut": "S1-05③", "seconds": 2.0, "move": "track_in", "camerawork": "トラックアップ"}   … 今のコマを使う（変えるところだけ書く）
  {"new": "黒板（前の日のまま）", "seconds": 0.8, "dialogue": "", "move": ""}             … 新しいコマ
  {"cut": "S1-07②", "take": 52}                                                          … 生成し直した動画（テイク）を使う
並びに書かなかった今のコマは「削る」。今の並びは version-base で出せる（それを直して出す）。
"""
import json
import re

from . import core, db

MOVES = {"track_in": "トラックアップ", "track_out": "トラックバック", "pan_left": "左へパン", "pan_right": "右へパン",
         "tilt_up": "上へティルト", "tilt_down": "下へティルト", "": ""}


def guess_move(camerawork: str) -> str:
    t = camerawork or ""
    if re.search(r"トラックアップ|寄る|ズームイン|T\.?U", t):
        return "track_in"
    if re.search(r"トラックバック|引く|ズームアウト|T\.?B", t):
        return "track_out"
    if re.search(r"左.{0,3}パン|パン.{0,3}左", t):
        return "pan_left"
    if re.search(r"パン|フォロー", t):
        return "pan_right"
    if re.search(r"ティルト.{0,3}上|上.{0,3}ティルト", t):
        return "tilt_up"
    if "ティルト" in t:
        return "tilt_down"
    return ""


def _code(c: dict) -> str:
    return f"{c['cut']}{(c['panel'] or '').strip('―')}"


def base_entries(conn, episode: str, scene: str) -> list[dict]:
    ep = db.episode_by_code(conn, episode)
    rows = db.rows(conn.execute("SELECT * FROM cuts WHERE episode_id=? AND scene=? ORDER BY seq", (ep["id"], scene)))
    return [{"cut": _code(c), "seconds": c["seconds"]} for c in rows]


def segments(conn, episode: str, scene: str, entries: list[dict] | None) -> list[dict]:
    """再生用のコマ列。entries が None なら今の版。"""
    plist = {p["cut"]["id"]: p for p in core.playlist(conn, episode)}
    ep = db.episode_by_code(conn, episode)
    cuts = db.rows(conn.execute("SELECT * FROM cuts WHERE episode_id=? AND scene=? ORDER BY seq", (ep["id"], scene)))
    by_code = {_code(c): c for c in cuts}
    base = [{"cut": _code(c)} for c in cuts]
    out = []
    for e in entries if entries is not None else base:
        if e.get("new"):
            out.append({"code": "追加", "cut_id": None, "seconds": float(e.get("seconds") or 1), "picture": e["new"],
                        "dialogue": e.get("dialogue", ""), "camerawork": e.get("camerawork", ""),
                        "move": e.get("move") or guess_move(e.get("camerawork", "")), "take": _take(conn, e.get("take")),
                        "offset": 0, "status": "new"})
            continue
        c = by_code.get(e.get("cut", ""))
        if not c:
            continue
        p = plist.get(c["id"], {})
        cw = e.get("camerawork", c["camerawork"] or "")
        seg = {"code": _code(c), "cut_id": c["id"], "seconds": float(e.get("seconds", c["seconds"]) or 0),
               "picture": e.get("picture", c["picture"] or ""), "dialogue": e.get("dialogue", c["dialogue"] or ""),
               "camerawork": cw, "move": e.get("move", guess_move(cw)),
               "take": _take(conn, e.get("take")) or p.get("take"), "offset": 0 if e.get("take") else p.get("offset", 0)}
        changed = [k for k in ("seconds", "picture", "dialogue", "camerawork", "move", "take") if k in e
                   and str(e[k]) != str({"seconds": c["seconds"], "picture": c["picture"], "dialogue": c["dialogue"],
                                         "camerawork": c["camerawork"], "move": guess_move(c["camerawork"] or ""),
                                         "take": None}.get(k))]
        seg["status"] = "changed" if changed else "same"
        seg["changed"] = changed
        out.append(seg)
    return out


def _take(conn, take_id):
    if not take_id:
        return None
    return db.one(conn.execute("SELECT id, kind, file_path, tier, status FROM takes WHERE id=?", (int(take_id),)))


def add(conn, episode: str, scene: str, title: str, entries: list[dict], note: str = "", round_id: int | None = None,
        by_role: str = "", made_by: str = "agent", reasons: list[dict] | None = None, choice_id: int | None = None,
        option: str = "") -> int:
    ep = db.get_or_create_episode(conn, episode)
    vid = db.insert(conn, "versions", {
        "episode_id": ep["id"], "scene": scene, "title": title, "note": note, "round_id": round_id, "by_role": by_role,
        "made_by": made_by, "entries_json": json.dumps(entries, ensure_ascii=False),
        "reasons_json": json.dumps(reasons or [], ensure_ascii=False), "choice_id": choice_id, "option": option,
        "status": "open", "created_at": db.now()})
    db.log(conn, made_by, "add_version", {"version": vid, "episode": episode, "scene": scene})
    return vid


def _row(conn, vid: int) -> dict:
    v = db.one(conn.execute("SELECT v.*, e.code AS episode FROM versions v JOIN episodes e ON e.id=v.episode_id WHERE v.id=?", (vid,)))
    if not v:
        raise ValueError(f"案 #{vid} がない")
    v["entries"] = json.loads(v.pop("entries_json") or "[]")
    v["reasons"] = json.loads(v.pop("reasons_json") or "[]")
    return v


def compare(conn, vid: int) -> dict:
    v = _row(conn, vid)
    base = segments(conn, v["episode"], v["scene"], None)
    alt = segments(conn, v["episode"], v["scene"], v["entries"])
    kept = {s["code"] for s in alt if s["cut_id"]}
    for s in base:
        s["status"] = "same" if s["code"] in kept else "dropped"
        if s["code"] in kept and next((a for a in alt if a["code"] == s["code"]), {}).get("status") == "changed":
            s["status"] = "changed"
    return {"version": v, "base": base, "alt": alt, "diff": diff_text(base, alt),
            "base_seconds": round(sum(s["seconds"] for s in base), 1), "alt_seconds": round(sum(s["seconds"] for s in alt), 1)}


def diff_text(base: list[dict], alt: list[dict]) -> list[str]:
    out = [f"削る：{s['code']}（{s['picture'][:16]}）" for s in base if s["status"] == "dropped"]
    bmap = {s["code"]: s for s in base}
    for s in alt:
        if s["status"] == "new":
            out.append(f"足す：{s['picture'][:20]}（{s['seconds']}秒）")
        elif s["status"] == "changed":
            b = bmap.get(s["code"], {})
            parts = []
            if "seconds" in s["changed"]:
                parts.append(f"{b.get('seconds')}→{s['seconds']}秒")
            if "move" in s["changed"] and s["move"]:
                parts.append(MOVES.get(s["move"], s["move"]))
            if "camerawork" in s["changed"] and "move" not in s["changed"]:
                parts.append(s["camerawork"])
            if "picture" in s["changed"]:
                parts.append(f"画面「{s['picture'][:18]}」")
            if "dialogue" in s["changed"]:
                parts.append("台詞")
            if "take" in s["changed"]:
                parts.append("作り直した動画")
            out.append(f"変える：{s['code']} " + "・".join(parts))
    return out


def list_versions(conn, episode: str, status: str = "open") -> list[dict]:
    st = status.split(",")
    rows = db.rows(conn.execute(
        f"SELECT v.id FROM versions v JOIN episodes e ON e.id=v.episode_id WHERE e.code=? AND v.status IN ({','.join('?' * len(st))}) "
        "ORDER BY v.scene, v.id", [episode, *st]))
    return [_row(conn, r["id"]) for r in rows]


def decide(conn, vid: int, verdict: str, note: str = "") -> dict:
    """監督の判断。adopt＝この案にする（作り直しの依頼になる）／keep＝今のまま／other＝ちがう（一言）。"""
    c = compare(conn, vid)
    v = c["version"]
    label = {"adopt": "案にする", "keep": "今のまま", "other": "ちがう"}[verdict]
    db.update(conn, "versions", vid, {"status": {"adopt": "adopted", "keep": "kept", "other": "other"}[verdict],
                                      "decision_note": note, "decided_at": db.now()})
    ep = db.episode_by_code(conn, v["episode"])
    rid = core.add_review(conn, target_type="episode", target_id=ep["id"], verdict="良い" if verdict == "adopt" else "修正",
                          tags=["意図"], comment=f"[案 #{vid} {v['scene']}「{v['title']}」] {label}" + (f"：{note}" if note else ""))
    req = None
    if verdict == "adopt":
        req = core.add_request(conn, f"[案 #{vid} を監督が採用] {v['episode']} {v['scene']}「{v['title']}」を字コンテに反映する"
                                     f"（version-show {vid} で並びを見る）：\n" + "\n".join(f"- {d}" for d in c["diff"])
                                     + (f"\n監督のひとこと：{note}" if note else ""), v["episode"])
    # 2択の選択肢になっている案なら、2択にも答える（選んだものを覚える）
    if v.get("choice_id") and verdict == "adopt":
        from . import direction
        ch = db.one(conn.execute("SELECT status FROM choices WHERE id=?", (v["choice_id"],)))
        if ch and ch["status"] == "open":
            direction.answer(conn, v["choice_id"], v["option"], note)
            conn.execute("UPDATE versions SET status='kept' WHERE choice_id=? AND id!=? AND status='open'", (v["choice_id"], vid))
    return {"review": rid, "request": req}
