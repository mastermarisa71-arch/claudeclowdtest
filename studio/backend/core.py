"""画面（app.py）とエージェント用 CLI（cli.py）が共通で使う操作。"""
import json
import shutil
import urllib.request
from pathlib import Path

from . import config, db
from .exporters import fcpxml
from .providers.base import GenerationRequest
from .providers.services import REGISTRY

REVIEW_TAGS = ["意図", "構図", "配置・左右", "芝居", "表情", "キャラ崩れ", "小物", "光・色",
               "背景", "カメラワーク", "尺・テンポ", "台詞・声", "音", "つなぎ"]
VERDICTS = ["採用", "良い", "保留", "修正", "却下"]


# ---- 話数・コマ ----

def episodes(conn) -> list[dict]:
    return db.rows(conn.execute("""
        SELECT e.*,
          (SELECT COUNT(*) FROM cuts c WHERE c.episode_id=e.id) AS n_cuts,
          (SELECT ROUND(COALESCE(SUM(seconds),0),1) FROM cuts c WHERE c.episode_id=e.id) AS seconds,
          (SELECT COUNT(*) FROM takes t WHERE t.episode_id=e.id) AS n_takes,
          (SELECT COUNT(*) FROM cuts c WHERE c.episode_id=e.id
             AND EXISTS (SELECT 1 FROM takes t WHERE t.cut_id=c.id AND t.selected=1)) AS n_selected,
          (SELECT COUNT(*) FROM reviews r WHERE r.episode_id=e.id AND r.status IN ('open','working')) AS n_open,
          (SELECT COUNT(*) FROM reviews r WHERE r.episode_id=e.id AND r.status='proposed') AS n_proposed
        FROM episodes e ORDER BY e.code"""))


def episode_cuts(conn, code: str) -> dict:
    ep = db.episode_by_code(conn, code)
    if not ep:
        raise KeyError(code)
    cuts = db.rows(conn.execute("SELECT * FROM cuts WHERE episode_id=? ORDER BY seq", (ep["id"],)))
    takes = db.rows(conn.execute("SELECT * FROM takes WHERE episode_id=? ORDER BY id", (ep["id"],)))
    open_counts = {r["target_id"]: r["n"] for r in db.rows(conn.execute(
        "SELECT target_id, COUNT(*) n FROM reviews WHERE target_type='take' AND status IN ('open','working') "
        "GROUP BY target_id"))}
    by_cut: dict[int, list] = {}
    for t in takes:
        t["open_reviews"] = open_counts.get(t["id"], 0)
        by_cut.setdefault(t["cut_id"], []).append(t)
    for c in cuts:
        c.pop("raw_json", None)
        c["takes"] = by_cut.get(c["id"], [])
    return {"episode": ep, "cuts": cuts, "unassigned_takes": by_cut.get(None, [])}


def cut_detail(conn, cut_id: int) -> dict:
    cut = db.one(conn.execute("SELECT * FROM cuts WHERE id=?", (cut_id,)))
    if not cut:
        raise KeyError(cut_id)
    takes = db.rows(conn.execute("SELECT * FROM takes WHERE cut_id=? ORDER BY id DESC", (cut_id,)))
    ids = [t["id"] for t in takes]
    reviews = db.rows(conn.execute(
        f"SELECT * FROM reviews WHERE (target_type='take' AND target_id IN ({','.join('?' * len(ids)) or 'NULL'}))"
        " OR (target_type='cut' AND target_id=?) ORDER BY id", (*ids, cut_id)))
    comps = db.rows(conn.execute("SELECT * FROM comparisons WHERE cut_id=? ORDER BY id DESC", (cut_id,)))
    return {"cut": cut, "takes": takes, "reviews": reviews, "comparisons": comps}


# ---- テイク ----

