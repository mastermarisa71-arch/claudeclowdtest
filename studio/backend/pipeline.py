"""シーンの工程の自動進行：AI 会議を「必要なときに開く」のではなく、工程ごとに毎回まわす。

  シーン整理を監督が承認（「このシーンでいく」）
    → 字コンテ会議（芝居・演出が話し合う）→ まとめ役が字コンテにし、そのまま 480p ドラフト（30秒程度）まで作る（依頼）
    → 映像会議（見る・演出・芝居が映像を見る）→ まとめ役が監督に結論を出す
    → 監督の判断：OK → 完成 ／ こうしたい（一言）→ まとめ役が作り直す（依頼）→ 映像会議 → 監督 …（2周目、3周目）

各 AI は自分の役の枠・依頼を取るだけ（見張り番 staff_watch が空いた枠と依頼で AI を起こす）。監督がやるのは、承認と、映像を見ての判断だけ。
"""
import json

from . import core, db, staff

STAGES = {
    "jikonte_meeting": "字コンテ会議（芝居・演出）",
    "making": "字コンテ → 480p ドラフト作り（まとめ）",
    "video_meeting": "映像会議（見る・演出・芝居）",
    "director": "監督の判断待ち",
    "remaking": "監督の指示で作り直し（まとめ）",
    "done": "OK（完成）",
}
MAKER = "まとめ"


def _flow(conn, episode_id: int, scene: str) -> dict | None:
    return db.one(conn.execute("SELECT * FROM scene_flows WHERE episode_id=? AND scene=?", (episode_id, scene)))


def _set(conn, flow_id: int, **f) -> None:
    db.update(conn, "scene_flows", flow_id, {**f, "updated_at": db.now()})


def auto_on() -> bool:
    return bool(staff.settings().get("rules", {}).get("auto", True))


def start(conn, episode: str, scene: str, by: str = "human") -> dict | None:
    """シーン整理が承認されたら、字コンテ会議を開く（もう流れているシーンは何もしない）。"""
    if not auto_on():
        return None
    ep = db.episode_by_code(conn, episode)
    f = _flow(conn, ep["id"], scene)
    if f and f["stage"] != "done":
        return f
    rid = staff.open_round(conn, episode, scene, kind="jikonte", created_by="pipeline",
                           note="承認されたシーン整理から、カットに割る")
    if f:
        _set(conn, f["id"], stage="jikonte_meeting", cycle=1, round_id=rid, request_id=None)
    else:
        db.insert(conn, "scene_flows", {"episode_id": ep["id"], "scene": scene, "stage": "jikonte_meeting", "cycle": 1,
                                        "round_id": rid, "updated_at": db.now()})
    db.log(conn, "pipeline", "flow_start", {"episode": episode, "scene": scene, "round": rid})
    return _flow(conn, ep["id"], scene)


def on_round_closed(conn, round_id: int) -> str:
    f = db.one(conn.execute("SELECT f.*, e.code AS episode FROM scene_flows f JOIN episodes e ON e.id=f.episode_id "
                            "WHERE f.round_id=?", (round_id,)))
    if not f:
        return ""
    r = db.one(conn.execute("SELECT * FROM rounds WHERE id=?", (round_id,)))
    summ = db.one(conn.execute("SELECT * FROM round_posts WHERE round_id=? AND kind='まとめ' ORDER BY id DESC LIMIT 1", (round_id,)))
    items = json.loads((summ or {}).get("items_json") or "[]")
    if r["kind"] == "jikonte":
        todo = "\n".join(f"- {i['text']}" for i in items if i.get("decision") == "do")
        req = _request(conn, f, f"[工程 {f['scene']}・字コンテ → 480p] 字コンテ会議 #{round_id} のまとめで、字コンテを作り、そのまま 480p ドラフトまで作る：\n"
                                f"1) 字コンテにする（新しく作るなら import-jikonte、今のコマを直すなら cut-edit / version-add）\n{todo}\n"
                                "2) ショット分け（1本30秒まで、shot-set）→ 3) 480p ドラフト（shot-shoot、テイクの --note に会議の番号）"
                                "→ 4) self-review → 5) request-done（終わると映像会議が自動で開く）")
        _set(conn, f["id"], stage="making", request_id=req)
        return f"{f['scene']}：字コンテ → 480p ドラフト作りの依頼 #{req} を積みました"
    if r["kind"] == "video":
        _set(conn, f["id"], stage="director")
        return f"{f['scene']}：監督の判断待ちにしました"
    return ""


