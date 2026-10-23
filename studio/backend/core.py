"""画面（app.py）とエージェント用 CLI（cli.py）が共通で使う操作。"""
import json
import shutil
import urllib.request
from pathlib import Path

from . import config, db, direction
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
    # このコマを含むショット（マルチショットの動画）のテイクも出す
    shot_ids = [r["id"] for r in db.rows(conn.execute(
        "SELECT id, cut_ids_json FROM shots WHERE episode_id=?", (cut["episode_id"],)))
        if cut_id in json.loads(r["cut_ids_json"])]
    takes = db.rows(conn.execute(
        f"SELECT * FROM takes WHERE cut_id=? OR shot_id IN ({','.join('?' * len(shot_ids)) or 'NULL'}) ORDER BY id DESC",
        (cut_id, *shot_ids)))
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
    db.update(conn, "takes", take_id, {"file_path": rel.as_posix(), "status": "done", "finished_at": db.now()})
    return rel.as_posix()


def select_take(conn, take_id: int) -> None:
    take = db.one(conn.execute("SELECT * FROM takes WHERE id=?", (take_id,)))
    if take.get("shot_id"):     # ショットの動画は、同じショット・同じ段階（ドラフト／本番）の中で1つ
        conn.execute("UPDATE takes SET selected=0 WHERE shot_id=? AND COALESCE(tier,'')=?",
                     (take["shot_id"], take.get("tier") or ""))
    else:
        conn.execute("UPDATE takes SET selected=0 WHERE cut_id=? AND shot_id IS NULL", (take["cut_id"],))
    db.update(conn, "takes", take_id, {"selected": 1})
    db.log(conn, "human", "select_take", {"take": take_id, "cut": take["cut_id"]})


class Blocked(RuntimeError):
    """予算や作り直しの上限で、人の判断が要る。"""


def estimate(provider: str, kind: str, units: float = 1, tier: str = "") -> float:
    """円の目安。動画は units＝秒。"""
    c = config.COST_TABLE
    if kind in config.PER_SECOND_KINDS and provider not in ("manual", "blender") and tier in config.TIERS:
        return units * config.TIERS[tier]["yen_per_sec"]
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


def check_gates(conn, episode: str, cut_id: int | None, provider: str, kind: str, units: float = 1,
                tier: str = "") -> None:
    ep = db.get_or_create_episode(conn, episode)
    budget = ep.get("budget_credits") or config.DEFAULT_BUDGET_YEN
    cost = estimate(provider, kind, units, tier)
    if budget and spent(conn, ep["id"]) + cost > budget:
        if ep.get("is_test"):
            print(f"注意：{episode} はテストの回なので続けます（予算 {budget:.0f}円 を超えます）")
            return
        raise Blocked(f"{episode} の予算 {budget} を超えます（使用 {spent(conn, ep['id']):.0f} + 今回 {cost:.0f}）。"
                      "優先するコマを監督に確認してください")
    if cut_id and agent_retries_since_human(conn, cut_id) > config.MAX_AGENT_RETRIES:
        raise Blocked(f"このコマはレビューなしで {config.MAX_AGENT_RETRIES + 1} 回作り直しました。"
                      "方向を監督に確認してください（cli: reviews / 画面: レビュー）")


def record_usage(conn, take_id: int, provider: str, kind: str, units: float = 1,
                 credits: float | None = None, note: str = "", tier: str = "") -> None:
    t = db.one(conn.execute("SELECT episode_id FROM takes WHERE id=?", (take_id,)))
    db.insert(conn, "usage", {"ts": db.now(), "episode_id": t["episode_id"], "take_id": take_id,
                              "provider": provider, "kind": kind, "units": units,
                              "credits": estimate(provider, kind, units, tier) if credits is None else credits,
                              "note": note})