def add_take(conn, *, episode: str, cut_id: int | None, kind: str, provider: str = "manual",
             model: str = "", prompt: str = "", refs: list | None = None, params: dict | None = None,
             parent_take_id: int | None = None, fixes_review_ids: list | None = None,
             agent_note: str = "", file_path: str = "", status: str | None = None,
             created_by: str = "agent") -> int:
    ep = db.get_or_create_episode(conn, episode)
    take_id = db.insert(conn, "takes", {
        "episode_id": ep["id"], "cut_id": cut_id, "kind": kind, "provider": provider, "model": model,
        "prompt": prompt, "refs_json": json.dumps(refs or [], ensure_ascii=False),
        "params_json": json.dumps(params or {}, ensure_ascii=False), "parent_take_id": parent_take_id,
        "fixes_review_ids": json.dumps(fixes_review_ids or []), "agent_note": agent_note,
        "file_path": file_path, "status": status or ("done" if file_path else "awaiting_upload"),
        "created_by": created_by, "created_at": db.now()})
    for rid in fixes_review_ids or []:
        db.update(conn, "reviews", rid, {"status": "working", "updated_at": db.now()})
    db.log(conn, created_by, "add_take", {"take": take_id, "cut": cut_id, "kind": kind, "provider": provider})
    return take_id


def attach_file(conn, take_id: int, src: Path, filename: str | None = None) -> str:
    take = db.one(conn.execute("SELECT t.*, e.code FROM takes t JOIN episodes e ON e.id=t.episode_id WHERE t.id=?",
                               (take_id,)))
    name = filename or src.name
    rel = Path(take["code"]) / f"take{take_id:05d}_{name}"
    dest = config.MEDIA_DIR / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest)
    db.update(conn, "takes", take_id, {"file_path": rel.as_posix(), "status": "done"})
    return rel.as_posix()


def select_take(conn, take_id: int) -> None:
    take = db.one(conn.execute("SELECT * FROM takes WHERE id=?", (take_id,)))
    conn.execute("UPDATE takes SET selected=0 WHERE cut_id=?", (take["cut_id"],))
    db.update(conn, "takes", take_id, {"selected": 1})
    db.log(conn, "human", "select_take", {"take": take_id, "cut": take["cut_id"]})


class Blocked(RuntimeError):
    """予算や作り直しの上限で、人の判断が要る。"""


def estimate(provider: str, kind: str, units: float = 1) -> float:
    c = config.COST_TABLE
    return units * c.get((provider, kind), c.get((provider, "*"), 0))


def spent(conn, episode_id: int) -> float:
    return conn.execute("SELECT COALESCE(SUM(credits),0) FROM usage WHERE episode_id=?", (episode_id,)).fetchone()[0]


def agent_retries_since_human(conn, cut_id: int) -> int:
    """最後に人がレビューしてから、エージェントがこのコマで作ったテイクの数。"""
    last = conn.execute("""SELECT MAX(r.created_at) FROM reviews r
        LEFT JOIN takes t ON r.target_type='take' AND t.id=r.target_id
        WHERE r.created_by='human' AND (t.cut_id=? OR (r.target_type='cut' AND r.target_id=?))""",
                        (cut_id, cut_id)).fetchone()[0] or ""
    return conn.execute("SELECT COUNT(*) FROM takes WHERE cut_id=? AND created_by='agent' AND created_at>?",
                        (cut_id, last)).fetchone()[0]


def check_gates(conn, episode: str, cut_id: int | None, provider: str, kind: str, units: float = 1) -> None:
    ep = db.get_or_create_episode(conn, episode)
    budget = ep.get("budget_credits") or 0
    cost = estimate(provider, kind, units)
    if budget and spent(conn, ep["id"]) + cost > budget:
        raise Blocked(f"{episode} の予算 {budget} を超えます（使用 {spent(conn, ep['id']):.0f} + 今回 {cost:.0f}）。"
                      "優先するコマを監督に確認してください")
    if cut_id and agent_retries_since_human(conn, cut_id) > config.MAX_AGENT_RETRIES:
        raise Blocked(f"このコマはレビューなしで {config.MAX_AGENT_RETRIES + 1} 回作り直しました。"
                      "方向を監督に確認してください（cli: reviews / 画面: レビュー）")


def record_usage(conn, take_id: int, provider: str, kind: str, units: float = 1,
                 credits: float | None = None, note: str = "") -> None:
    t = db.one(conn.execute("SELECT episode_id FROM takes WHERE id=?", (take_id,)))
    db.insert(conn, "usage", {"ts": db.now(), "episode_id": t["episode_id"], "take_id": take_id,
                              "provider": provider, "kind": kind, "units": units,
                              "credits": estimate(provider, kind, units) if credits is None else credits,
                              "note": note})


