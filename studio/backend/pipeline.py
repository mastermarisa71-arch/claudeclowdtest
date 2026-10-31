"""シーンの工程の自動進行：AI 会議を「必要なときに開く」のではなく、工程ごとに毎回まわす。

  シーン整理を監督が承認（「このシーンでいく」）
    → 演出が仮の字コンテを書く（生成しない）→ 監督が仮字コンテを見る（OK ／ 直して）
    → 話数の全シーンの仮字コンテが OK になったら、字コンテ会議（芝居・演出）を全シーンで開く（他シーンとの整合を見るため）
      （監督が「このシーンだけ先に進める」を押せば、待たずに開く）
    → まとめ役が字コンテに仕上げる → まとめ役がショット分け・プロンプトを仕上げ、素材がそろっているかを確かめる（生成しない）
    → 監督の生成チェック：足りない素材を見て「生成する」／「直して」
    → 480p ドラフト → 映像会議（見る・演出・芝居）→ 監督の判断：OK → 完成 ／ こうしたい → 作り直し → 映像会議 …
  監督が「生成する」を押すまで、お金のかかる生成は回さない。

各 AI は自分の役の枠・依頼を取るだけ（見張り番 staff_watch が空いた枠と依頼で AI を起こす）。監督がやるのは、承認と、映像を見ての判断だけ。
"""
import json

from . import core, db, staff

STAGES = {
    "rough": "仮字コンテ作り（演出）",
    "rough_check": "監督の仮字コンテチェック待ち",
    "rough_ok": "仮字コンテ OK（ほかのシーン待ち）",
    "jikonte_meeting": "字コンテ会議（芝居・演出）",
    "jikonte": "字コンテ作り（制作進行）",
    "prep": "プロンプト・素材の確認（制作進行）",
    "gate": "監督の生成チェック待ち",
    "making": "480p ドラフト作り（制作進行）",
    "video_meeting": "映像会議（見る・演出・芝居）",
    "director": "監督の判断待ち",
    "remaking": "監督の指示で作り直し（まとめ）",
    "done": "OK（完成）",
}
MAKER = "まとめ"
ROUGH = "演出"
DIRECTOR_STAGES = ("rough_check", "gate", "director")    # 監督の番


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
    if not f:
        db.insert(conn, "scene_flows", {"episode_id": ep["id"], "scene": scene, "stage": "rough", "cycle": 1, "updated_at": db.now()})
        f = _flow(conn, ep["id"], scene)
    f["episode"] = episode
    _rough(conn, f)
    db.log(conn, "pipeline", "flow_start", {"episode": episode, "scene": scene})
    return _flow(conn, ep["id"], scene)


def _rough(conn, f: dict, note: str = "") -> int:
    req = _request(conn, f, f"[工程 {f['scene']}・仮字コンテ] 演出として、承認されたシーン整理 {f['episode']} {f['scene']} から仮の字コンテを書く（生成はしない）。\n"
                            "カット割り・カメラ位置とカメラワーク・秒・画面の中身・台詞（新しく作るなら import-jikonte、今のコマを直すなら cut-edit）。"
                            "前後のシーンの字コンテ・シーン整理とつながるか（他シーンとの整合）を見る。要る背景・小物は art-plan で挙げる。"
                            + (f"\n監督の直し：{note}" if note else "") + "\nself-review → request-done（結果に、カット数・秒・気になる所を書く）",
                   role=ROUGH)
    _set(conn, f["id"], stage="rough", request_id=req, round_id=None, director_note=note or "")
    return req


def _open_meeting(conn, f: dict) -> int:
    rid = staff.open_round(conn, f["episode"], f["scene"], kind="jikonte", created_by="pipeline",
                           note="監督が OK した仮字コンテを元に、芝居と演出で字コンテを詰める（ほかのシーンとの整合も）")
    _set(conn, f["id"], stage="jikonte_meeting", round_id=rid, request_id=None)
    return rid


def upgrade_old(conn) -> list[str]:
    """前の流れで積んだ「字コンテ → 480p」の依頼（まだ終わっていないもの）を取り消し、字コンテだけの依頼に積み直す。
    監督が生成を決める前に 480p が回らないように。"""
    out = []
    for f in db.rows(conn.execute("""SELECT f.*, r.text, r.status AS rstatus FROM scene_flows f JOIN requests r ON r.id=f.request_id
            WHERE f.stage='making' AND r.status IN ('open','claimed') AND r.text LIKE '%字コンテ → 480p%'""")):
        db.update(conn, "requests", f["request_id"], {"status": "cancelled", "result": "工程の組み直しで、字コンテだけの依頼に積み直した"})
        if f["round_id"]:
            out.append(on_round_closed(conn, f["round_id"]))
    return out