def generate(conn, *, episode: str, cut_id: int | None, kind: str, provider: str, prompt: str,
             model: str = "", refs: list | None = None, params: dict | None = None, tier: str = "",
             source_take_id: int | None = None, shot_id: int | None = None, board_id: int | None = None,
             **extra) -> int:
    p = REGISTRY[provider]
    params = dict(params or {})
    if tier:
        params.setdefault("resolution", config.TIERS[tier]["resolution"])
        params["tier"] = tier
    if source_take_id:
        src = db.one(conn.execute("SELECT file_path FROM takes WHERE id=?", (source_take_id,)))
        params["input_video"] = src["file_path"]          # 拡大版を入力に本番を作る
    if tier == "final" and not source_take_id:
        raise Blocked("本番（1080p）は、承認したドラフトの拡大版から作ります（promote を使う）")
    units = float(params.get("duration", 1)) if kind in config.PER_SECOND_KINDS else 1
    check_gates(conn, episode, cut_id, provider, kind, units=units, tier=tier)
    take_id = add_take(conn, episode=episode, cut_id=cut_id, kind=kind, provider=provider, model=model,
                       prompt=prompt, refs=refs, params=params, status="queued", **extra)
    try:
        job = p.submit(GenerationRequest(kind, prompt, model, refs or [], params))
        db.update(conn, "takes", take_id, {"external_job_id": job, "submitted_at": db.now(),
                                           "status": "running" if job else "awaiting_upload"})
        record_usage(conn, take_id, provider, kind, units=units, tier=tier)
    except Exception as e:  # 未接続・API エラーもテイクとして残し、画面とエージェントの両方から見えるようにする
        db.update(conn, "takes", take_id, {"status": "failed", "error": f"{type(e).__name__}: {e}"})
    if tier or source_take_id or shot_id or board_id:
        db.update(conn, "takes", take_id, {"tier": tier, "source_take_id": source_take_id,
                                           "shot_id": shot_id, "board_id": board_id})
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
            db.update(conn, "takes", t["id"], {"status": "done", "file_path": rel.as_posix(), "finished_at": db.now()})
            n += 1
        elif st.state == "failed":
            db.update(conn, "takes", t["id"], {"status": "failed", "error": st.error, "finished_at": db.now()})
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
               created_by: str = "human", image_data: str | None = None) -> int:
    rid = db.insert(conn, "reviews", {
        "episode_id": _episode_id_for(conn, target_type, target_id), "target_type": target_type,
        "target_id": target_id, "verdict": verdict, "score": score, "tags": ",".join(tags or []),
        "comment": comment, "region_json": json.dumps(region) if region else "",
        "status": "resolved" if verdict in ("採用", "良い") else "open",
        "created_by": created_by, "created_at": db.now(), "updated_at": db.now()})
    if image_data and image_data.startswith("data:image/"):
        # 画面に矢印や囲みを描いたまま止めた絵。エージェントはこれを見て、どこをどう直すかを読む
        import base64
        rel = Path("reviews") / f"review{rid:05d}.png"
        (config.MEDIA_DIR / rel).parent.mkdir(parents=True, exist_ok=True)
        (config.MEDIA_DIR / rel).write_bytes(base64.b64decode(image_data.split(",", 1)[1]))
        db.update(conn, "reviews", rid, {"attachment": rel.as_posix()})
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
                "props", "status", "seq",
                # シーン整理：変化（前→後）とそのきっかけ、キャラごとの欲求・芝居・内心、小さな区切り、脚本の範囲
                "change_before", "change_after", "turn", "characters", "beats", "script_from", "script_to")


def set_scene(conn, episode: str, code: str, actor: str = "agent", **fields) -> int:
    ep = db.get_or_create_episode(conn, episode)
    data = {k: v for k, v in fields.items() if k in SCENE_FIELDS and v is not None}
    for k in ("characters", "beats"):   # [{name, want, does, inner, tension}] / [{seconds, who, does, why}]
        if k in data:
            v = data.pop(k)
            data[f"{k}_json"] = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    row = db.one(conn.execute("SELECT id FROM scenes WHERE episode_id=? AND code=?", (ep["id"], code)))
    if row:
        db.update(conn, "scenes", row["id"], data)
        sid = row["id"]
    else:
        data.setdefault("seq", conn.execute("SELECT COUNT(*)+1 FROM scenes WHERE episode_id=?",
                                            (ep["id"],)).fetchone()[0])
        sid = db.insert(conn, "scenes", {"episode_id": ep["id"], "code": code, **data})
    db.log(conn, actor, "set_scene", {"episode": episode, "scene": code, "fields": list(data)})
    return sid


