"""話数の「いま」：どの工程にいるか、何を読み込んでいるか、監督の番の仕事は何か（話数を開いて最初に出す画面）。"""
import re

from . import config, core, db, direction, staff, versions

STEPS = [("script", "脚本", ""), ("sheet", "シーン整理", "G1"), ("board", "仮Vコン（9コマ）", "G2"),
         ("draft", "ドラフト 480p", "G3"), ("final", "本番 1080p", "G4"), ("edit", "音・編集", "G5")]


def _n(conn, sql: str, args=()) -> int:
    return conn.execute(sql, args).fetchone()[0] or 0


def overview(conn, code: str) -> dict:
    ep = db.episode_by_code(conn, code)
    eid = ep["id"]
    sc = core.scenes(conn, code)["scenes"]
    script = config.VAULT_DIR / "03_脚本" / "いまの版" / f"{code}_脚本_いまの版.md"
    sdate = ""
    if script.exists():
        m = re.search(r"^date:\s*(\S+)", script.read_text(encoding="utf-8")[:400], re.M)
        sdate = m.group(1) if m else ""
    doc = db.one(conn.execute("SELECT * FROM documents WHERE episode_id=? AND kind='jikonte' ORDER BY id DESC LIMIT 1", (eid,)))
    ncuts = _n(conn, "SELECT COUNT(*) FROM cuts WHERE episode_id=?", (eid,))
    secs = conn.execute("SELECT ROUND(SUM(seconds),1) FROM cuts WHERE episode_id=?", (eid,)).fetchone()[0] or 0
    boards = _n(conn, "SELECT COUNT(*) FROM boards WHERE episode_id=?", (eid,))
    board_imgs = _n(conn, "SELECT COUNT(DISTINCT cut_id) FROM takes WHERE episode_id=? AND tier='board' AND file_path!='' AND cut_id IS NOT NULL", (eid,))
    shots = _n(conn, "SELECT COUNT(*) FROM shots WHERE episode_id=?", (eid,))
    tier = lambda t: _n(conn, "SELECT COUNT(DISTINCT shot_id) FROM takes WHERE episode_id=? AND tier=? AND status='done' AND file_path!=''", (eid, t))
    drafts, finals = tier("draft"), tier("final")
    audio = _n(conn, "SELECT COUNT(*) FROM takes WHERE episode_id=? AND kind='audio' AND file_path!=''", (eid,))
    assets = db.rows(conn.execute("SELECT kind, COUNT(*) n FROM assets WHERE active=1 GROUP BY kind"))
    approved = sum(s["status"] == "approved" for s in sc)
    organized = sum(bool(s["change_before"] or s["characters"]) for s in sc)
    blocked = sum(bool(s["blocking_text"]) for s in sc)
    loaded = [
        {"name": "脚本（いまの版）", "value": f"{script.name}" + (f"（{sdate}）" if sdate else "") if script.exists() else "見つからない",
         "ok": script.exists(), "path": str(script.relative_to(config.REPO_ROOT)) if script.exists() else ""},
        {"name": "字コンテ", "value": f"{doc['version'] if doc else '―'}　{ncuts}コマ・{secs}秒（目標 {ep['target_seconds']}秒）",
         "ok": ncuts > 0, "path": doc["path"] if doc else ""},
        {"name": "シーン整理", "value": f"{len(sc)}シーン（整理済み {organized}・承認 {approved}）", "ok": organized > 0},
        {"name": "配置図", "value": f"{blocked}シーンに立ち位置", "ok": blocked > 0},
        {"name": "仮Vコン（9コマ）", "value": f"{boards}シート・絵があるコマ {board_imgs}/{ncuts}", "ok": board_imgs > 0},
        {"name": "ショット", "value": f"{shots}本（ドラフト {drafts}・本番 {finals}）", "ok": shots > 0},
        {"name": "参照素材", "value": "・".join(f"{a['kind']} {a['n']}" for a in assets) or "なし（キャラの設定資料・背景を入れる）",
         "ok": bool(assets)},
        {"name": "音", "value": f"{audio}本", "ok": audio > 0},
    ]
    state = {
        "script": "done" if script.exists() else "todo",
        "sheet": "done" if sc and approved == len([s for s in sc if s["target_seconds"]]) else "now" if sc else "todo",
        "board": "done" if ncuts and board_imgs >= ncuts else "now" if boards else "todo",
        "draft": "done" if shots and drafts >= shots else "now" if drafts else "todo",
        "final": "done" if shots and finals >= shots else "now" if finals else "todo",
        "edit": "now" if audio else "todo",
    }
    detail = {"script": sdate, "sheet": f"承認 {approved}/{len(sc)}", "board": f"絵 {board_imgs}/{ncuts}コマ",
              "draft": f"{drafts}/{shots}本", "final": f"{finals}/{shots}本", "edit": f"音 {audio}本"}
    links = {"script": "", "sheet": f"#/ep/{code}/sheet", "board": f"#/ep/{code}/vcon", "draft": f"#/ep/{code}/vcon",
             "final": f"#/ep/{code}/vcon", "edit": f"#/ep/{code}/edit"}
    steps = [{"key": k, "name": n, "gate": g, "state": state[k], "detail": detail[k], "link": links[k]} for k, n, g in STEPS]

    # 監督の番（工程の順に）
    vs = versions.list_versions(conn, code)
    choices = direction.list_choices(conn, code, "open")
    plain_choices = [c for c in choices if not any(v["choice_id"] == c["id"] for v in vs)]
    agent_q = _n(conn, "SELECT COUNT(*) FROM reviews WHERE episode_id=? AND created_by='agent' AND status='proposed'", (eid,))
    awaiting = len(core.awaiting_human(conn, code))
    todo = []
    if vs:
        scenes_v = sorted({v["scene"] for v in vs}, key=lambda s: int(re.sub(r"\D", "", s) or 0))
        todo.append({"what": f"AI の直し案を、今の版と並べて見て決める（{len(vs)}件：{'・'.join(scenes_v)}）", "link": f"#/ep/{code}/decide",
                     "n": len(vs), "kind": "decide"})
    if plain_choices:
        todo.append({"what": f"AI からの2択に答える（{len(plain_choices)}件）", "link": f"#/ep/{code}/decide", "n": len(plain_choices), "kind": "decide"})
    if sc and approved < len(sc):
        todo.append({"what": f"シーン整理を確認して「このシーンでいく」（{len(sc) - approved}シーン）", "link": f"#/ep/{code}/sheet",
                     "n": len(sc) - approved, "kind": "sheet"})
    if agent_q:
        todo.append({"what": f"AI からの質問（文章）に答える（{agent_q}件）", "link": f"#/ep/{code}/questions", "n": agent_q, "kind": "q"})
    if awaiting:
        todo.append({"what": f"AI が通した絵・動画を流し見する（{awaiting}件）", "link": f"#/ep/{code}/awaiting", "n": awaiting, "kind": "vcon"})
    working = []
    for r in staff.list_rounds(conn, code, "open"):
        done = sum(s["status"] == "done" for s in r["slots"])
        working.append({"what": f"AI スタッフ会議 #{r['id']} {r['target'] or '全体'}：{r['stage']}（{done}/{len(r['slots'])}）",
                        "link": f"#/ep/{code}/staff"})
    for q in core.list_requests(conn, "open,claimed"):
        if q["episode"] in ("", code):
            working.append({"what": f"依頼 #{q['id']}：{q['text'].splitlines()[0][:60]}"
                                    + (f"（{q['claimed_by']} が作業中）" if q["status"] == "claimed" else "（まだ誰も取っていない）"),
                            "link": "#/requests"})
    return {"episode": ep, "steps": steps, "loaded": loaded, "todo": todo, "working": working,
            "decide_count": len(vs) + len(plain_choices)}