def generate(conn, *, episode: str, cut_id: int | None, kind: str, provider: str, prompt: str,
             model: str = "", refs: list | None = None, params: dict | None = None, **extra) -> int:
    p = REGISTRY[provider]
    check_gates(conn, episode, cut_id, provider, kind)
    take_id = add_take(conn, episode=episode, cut_id=cut_id, kind=kind, provider=provider, model=model,
                       prompt=prompt, refs=refs, params=params, status="queued", **extra)
    try:
        job = p.submit(GenerationRequest(kind, prompt, model, refs or [], params or {}))
        db.update(conn, "takes", take_id, {"external_job_id": job,
                                           "status": "running" if job else "awaiting_upload"})
        record_usage(conn, take_id, provider, kind)
    except Exception as e:  # 未接続・API エラーもテイクとして残し、画面とエージェントの両方から見えるようにする
        db.update(conn, "takes", take_id, {"status": "failed", "error": f"{type(e).__name__}: {e}"})
    return take_id


def poll_running(conn) -> int:
    """running のテイクを1回ずつ確認し、終わったものは結果をダウンロードする。"""
    n = 0
    for t in db.rows(conn.execute("SELECT * FROM takes WHERE status='running'")):
        st = REGISTRY[t["provider"]].poll(t["external_job_id"])
        if st.state == "done" and st.result_urls:
            ep = db.one(conn.execute("SELECT code FROM episodes WHERE id=?", (t["episode_id"],)))
            ext = Path(st.result_urls[0].split("?")[0]).suffix or ".bin"
            rel = Path(ep["code"]) / f"take{t['id']:05d}{ext}"
            (config.MEDIA_DIR / rel).parent.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(st.result_urls[0], config.MEDIA_DIR / rel)
            db.update(conn, "takes", t["id"], {"status": "done", "file_path": rel.as_posix()})
            n += 1
        elif st.state == "failed":
            db.update(conn, "takes", t["id"], {"status": "failed", "error": st.error})
    return n


def take_lineage(conn, take_id: int) -> list[dict]:
    chain, cur = [], take_id
    while cur:
        t = db.one(conn.execute("SELECT * FROM takes WHERE id=?", (cur,)))
        if not t:
            break
        chain.append(t)
        cur = t["parent_take_id"]
    return chain


# ---- レビュー ----

def _episode_id_for(conn, target_type: str, target_id: int) -> int | None:
    table = {"take": "takes", "cut": "cuts", "document": "documents"}.get(target_type)
    if target_type == "episode":
        return target_id
    r = db.one(conn.execute(f"SELECT episode_id FROM {table} WHERE id=?", (target_id,)))
    return r["episode_id"] if r else None


def add_review(conn, *, target_type: str, target_id: int, verdict: str = "修正", comment: str = "",
               tags: list[str] | None = None, score: int | None = None, region: dict | None = None,
               created_by: str = "human") -> int:
    rid = db.insert(conn, "reviews", {
        "episode_id": _episode_id_for(conn, target_type, target_id), "target_type": target_type,
        "target_id": target_id, "verdict": verdict, "score": score, "tags": ",".join(tags or []),
        "comment": comment, "region_json": json.dumps(region) if region else "",
        "status": "resolved" if verdict in ("採用", "良い") else "open",
        "created_by": created_by, "created_at": db.now(), "updated_at": db.now()})
    if verdict == "採用" and target_type == "take":
        select_take(conn, target_id)
    db.log(conn, created_by, "add_review", {"review": rid, "target": f"{target_type}:{target_id}", "verdict": verdict})
    return rid


def respond_review(conn, review_id: int, response: str, take_id: int | None = None,
                   status: str = "proposed") -> None:
    """エージェントの返答。直したテイクを示して proposed にし、人が確認して resolved にする。"""
    db.update(conn, "reviews", review_id, {"agent_response": response, "resolved_by_take_id": take_id,
                                           "status": status, "updated_at": db.now()})
    db.log(conn, "agent", "respond_review", {"review": review_id, "take": take_id, "status": status})


def set_review_status(conn, review_id: int, status: str, actor: str = "human") -> None:
    db.update(conn, "reviews", review_id, {"status": status, "updated_at": db.now()})
    db.log(conn, actor, "review_status", {"review": review_id, "status": status})