def scenes(conn, code: str) -> dict:
    ep = db.episode_by_code(conn, code)
    rows = db.rows(conn.execute("SELECT * FROM scenes WHERE episode_id=? ORDER BY seq", (ep["id"],)))
    actual = {r["scene"]: r["s"] for r in db.rows(conn.execute(
        "SELECT scene, ROUND(SUM(seconds),1) s, COUNT(*) n FROM cuts WHERE episode_id=? GROUP BY scene", (ep["id"],)))}
    for r in rows:
        r["actual_seconds"] = actual.get(r["code"], 0)
        for k in ("characters", "beats"):
            try:
                r[k] = json.loads(r.pop(f"{k}_json") or "[]")
            except ValueError:
                r[k] = []
        r["blocking_plan"] = json.loads(r.pop("blocking_json", "") or "{}")
        r["blocking_text"] = direction.blocking_text(r["blocking_plan"])
    return {"episode": ep, "scenes": rows, "spent": spent(conn, ep["id"])}


def scene_script(conn, code: str, scene: str) -> dict:
    """シーンの脚本の範囲（script_from の行から script_to の行まで）。どちらも脚本の一節で指す（行番号は変わるので）。"""
    ep = db.episode_by_code(conn, code)
    sc = db.one(conn.execute("SELECT * FROM scenes WHERE episode_id=? AND code=?", (ep["id"], scene)))
    path = config.VAULT_DIR / "03_脚本" / "いまの版" / f"{code}_脚本_いまの版.md"
    if not sc or not path.exists() or not sc.get("script_from"):
        return {"found": False, "lines": []}
    lines = [l.rstrip() for l in path.read_text(encoding="utf-8").splitlines()]
    plain = [l.replace("**", "") for l in lines]
    a = next((i for i, l in enumerate(plain) if sc["script_from"] in l), None)
    if a is None:
        return {"found": False, "lines": []}
    b = next((i for i in range(a, len(plain)) if sc.get("script_to") and sc["script_to"] in plain[i]), a + 30)
    heading = next((plain[i].lstrip("# ") for i in range(a, -1, -1) if plain[i].startswith("###")), "")
    return {"found": True, "heading": heading, "lines": [l for l in plain[a:b + 1] if l.strip() and l.strip() != "× × ×"]}


def scene_sheet_md(conn, code: str) -> str:
    """シーン整理を vault に置く形（02_各話/EPxx/EPxx_シーン整理.md）。監督が Obsidian でも読めるように。"""
    sc = scenes(conn, code)
    out = ["---", f'title: "{code} シーン整理"', f"date: {db.now()[:10]}", f"tags: [シーン整理, {code}]", "---",
           f"# {code} シーン整理", "",
           "脚本と字コンテの間の段。シーンごとに「何が変わるか」「誰が何をしたくて、何をするか」を先に決め、"
           "字コンテのカットごとの意図はここから引く。月灯スタジオの「シーン整理」で監督が確認する。", ""]
    for s_ in sc["scenes"]:
        out += [f"## {s_['code']}　{s_['place']}・{s_['time']}　{s_['target_seconds']:g}秒　[{s_['status']}]", "",
                f"- **見せたいもの**：{s_['purpose']}",
                f"- **変化**：{s_['change_before'] or '―'} → {s_['change_after'] or '―'}",
                f"- **きっかけ**：{s_['turn'] or '―'}"]
        if s_["characters"]:
            out += ["", "| キャラ | したいこと | すること（見える芝居） | 内心 | 温度 |", "| --- | --- | --- | --- | --- |"]
            out += [f"| {c.get('name','')} | {c.get('want','')} | {c.get('does','')} | {c.get('inner','')} | "
                    f"{'●' * int(c.get('tension') or 0)}{'○' * (5 - int(c.get('tension') or 0))} |" for c in s_["characters"]]
        if s_["beats"]:
            out += ["", "区切り："]
            out += [f"{i}. （{b.get('seconds', '')}秒{'・高さ' + str(b['level']) if b.get('level') else ''}）"
                    f"{'★' + b['peak'] + '　' if b.get('peak') else ''}{b.get('who', '')}：{b.get('does', '')}"
                    + (f" ― {b['why']}" if b.get("why") else "") for i, b in enumerate(s_["beats"], 1)]
        if s_["blocking"]:
            out += ["", f"立ち位置と動線：{s_['blocking']}"]
        if s_["blocking_text"]:
            out += ["", "配置図："] + [f"- {t}" for t in s_["blocking_text"]]
        out.append("")
    return "\n".join(out)


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
              extra_args: list[str] | None = None, asset_name: str = "") -> int:
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
        rel = attach_file(conn, take_id, out)
        db.update(conn, "takes", take_id, {"params_json": json.dumps(meta, ensure_ascii=False)})
        from . import shots
        shots.add_asset(conn, "bg", asset_name or f"{Path(blend).stem}:{camera}", rel, meta=meta, note=note,
                        replace=True)
    except (OSError, subprocess.SubprocessError, FileNotFoundError) as e:
        db.update(conn, "takes", take_id, {"status": "failed", "error": f"{type(e).__name__}: {e}"})
    return take_id