def check(conn, episode: str, scene: str, action: str, note: str = "") -> dict:
    """監督のチェック。
    rough_check：ok（仮字コンテ OK）／ redo（直して）／ now（ほかのシーンを待たずに字コンテ会議へ）
    gate：go（生成する）／ redo（プロンプト・素材を直して）"""
    ep = db.episode_by_code(conn, episode)
    f = _flow(conn, ep["id"], scene)
    if not f:
        raise ValueError(f"{episode} {scene} はまだ工程に入っていない")
    f["episode"] = episode
    if note:
        core.add_review(conn, target_type="episode", target_id=ep["id"], verdict="修正" if action == "redo" else "良い",
                        tags=["意図"], comment=f"[{scene}・{STAGES.get(f['stage'], f['stage'])}] {note}")
    if f["stage"] in ("rough_check", "rough_ok"):
        if action == "redo":
            return {"stage": "rough", "request": _rough(conn, f, note)}
        if action == "now":
            return {"stage": "jikonte_meeting", "round": _open_meeting(conn, f)}
        _set(conn, f["id"], stage="rough_ok", director_note=note)
        opened = _all_rough_ok(conn, episode)
        return {"stage": "jikonte_meeting" if scene in opened else "rough_ok", "opened": opened}
    if f["stage"] == "gate":
        if action == "go":
            req = _request(conn, f, f"[工程 {scene}・480p] 監督が生成を OK した。仕上げたショットとプロンプトで 480p ドラフトを作る"
                                    "（shot-shoot、テイクの --note に会議の番号）" + (f"。監督のひとこと：{note}" if note else "")
                                    + " → self-review → request-done（終わると映像会議が自動で開く）")
            _set(conn, f["id"], stage="making", request_id=req, director_note=note)
            return {"stage": "making", "request": req}
        return {"stage": "prep", "request": _prep(conn, f, note)}
    raise ValueError(f"{scene} はいま監督のチェックの段ではありません（{STAGES.get(f['stage'], f['stage'])}）")


def _all_rough_ok(conn, episode: str) -> list[str]:
    """話数の全シーンが承認済みで、仮字コンテが全部 OK なら、字コンテ会議を全部のシーンで開く。"""
    ep = db.episode_by_code(conn, episode)
    scenes = db.rows(conn.execute("SELECT code, status FROM scenes WHERE episode_id=?", (ep["id"],)))
    fl = {x["scene"]: x for x in db.rows(conn.execute("SELECT * FROM scene_flows WHERE episode_id=?", (ep["id"],)))}
    if not scenes or any(s["code"] not in fl or fl[s["code"]]["stage"] not in ("rough_ok", "jikonte_meeting", "jikonte", "prep", "gate",
                                                                               "making", "video_meeting", "director", "remaking", "done")
                         for s in scenes):
        return []
    opened = []
    for code, x in fl.items():
        if x["stage"] == "rough_ok":
            x["episode"] = episode
            _open_meeting(conn, x)
            opened.append(code)
    return opened


def _prep(conn, f: dict, note: str = "") -> int:
    req = _request(conn, f, f"[工程 {f['scene']}・プロンプトと素材の確認] 字コンテから、ショット分け（shot-set、1本30秒まで）とプロンプト（shot-brief）を仕上げる。生成はしない。\n"
                            "art-plan で要る背景・小物・キャラ資料を並べ、素材庫（art / library）にあるかを確かめる。まだの素材は勝手に代用しない。"
                            + (f"\n監督の直し：{note}" if note else "")
                            + "\nrequest-done の結果に「そろっている素材」「足りない素材（何を・どのコマで）」「ショット数と秒・480p の見込み金額」を箇条書きで書く（監督がそれを見て生成を決める）")
    _set(conn, f["id"], stage="prep", request_id=req, director_note=note or "")
    return req


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
        req = _request(conn, f, f"[工程 {f['scene']}・字コンテ] 字コンテ会議 #{round_id} のまとめで、仮字コンテを字コンテに仕上げる（生成はしない）：\n"
                                f"今のコマを直す（cut-edit / version-add）\n{todo}\n"
                                "→ self-review → request-done（終わるとプロンプト・素材の確認に進む）")
        _set(conn, f["id"], stage="jikonte", request_id=req)
        return f"{f['scene']}：字コンテ作りの依頼 #{req} を積みました"
    if r["kind"] == "video":
        _set(conn, f["id"], stage="director")
        return f"{f['scene']}：監督の判断待ちにしました"
    return ""


def on_request_done(conn, request_id: int) -> str:
    """字コンテ・ドラフト作り（または作り直し）が終わったら、映像会議を開く。"""
    f = db.one(conn.execute("SELECT f.*, e.code AS episode FROM scene_flows f JOIN episodes e ON e.id=f.episode_id "
                            "WHERE f.request_id=?", (request_id,)))
    if not f:
        return ""
    if f["stage"] == "rough":
        _set(conn, f["id"], stage="rough_check")
        return f"{f['scene']}：仮字コンテができました。監督のチェック待ちにしました"
    if f["stage"] == "jikonte":
        return f"{f['scene']}：プロンプト・素材の確認の依頼 #{_prep(conn, f)} を積みました"
    if f["stage"] == "prep":
        _set(conn, f["id"], stage="gate")
        return f"{f['scene']}：プロンプトと素材の確認ができました。監督の生成チェック待ちにしました"
    if f["stage"] not in ("making", "remaking"):
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


def _request(conn, f: dict, text: str, role: str = MAKER) -> int:
    rid = core.add_request(conn, text, f["episode"])
    db.update(conn, "requests", rid, {"role": role})
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
        q = db.one(conn.execute("SELECT id, status, claimed_by, result FROM requests WHERE id=?", (f["request_id"],))) if f["request_id"] else None
        f["request"] = q
    return rows