def list_reviews(conn, episode: str | None = None, status: str | None = None,
                 by: str | None = None) -> list[dict]:
    q, args = """SELECT r.*, t.file_path AS take_file, t.kind AS take_kind, c.cut, c.panel, c.id AS cut_ref
                 FROM reviews r
                 LEFT JOIN takes t ON r.target_type='take' AND t.id=r.target_id
                 LEFT JOIN cuts c ON c.id = COALESCE(t.cut_id, CASE WHEN r.target_type='cut' THEN r.target_id END)
                 WHERE 1=1""", []
    if episode:
        q += " AND r.episode_id=(SELECT id FROM episodes WHERE code=?)"
        args.append(episode)
    if by:
        q += " AND r.created_by=?"
        args.append(by)
    if status:
        sts = status.split(",")
        q += f" AND r.status IN ({','.join('?' * len(sts))})"
        args += sts
    return db.rows(conn.execute(q + " ORDER BY r.id DESC", args))


def self_review(conn, take_id: int, checks: dict, comment: str = "", passed: bool | None = None) -> int:
    """エージェント自身のレビュー。checks は {"意図": true, "芝居": "まひるの持ち方があかねになっている", ...}。
    true 以外の値が1つでもあれば不合格。合格は監督の「AIが通したもの」に、不合格はエージェントの作り直し対象になる。"""
    ok = all(v is True for v in checks.values()) if passed is None else passed
    rid = db.insert(conn, "reviews", {
        "episode_id": _episode_id_for(conn, "take", take_id), "target_type": "take", "target_id": take_id,
        "verdict": "良い" if ok else "修正",
        "tags": ",".join(k for k, v in checks.items() if v is not True),
        "comment": comment, "checks_json": json.dumps(checks, ensure_ascii=False),
        "status": "resolved" if ok else "working", "created_by": "agent",
        "created_at": db.now(), "updated_at": db.now()})
    db.log(conn, "agent", "self_review", {"review": rid, "take": take_id, "pass": ok})
    return rid


def awaiting_human(conn, code: str) -> list[dict]:
    """AI が通したが、監督がまだ見ていないテイク（監督が上から確認する列）。"""
    return db.rows(conn.execute("""
        SELECT t.*, c.cut, c.panel, c.seq, r.comment AS ai_comment, r.checks_json
        FROM takes t JOIN cuts c ON c.id=t.cut_id JOIN episodes e ON e.id=t.episode_id
        JOIN reviews r ON r.target_type='take' AND r.target_id=t.id AND r.created_by='agent' AND r.verdict='良い'
        WHERE e.code=? AND NOT EXISTS (SELECT 1 FROM reviews h WHERE h.target_type='take' AND h.target_id=t.id
                                       AND h.created_by='human')
        ORDER BY c.seq, t.id""", (code,)))


# ---- 設計（シーン） ----

SCENE_FIELDS = ("place", "time", "look", "target_seconds", "purpose", "emotion", "blocking", "cameras",
                "props", "status", "seq")


def set_scene(conn, episode: str, code: str, **fields) -> int:
    ep = db.get_or_create_episode(conn, episode)
    data = {k: v for k, v in fields.items() if k in SCENE_FIELDS and v is not None}
    row = db.one(conn.execute("SELECT id FROM scenes WHERE episode_id=? AND code=?", (ep["id"], code)))
    if row:
        db.update(conn, "scenes", row["id"], data)
        sid = row["id"]
    else:
        data.setdefault("seq", conn.execute("SELECT COUNT(*)+1 FROM scenes WHERE episode_id=?",
                                            (ep["id"],)).fetchone()[0])
        sid = db.insert(conn, "scenes", {"episode_id": ep["id"], "code": code, **data})
    db.log(conn, "agent", "set_scene", {"episode": episode, "scene": code, "fields": list(data)})
    return sid


def scenes(conn, code: str) -> dict:
    ep = db.episode_by_code(conn, code)
    rows = db.rows(conn.execute("SELECT * FROM scenes WHERE episode_id=? ORDER BY seq", (ep["id"],)))
    actual = {r["scene"]: r["s"] for r in db.rows(conn.execute(
        "SELECT scene, ROUND(SUM(seconds),1) s, COUNT(*) n FROM cuts WHERE episode_id=? GROUP BY scene", (ep["id"],)))}
    for r in rows:
        r["actual_seconds"] = actual.get(r["code"], 0)
    return {"episode": ep, "scenes": rows, "spent": spent(conn, ep["id"])}