# ---- 書き出し ----

def playlist(conn, code: str, selected_only: bool = False) -> list[dict]:
    """上映順のコマごとに、いま映すもの（テイクと、その動画の中の開始位置）を決める。

    ショット（マルチショットの動画）に入っているコマは、そのショットの動画を、ショット内の位置から映す。
    優先：本番（採用）＞ ドラフト（採用）＞ 最新のドラフト ＞ コマ自身のテイク（9コマの仮Vコンなど）。
    selected_only=True なら採用中のものだけ（書き出し用）。
    """
    data = episode_cuts(conn, code)
    cuts = data["cuts"]
    ep_id = data["episode"]["id"]
    shots = db.rows(conn.execute("SELECT * FROM shots WHERE episode_id=? ORDER BY seq", (ep_id,)))
    shot_of = {}
    for sh in shots:
        ids = json.loads(sh["cut_ids_json"])
        sh["cut_ids"] = ids
        for cid in ids:
            shot_of[cid] = sh
    shot_takes = {}
    for sh in shots:
        ts = db.rows(conn.execute("SELECT * FROM takes WHERE shot_id=? AND status='done' AND file_path!='' "
                                  "ORDER BY id DESC", (sh["id"],)))
        rank = lambda t: (t["selected"] and t["tier"] == "final", t["selected"] and t["tier"] == "draft",
                          t["selected"], not selected_only and t["tier"] == "draft")
        best = max(ts, key=rank, default=None)
        if best and selected_only and not best["selected"]:
            best = None
        if best and not any(rank(best)):
            best = None
        shot_takes[sh["id"]] = best
    out = []
    for c in cuts:
        sh = shot_of.get(c["id"])
        item = {"cut": c, "take": None, "offset": 0.0, "shot": sh["code"] if sh else "", "shot_first": False,
                "shot_seconds": 0.0}
        if sh and shot_takes.get(sh["id"]):
            idx = sh["cut_ids"].index(c["id"])
            secs = {x["id"]: x["seconds"] or 0 for x in cuts if x["id"] in sh["cut_ids"]}
            item.update(take=shot_takes[sh["id"]], offset=sum(secs[i] for i in sh["cut_ids"][:idx]),
                        shot_first=idx == 0, shot_seconds=sum(secs.values()))
        else:
            own = [t for t in c["takes"] if t["file_path"] and not t.get("shot_id") and t["kind"] != "audio"]
            pick = next((t for t in own if t["selected"]), None) or (None if selected_only else (own[-1] if own else None))
            item["take"] = pick
        item["audio"] = _cut_audio(c)
        out.append(item)
    return out


AUDIO_ROLES = {"actor": "A1 声", "voice": "A1 声", "sfx": "A2 効果音", "music": "A3 劇伴"}


def _cut_audio(c: dict) -> list[dict]:
    """このコマで鳴らす音。声は 声優 ＞ 仮の声（Runway）の順で1つ、効果音・劇伴はそれぞれ採用中か最新。
    Seedance がドラフトに付けた音声は使わない（編集では動画の音を切る）。"""
    aud = [t for t in c["takes"] if t["kind"] == "audio" and t["file_path"]]
    out = []
    voice = [t for t in aud if t.get("role") in ("actor", "voice")]
    pick = lambda ts: next((t for t in ts if t["selected"]), ts[-1] if ts else None)
    v = pick([t for t in voice if t.get("role") == "actor"]) or pick([t for t in voice if t.get("role") == "voice"])
    if v:
        out.append(v)
    for role in ("sfx", "music"):
        x = pick([t for t in aud if t.get("role") == role])
        if x:
            out.append(x)
    return out