def on_request_done(conn, request_id: int) -> str:
    """字コンテ・ドラフト作り（または作り直し）が終わったら、映像会議を開く。"""
    f = db.one(conn.execute("SELECT f.*, e.code AS episode FROM scene_flows f JOIN episodes e ON e.id=f.episode_id "
                            "WHERE f.request_id=? AND f.stage IN ('making','remaking')", (request_id,)))
    if not f:
        return ""
    req = db.one(conn.execute("SELECT * FROM requests WHERE id=?", (request_id,)))
    rid = staff.open_round(conn, f["episode"], f["scene"], kind="video", created_by="pipeline", cycle=f["cycle"],
                           made_by=req.get("claimed_by") or "", note=(f"監督の指示：{f['director_note']}" if f["director_note"] else ""))
    _set(conn, f["id"], stage="video_meeting", round_id=rid)
    db.log(conn, "pipeline", "flow_video", {"episode": f["episode"], "scene": f["scene"], "round": rid})
    return f"{f['scene']}：映像会議 #{rid} を開きました"


def direct(conn, episode: str, scene: str, verdict: str, note: str = "") -> dict:
    """監督の判断。ok → 完成。redo → 一言の指示で、まとめ役が作り直す（そのあと映像会議 → 監督にまた戻る）。"""
    ep = db.episode_by_code(conn, episode)
    f = _flow(conn, ep["id"], scene)
    if not f:
        raise ValueError(f"{episode} {scene} はまだ工程に入っていない")
    f["episode"] = episode
    core.add_review(conn, target_type="episode", target_id=ep["id"], verdict="良い" if verdict == "ok" else "修正",
                    tags=["意図"], comment=f"[{scene}・{f['cycle']}周目の映像] " + ("OK" if verdict == "ok" else "こうしたい") + (f"：{note}" if note else ""))
    if verdict == "ok":
        _set(conn, f["id"], stage="done", director_note=note)
        return {"stage": "done"}
    summ = db.one(conn.execute("SELECT summary FROM round_posts WHERE round_id=? AND kind='まとめ' ORDER BY id DESC LIMIT 1", (f["round_id"],)))
    req = _request(conn, f, f"[工程 {scene}・{f['cycle'] + 1}周目] 監督の指示で作り直す：{note}\n"
                            f"映像会議 #{f['round_id']} の結論：{(summ or {}).get('summary', '')}\n"
                            "監督の指示が会議の結論より上。字コンテ・ドラフトを直し（テイクの --parent と --note）、self-review → request-done"
                            "（終わると映像会議が自動で開く）")
    _set(conn, f["id"], stage="remaking", cycle=f["cycle"] + 1, request_id=req, director_note=note)
    return {"stage": "remaking", "request": req}


def _request(conn, f: dict, text: str) -> int:
    rid = core.add_request(conn, text, f["episode"])
    db.update(conn, "requests", rid, {"role": MAKER})
    return rid


def flows(conn, episode: str) -> list[dict]:
    ep = db.episode_by_code(conn, episode)
    rows = db.rows(conn.execute("SELECT * FROM scene_flows WHERE episode_id=? ORDER BY CAST(SUBSTR(scene, 2) AS INTEGER)", (ep["id"],)))
    for f in rows:
        f["stage_label"] = STAGES.get(f["stage"], f["stage"])
        r = db.one(conn.execute("SELECT * FROM rounds WHERE id=?", (f["round_id"],))) if f["round_id"] else None
        f["round"] = {"id": r["id"], "kind": r["kind"], "status": r["status"]} if r else None
        posts = db.rows(conn.execute("SELECT role, agent, kind, summary, items_json FROM round_posts WHERE round_id=? ORDER BY id",
                                     (f["round_id"],))) if r else []
        for p in posts:
            p["items"] = json.loads(p.pop("items_json") or "[]")
        f["summary"] = next((p for p in posts if p["kind"] == "まとめ"), None)
        f["views"] = [p for p in posts if p["kind"] == "所見"]
        q = db.one(conn.execute("SELECT id, status, claimed_by FROM requests WHERE id=?", (f["request_id"],))) if f["request_id"] else None
        f["request"] = q
    return rows