def update_cut(conn, cut_id: int, actor: str = "human", **fields) -> None:
    """尺・台詞などの手直し。編集画面から人が、または CLI からエージェントが使う。"""
    allowed = {"seconds", "dialogue", "picture", "edit_memo", "camerawork", "seq"}
    data = {k: v for k, v in fields.items() if k in allowed}
    db.update(conn, "cuts", cut_id, data)
    db.log(conn, actor, "update_cut", {"cut": cut_id, **data})


# ---- 比較 ----

def add_comparison(conn, *, take_ids: list[int], winner_take_id: int | None, reason: str = "",
                   axes: dict | None = None) -> int:
    t = db.one(conn.execute("SELECT episode_id, cut_id FROM takes WHERE id=?", (take_ids[0],)))
    cid = db.insert(conn, "comparisons", {
        "episode_id": t["episode_id"], "cut_id": t["cut_id"], "take_ids_json": json.dumps(take_ids),
        "winner_take_id": winner_take_id, "axes_json": json.dumps(axes or {}, ensure_ascii=False),
        "reason": reason, "created_at": db.now()})
    db.log(conn, "human", "compare", {"comparison": cid, "winner": winner_take_id})
    return cid


# ---- ルール ----

def propose_learning(conn, rule_text: str, scope: str = "series", source_review_ids: list | None = None,
                     vault_target: str = "") -> int:
    lid = db.insert(conn, "learnings", {"rule_text": rule_text, "scope": scope,
                                        "source_review_ids": json.dumps(source_review_ids or []),
                                        "vault_target": vault_target, "created_at": db.now()})
    db.log(conn, "agent", "propose_learning", {"learning": lid})
    return lid


def decide_learning(conn, lid: int, approve: bool, rule_text: str | None = None) -> None:
    data = {"status": "approved" if approve else "rejected", "decided_at": db.now()}
    if rule_text:
        data["rule_text"] = rule_text
    db.update(conn, "learnings", lid, data)
    db.log(conn, "human", "decide_learning", {"learning": lid, "approve": approve})


# ---- 背景（Blender） ----

def render_bg(conn, *, episode: str, blend: str, camera: str, cut_id: int | None = None, note: str = "",
              extra_args: list[str] | None = None) -> int:
    """Blender をバックグラウンドで動かし、カメラ1つ分の背景を参照用テイク（kind=bg）として登録する。"""
    import subprocess
    import tempfile
    exe = config.BLENDER_EXE
    script = Path(__file__).parent / "blender" / "render_shot.py"
    out = Path(tempfile.mkdtemp()) / f"{Path(blend).stem}_{camera}.png"
    take_id = add_take(conn, episode=episode, cut_id=cut_id, kind="bg", provider="blender",
                       prompt=f"{Path(blend).name} / camera {camera}", agent_note=note, status="running")
    cmd = [exe, "-b", blend, "--python", str(script), "--", "--camera", camera, "--out", str(out),
           *(extra_args or [])]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=1800)
        meta = json.loads(out.with_suffix(".json").read_text(encoding="utf-8"))
        attach_file(conn, take_id, out)
        db.update(conn, "takes", take_id, {"params_json": json.dumps(meta, ensure_ascii=False)})
    except (OSError, subprocess.SubprocessError, FileNotFoundError) as e:
        db.update(conn, "takes", take_id, {"status": "failed", "error": f"{type(e).__name__}: {e}"})
    return take_id


# ---- 書き出し ----

def export_timeline(conn, code: str) -> dict:
    data = episode_cuts(conn, code)
    selected = {c["id"]: next((t for t in c["takes"] if t["selected"]), None) for c in data["cuts"]}
    items = fcpxml.timeline(data["cuts"], {k: v for k, v in selected.items() if v})
    name = f"{code}_studio_{db.now()[:10]}"
    out_dir = config.DATA_DIR / "exports" / code
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{name}.xml").write_text(fcpxml.to_xmeml(name, items), encoding="utf-8")
    (out_dir / f"{name}.ffconcat").write_text(fcpxml.to_ffconcat(items), encoding="utf-8")
    missing = [f"{i['cut']['cut']}{i['cut']['panel']}" for i in items if not i["take"]]
    return {"xml": str(out_dir / f"{name}.xml"), "ffconcat": str(out_dir / f"{name}.ffconcat"),
            "frames": items[-1]["end"] if items else 0, "missing": missing}