def export_timeline(conn, code: str) -> dict:
    items, audio, frame = [], [], 0
    for p in playlist(conn, code, selected_only=True):
        dur = max(1, round((p["cut"]["seconds"] or 1.0) * config.FPS))
        for a in p["audio"]:
            alen = round(float(json.loads(a["params_json"] or "{}").get("audio_seconds", 0) or 0) * config.FPS) or dur
            audio.append({"track": AUDIO_ROLES.get(a.get("role") or "voice", "A1 声"), "take": a,
                          "start": frame, "end": frame + alen})
        if p["shot"] and p["take"]:
            if p["shot_first"]:     # ショットの動画は先頭のコマの位置に1本で置く
                items.append({"cut": p["cut"], "take": p["take"], "start": frame,
                              "end": frame + max(1, round(p["shot_seconds"] * config.FPS))})
        else:
            items.append({"cut": p["cut"], "take": p["take"], "start": frame, "end": frame + dur})
        frame += dur
    name = f"{code}_studio_{db.now()[:10]}"
    out_dir = config.DATA_DIR / "exports" / code
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{name}.xml").write_text(fcpxml.to_xmeml(name, items, audio), encoding="utf-8")
    (out_dir / f"{name}.ffconcat").write_text(fcpxml.to_ffconcat(items), encoding="utf-8")
    missing = [f"{i['cut']['cut']}{i['cut']['panel']}" for i in items if not i["take"]]
    return {"xml": str(out_dir / f"{name}.xml"), "ffconcat": str(out_dir / f"{name}.ffconcat"),
            "frames": frame, "missing": missing}


# ---- 実績：どの工程で、いくら使い、どれだけ待ったか ----

def _secs(a: str, b: str) -> float:
    from datetime import datetime
    try:
        return (datetime.fromisoformat(b) - datetime.fromisoformat(a)).total_seconds()
    except (TypeError, ValueError):
        return 0.0


def stage_of(t: dict) -> str:
    if t.get("board_id") or t["kind"] == "sheet" or t.get("tier") == "board":
        return "仮Vコン"
    if t["kind"] == "video":
        return {"draft": "480p ドラフト", "final": "1080p 本番", "mid": "720p"}.get(t.get("tier") or "", "動画")
    if t["kind"] == "audio":
        return "音声"
    if t["kind"] == "bg":
        return "背景"
    return "その他"


def stats(conn, code: str) -> dict:
    """工程ごとの 回数・費用・生成の待ち時間・監督のレビューまでの時間。数字で段取りを直すための材料。"""
    ep = db.episode_by_code(conn, code)
    takes = db.rows(conn.execute("SELECT * FROM takes WHERE episode_id=?", (ep["id"],)))
    cost = {r["take_id"]: r["c"] for r in db.rows(conn.execute(
        "SELECT take_id, SUM(credits) c FROM usage WHERE episode_id=? GROUP BY take_id", (ep["id"],)))}
    first_review = {r["target_id"]: r["ts"] for r in db.rows(conn.execute(
        "SELECT target_id, MIN(created_at) ts FROM reviews WHERE target_type='take' AND created_by='human' "
        "AND episode_id=? GROUP BY target_id", (ep["id"],)))}
    st: dict[str, dict] = {}
    for t in takes:
        k = stage_of(t)
        s_ = st.setdefault(k, {"stage": k, "n": 0, "failed": 0, "yen": 0.0, "seconds": 0.0,
                               "gen_wait": [], "review_wait": [], "adopted": 0})
        s_["n"] += 1
        s_["failed"] += t["status"] == "failed"
        s_["yen"] += cost.get(t["id"], 0)
        s_["seconds"] += float(json.loads(t["params_json"] or "{}").get("duration", 0) or 0) if t["kind"] == "video" else 0
        s_["adopted"] += bool(t["selected"])
        if t.get("submitted_at") and t.get("finished_at"):
            s_["gen_wait"].append(_secs(t["submitted_at"], t["finished_at"]))
        if t.get("finished_at") and t["id"] in first_review:
            s_["review_wait"].append(_secs(t["finished_at"], first_review[t["id"]]))
    out = []
    order = ["背景", "仮Vコン", "480p ドラフト", "720p", "1080p 本番", "動画", "音声", "その他"]
    for k in sorted(st, key=lambda x: order.index(x) if x in order else 99):
        s_ = st[k]
        avg = lambda xs: round(sum(xs) / len(xs) / 60, 1) if xs else None
        out.append({**{x: s_[x] for x in ("stage", "n", "failed", "adopted")}, "yen": round(s_["yen"]),
                    "video_seconds": round(s_["seconds"]), "gen_wait_min": avg(s_["gen_wait"]),
                    "gen_wait_total_min": round(sum(s_["gen_wait"]) / 60, 1),
                    "review_wait_min": avg(s_["review_wait"])})
    budget = ep.get("budget_credits") or config.DEFAULT_BUDGET_YEN
    return {"episode": code, "stages": out, "spent": round(spent(conn, ep["id"])), "budget": budget,
            "is_test": ep.get("is_test")}


def add_audio(conn, *, episode: str, cut_id: int, src: Path, role: str = "voice", speaker: str = "",
              note: str = "", created_by: str = "agent") -> int:
    """声・効果音・劇伴をコマに付ける。role：voice（仮の声）/ actor（声優）/ sfx / music。"""
    import subprocess
    try:
        secs = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                     str(src)], capture_output=True, text=True).stdout.strip() or 0)
    except (OSError, ValueError):
        secs = 0
    tid = add_take(conn, episode=episode, cut_id=cut_id, kind="audio",
                   provider="actor" if role == "actor" else "manual", prompt=speaker,
                   params={"audio_seconds": secs, "speaker": speaker}, agent_note=note, created_by=created_by)
    attach_file(conn, tid, src)
    db.update(conn, "takes", tid, {"role": role})
    return tid


# ---- 依頼：監督 → どのエージェントでも ----

def add_request(conn, text: str, episode: str = "") -> int:
    rid = db.insert(conn, "requests", {"ts": db.now(), "episode": episode, "text": text})
    db.log(conn, "human", "add_request", {"request": rid, "episode": episode})
    return rid


def list_requests(conn, status: str = "open,claimed") -> list[dict]:
    sts = status.split(",")
    return db.rows(conn.execute(f"SELECT * FROM requests WHERE status IN ({','.join('?' * len(sts))}) ORDER BY id",
                                sts))


def claim_request(conn, agent: str, request_id: int | None = None) -> dict | None:
    """依頼を1つ取る。id を指定しなければ、いちばん古い open を取る。取られていたら None。"""
    q = "SELECT * FROM requests WHERE status='open'" + (" AND id=?" if request_id else "") + " ORDER BY id LIMIT 1"
    r = db.one(conn.execute(q, (request_id,) if request_id else ()))
    if not r:
        return None
    cur = conn.execute("UPDATE requests SET status='claimed', claimed_by=?, claimed_at=? WHERE id=? AND status='open'",
                       (agent, db.now(), r["id"]))
    if cur.rowcount != 1:
        return None
    db.log(conn, "agent", "claim_request", {"request": r["id"], "by": agent})
    return {**r, "status": "claimed", "claimed_by": agent}


def finish_request(conn, request_id: int, result: str, status: str = "done") -> None:
    db.update(conn, "requests", request_id, {"status": status, "result": result, "done_at": db.now()})
    db.log(conn, "agent", "finish_request", {"request": request_id, "status": status})


# ---- 画面の印を言葉に（エージェントが読む） ----

def _where(x: float, y: float) -> str:
    col = "左" if x < 0.34 else "中央" if x < 0.67 else "右"
    row = "上" if y < 0.34 else "" if y < 0.67 else "下"
    return f"画面の{col}{row}" if row else ("画面の中央" if col == "中央" else f"画面の{col}")


def describe_region(region_json: str) -> str:
    if not region_json:
        return ""
    g = json.loads(region_json)
    parts = []
    if "t" in g:
        parts.append(f"{g['t']:.1f}秒の時点")
    if "t_in" in g:
        parts.append(f"{g['t_in']:.1f}〜{g.get('t_out', g['t_in']):.1f}秒")
    if "x" in g:
        parts.append(f"{_where(g['x'] + g['w'] / 2, g['y'] + g['h'] / 2)}の囲み")
    for sh in g.get("shapes", []):
        if sh.get("type") == "arrow":
            parts.append(f"矢印：{_where(sh['x1'], sh['y1'])}→{_where(sh['x2'], sh['y2'])}")
        elif sh.get("type") == "box":
            parts.append(f"囲み：{_where(sh['x'] + sh['w'] / 2, sh['y'] + sh['h'] / 2)}")
    return "（" + "、".join(parts) + "）" if parts else ""


# ---- 字コンテのコマ → 脚本の該当箇所 ----

def script_snippet(conn, cut_id: int, around: int = 4) -> dict:
    """コマの台詞（なければ同じカット・前のコマの台詞）を脚本（いまの版）から探し、前後の数行を返す。"""
    import re
    cut = db.one(conn.execute("SELECT c.*, e.code FROM cuts c JOIN episodes e ON e.id=c.episode_id WHERE c.id=?",
                              (cut_id,)))
    path = config.VAULT_DIR / "03_脚本" / "いまの版" / f"{cut['code']}_脚本_いまの版.md"
    if not path.exists():
        return {"found": False, "lines": [], "heading": "", "file": ""}
    lines = [l.rstrip() for l in path.read_text(encoding="utf-8").splitlines()]
    cands = db.rows(conn.execute("SELECT dialogue, picture FROM cuts WHERE episode_id=? AND seq<=? ORDER BY seq DESC LIMIT 12",
                                 (cut["episode_id"], cut["seq"])))
    total = conn.execute("SELECT COUNT(*) FROM cuts WHERE episode_id=?", (cut["episode_id"],)).fetchone()[0] or 1
    norm = lambda t: re.sub(r"[\s　…―ー！？!?、。『』]", "", t)
    hit = None
    for c in cands:
        # 「話者「台詞」」の組で探す。短い台詞（「行った」など）がト書きに当たらないよう、台詞の行（「を含む行）だけを見る
        for who, q in re.findall(r"([^\s「」（）]+)(?:（[^）]*）)?「([^」]+)」", c["dialogue"] or ""):
            key = norm(q)[:8]
            if not key:
                continue
            found = [i for i, l in enumerate(lines)
                     if "「" in l and key in norm(l.split("「", 1)[1]) and (who in l or len(key) >= 4)]
            # 同じ台詞が何度も出るとき（「ニャー」など）は、話の中の位置がいちばん近いものを選ぶ
            hit = min(found, key=lambda i: abs(i / len(lines) - cut["seq"] / total)) if found else None
            if hit is not None:
                break
        if hit is not None:
            break
    if hit is None:
        return {"found": False, "lines": [], "heading": "", "file": str(path.relative_to(config.VAULT_DIR))}
    heading = next((lines[i].lstrip("# ") for i in range(hit, -1, -1) if lines[i].startswith("###")), "")
    body = [(i, l) for i, l in enumerate(lines) if l.strip()]
    pos = next(k for k, (i, _) in enumerate(body) if i == hit)
    sel = body[max(0, pos - around): pos + around + 1]
    return {"found": True, "heading": heading, "file": str(path.relative_to(config.VAULT_DIR)),
            "lines": [{"text": l.replace("**", ""), "hit": i == hit} for i, l in sel if not l.startswith("###")]}


def episode_marks(conn, code: str) -> list[dict]:
    """Vコンの上に出す、監督とエージェントのレビュー（どのコマの、何秒で、どんな印か）。"""
    return db.rows(conn.execute("""
        SELECT r.id, r.verdict, r.status, r.comment, r.tags, r.region_json, r.attachment, r.created_by,
               r.agent_response, r.created_at,
               COALESCE(t.cut_id, CASE WHEN r.target_type='cut' THEN r.target_id END) AS cut_id,
               r.target_type, r.target_id
        FROM reviews r LEFT JOIN takes t ON r.target_type='take' AND t.id=r.target_id
        WHERE r.episode_id=(SELECT id FROM episodes WHERE code=?) AND r.target_type IN ('take','cut')
        ORDER BY r.id""", (code,)))
