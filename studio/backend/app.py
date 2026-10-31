"""レビュー画面の API。起動：  python -m uvicorn studio.backend.app:app --reload  （リポジトリ直下で）"""
import json
import tempfile
import threading
import time
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, PlainTextResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import episodes as episodes_mod
from . import art, chat, config, context, core, db, direction, overview, pipeline, runner, scriptdoc, staff, versions

db.init()
with db.session() as _c:
    episodes_mod.ensure_series(_c)      # EP01〜EP12 の枠
app = FastAPI(title="月灯スタジオ")
app.mount("/media", StaticFiles(directory=config.MEDIA_DIR), name="media")
FRONTEND = config.STUDIO_DIR / "frontend"


def _poll_loop():
    while True:
        try:
            with db.session() as conn:
                core.poll_running(conn)
        except Exception as e:  # 外部サービスの一時的な失敗でループを止めない
            print("poll error:", e)
        time.sleep(15)


threading.Thread(target=_poll_loop, daemon=True).start()
runner.start()       # 会議の枠・役のついた依頼が空いたら、その役の AI を起こす（見張り番）


@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")


app.mount("/static", StaticFiles(directory=FRONTEND), name="static")


@app.get("/api/meta")
def meta():
    from .providers.services import REGISTRY
    return {"tags": core.REVIEW_TAGS, "verdicts": core.VERDICTS,
            "providers": {k: p.available() for k, p in REGISTRY.items()}}


@app.get("/api/episodes")
def episodes():
    with db.session() as conn:
        return core.episodes_with_script(conn)


@app.post("/api/episodes/{code}/split")
def episode_split(code: str):
    """vault にある脚本（いまの版）からシーンに分け、制作進行にシーン整理の下書きを頼む。"""
    with db.session() as conn:
        n = scriptdoc.split(conn, code)
        if n:
            rid = core.add_request(conn, f"[{code}] 脚本（いまの版）を読み、シーン整理の下書きを作る：この話の芯・物語の流れ（story-set）と、"
                                         f"シーンごとの ①伝えたいこと ②変化 ③あらすじ ④キャラ（scene-set。シーンは S1〜S{n} に分けてある）。終わったら request-done", code)
            db.update(conn, "requests", rid, {"role": "まとめ"})
        return {"scenes": n}


@app.get("/api/episodes/{code}/cuts")
def episode_cuts(code: str):
    with db.session() as conn:
        try:
            return core.episode_cuts(conn, code)
        except KeyError:
            raise HTTPException(404, f"{code} がありません")


@app.get("/api/cuts/{cut_id}")
def cut_detail(cut_id: int):
    with db.session() as conn:
        return core.cut_detail(conn, cut_id)


@app.get("/api/takes/{take_id}/lineage")
def lineage(take_id: int):
    with db.session() as conn:
        return core.take_lineage(conn, take_id)


@app.post("/api/takes/{take_id}/upload")
async def upload(take_id: int, file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(await file.read())
    with db.session() as conn:
        return {"file_path": core.attach_file(conn, take_id, Path(tmp.name), file.filename)}


@app.post("/api/cuts/{cut_id}/takes")
async def human_take(cut_id: int, file: UploadFile = File(...), note: str = Form("")):
    """人が外で作ったもの（Seedance の動画など）をそのコマのテイクとして足す。"""
    with db.session() as conn:
        cut = db.one(conn.execute("SELECT c.*, e.code FROM cuts c JOIN episodes e ON e.id=c.episode_id WHERE c.id=?",
                                  (cut_id,)))
        kind = "video" if (file.content_type or "").startswith("video") else \
            "audio" if (file.content_type or "").startswith("audio") else "image"
        tid = core.add_take(conn, episode=cut["code"], cut_id=cut_id, kind=kind, agent_note=note,
                            created_by="human")
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(await file.read())
        core.attach_file(conn, tid, Path(tmp.name), file.filename)
        return {"take_id": tid}


@app.post("/api/takes/{take_id}/select")
def select(take_id: int):
    with db.session() as conn:
        core.select_take(conn, take_id)
    return {"ok": True}


class ReviewIn(BaseModel):
    target_type: str
    target_id: int
    verdict: str = "修正"
    comment: str = ""
    tags: list[str] = []
    score: int | None = None
    region: dict | None = None
    image: str | None = None     # 印を描いたまま止めた画面（data URL）


@app.post("/api/reviews")
def add_review(r: ReviewIn):
    with db.session() as conn:
        d = r.model_dump()
        return {"id": core.add_review(conn, image_data=d.pop("image"), **d)}


@app.get("/api/reviews")
def reviews(episode: str | None = None, status: str | None = None, by: str | None = None):
    with db.session() as conn:
        return core.list_reviews(conn, episode, status, by)


class StatusIn(BaseModel):
    status: str


@app.patch("/api/reviews/{rid}")
def review_status(rid: int, s: StatusIn):
    with db.session() as conn:
        core.set_review_status(conn, rid, s.status)
    return {"ok": True}


class CompareIn(BaseModel):
    take_ids: list[int]
    winner_take_id: int | None = None
    reason: str = ""
    axes: dict = {}


@app.post("/api/comparisons")
def compare(c: CompareIn):
    with db.session() as conn:
        return {"id": core.add_comparison(conn, **c.model_dump())}


@app.get("/api/takes")
def takes(ids: str):
    id_list = [int(i) for i in ids.split(",") if i]
    with db.session() as conn:
        rows = db.rows(conn.execute(
            f"SELECT t.*, c.cut, c.panel FROM takes t LEFT JOIN cuts c ON c.id=t.cut_id "
            f"WHERE t.id IN ({','.join('?' * len(id_list))})", id_list))
    return sorted(rows, key=lambda t: id_list.index(t["id"]))


@app.get("/api/learnings")
def learnings():
    with db.session() as conn:
        return db.rows(conn.execute("SELECT * FROM learnings ORDER BY status='proposed' DESC, id DESC"))


class StoryIn(BaseModel):
    theme: str | None = None
    story_flow: str | None = None


class EditIn(BaseModel):
    field: str
    value: str | list | None = None


@app.patch("/api/episodes/{code}/story")
def story_edit(code: str, s_: StoryIn):
    """シーン整理のいちばん上（この話の芯・物語の流れ）を監督が直す。"""
    with db.session() as conn:
        core.set_story(conn, code, actor="human", **s_.model_dump(exclude_none=True))
    return {"ok": True}


@app.post("/api/episodes/{code}/scenes/{scode}/edit")
def scene_edit(code: str, scode: str, e: EditIn):
    """シーン整理の欄を監督がその場で直す（直した欄は正）。"""
    with db.session() as conn:
        return core.edit_by_human(conn, code, scode, e.field, e.value)


@app.get("/api/episodes/{code}/art")
def art_view(code: str):
    with db.session() as conn:
        return {"orders": art.orders(conn, code), "materials": art.materials(conn, code),
                "note_fields": art.NOTE_FIELDS, "uses": art.USES}


@app.get("/api/agents")
def agents_list():
    """AI の接続（ログインしているか）と、裏の AI の様子・役。"""
    from . import agents_auth
    st = staff.settings()
    agents = runner.status()
    for k, v in st.get("agents", {}).items():     # その AI がどのアカウントでログインしているか（claude-b は別の置き場所）
        au = agents_auth.agent_status(v.get("command", ""))
        agents[k].update(tool=au.get("tool"), installed=au.get("installed"), logged_in=au.get("logged_in"),
                         account=au.get("detail", ""), config_dir=au.get("config_dir", ""))
    return {"tools": agents_auth.all_status(), "agents": agents, "run_agents": st.get("rules", {}).get("run_agents", True),
            "roles": {k: v.get("name", k) for k, v in st.get("roles", {}).items()}, "assign": st.get("assign", {})}


@app.post("/api/agents/check")
def agents_check():
    """ログインの状態を調べ直す（覚えていた結果を捨てる）。"""
    from . import agents_auth
    agents_auth._CACHE.clear()
    return {"ok": True}


@app.post("/api/agents/{agent}/login-as")
def agents_login_as(agent: str):
    """その AI のアカウントでログインを始める（claude-b は CLAUDE_CONFIG_DIR の置き場所に入る）。"""
    from . import agents_auth
    a = staff.settings().get("agents", {}).get(agent)
    if not a:
        raise HTTPException(404, f"{agent} という AI はいません")
    tool, d = agents_auth.of_agent(a.get("command", ""))
    runner.wake(agent)
    return agents_auth.login(tool, d)


class AssignIn(BaseModel):
    assign: dict = {}
    labels: dict = {}


@app.put("/api/staff/assign")
def staff_assign(a: AssignIn):
    """役の割り振り（どの役をどの AI がやるか）と AI の呼び名を、画面から AIスタッフ.json に書く。"""
    d = staff.settings()
    agents = d.get("agents", {})
    for role, who in a.assign.items():
        if role not in d.get("roles", {}):
            raise HTTPException(400, f"「{role}」という役はありません")
        if who and who not in agents:
            raise HTTPException(400, f"「{who}」という AI はいません")
        d.setdefault("assign", {})[role] = who
    for k, label in a.labels.items():
        if k in agents and label.strip():
            agents[k]["label"] = label.strip()
    staff.STAFF_FILE.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    runner.wake()
    return {"ok": True, "assign": d["assign"]}


class QueueIn(BaseModel):
    action: str          # stop（中止）/ delete（消す）/ up / down / top


@app.post("/api/queue/{kind}/{qid}")
def queue_act(kind: str, qid: int, q: QueueIn):
    """順番待ちの操作。kind は request（仕事）か slot（会議の枠）。"""
    with db.session() as conn:
        if kind == "slot":
            s = db.one(conn.execute("SELECT * FROM round_slots WHERE id=?", (qid,)))
            if not s:
                raise HTTPException(404, "見つかりません")
            if q.action in ("stop", "delete"):
                if s["status"] == "claimed" and s["agent"]:
                    runner.stop(s["agent"])
                db.update(conn, "round_slots", qid, {"status": "cancelled"})
            return {"ok": True}
        r = db.one(conn.execute("SELECT * FROM requests WHERE id=?", (qid,)))
        if not r:
            raise HTTPException(404, "見つかりません")
        if q.action in ("stop", "delete"):
            if r["status"] == "claimed" and r["claimed_by"]:
                runner.stop(r["claimed_by"])
            db.update(conn, "requests", qid, {"status": "cancelled" if q.action == "stop" else "deleted"})
            return {"ok": True}
        opened = core.list_requests(conn, "open")
        ids = [x["id"] for x in opened]
        if qid not in ids:
            raise HTTPException(400, "作業中のものは並べ替えられません")
        i = ids.index(qid)
        ids.pop(i)
        ids.insert(0 if q.action == "top" else max(0, i - 1) if q.action == "up" else min(len(ids), i + 1), qid)
        for n, x in enumerate(ids):
            conn.execute("UPDATE requests SET prio=? WHERE id=?", (n, x))
    return {"ok": True}


class ResolvedIn(BaseModel):
    resolved: int


@app.patch("/api/errors/{eid}")
def errors_resolve(eid: int, r: ResolvedIn):
    with db.session() as conn:
        db.update(conn, "agent_runs", eid, {"resolved": r.resolved})
    return {"ok": True}


@app.exception_handler(Exception)
async def _record_error(request, exc):
    """ツール自身のエラーも「進み具合 → エラー」に残す（どの画面の、何で起きたか）。"""
    import traceback
    from fastapi.responses import JSONResponse
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))[-3000:]
    try:
        with db.session() as conn:
            ep, stage = runner.stage_of_path(request.url.path)
            db.insert(conn, "agent_runs", {"agent": "月灯スタジオ（ツール）", "kind": "tool", "started_at": db.now(), "ended_at": db.now(),
                                           "status": "error", "command": f"{request.method} {request.url.path}", "error": tb,
                                           "episode": ep, "stage": stage})
    except Exception:
        pass
    return JSONResponse({"detail": f"{type(exc).__name__}: {exc}"}, status_code=500)


@app.get("/api/progress")
def progress():
    """進み具合：動いている AI と、その場の流れ・順番待ち・最近の記録・きょうの使用量。"""
    with db.session() as conn:
        return runner.progress(conn)


@app.get("/api/errors")
def errors():
    """エラーの一覧と、そのまま貼れる報告文（開発の Claude に渡す）。"""
    with db.session() as conn:
        runs = db.rows(conn.execute("SELECT * FROM agent_runs WHERE status='error' ORDER BY id DESC LIMIT 50"))
    import platform
    report = ["月灯スタジオのエラー報告", f"- PC：{platform.platform()} / Python {platform.python_version()}", ""]
    for r in runs[:10]:
        report += [f"## #{r['id']} {r.get('episode') or ''} {r.get('stage') or ''}でエラー：{r['agent']}（{r['kind']}） {r['started_at']}〜{r['ended_at']}", f"コマンド：{r['command'][:300]}",
                   "エラー：", r["error"][:1500], ""]
    return {"runs": runs, "report": "\n".join(report), "health": _health(runs)}


def _health(runs: list[dict]) -> list[dict]:
    """いま何が使えて、何が使えないか。"""
    from . import agents_auth
    st = staff.settings()
    out = [{"name": "月灯スタジオ（この画面）", "ok": True, "detail": "動いています"}]
    for k, v in st.get("agents", {}).items():
        au = agents_auth.agent_status(v.get("command", ""))
        ok = bool(au.get("installed") and au.get("logged_in"))
        bad = [r for r in runs if r["agent"] == k and not r.get("resolved")]
        out.append({"name": v.get("label", k), "ok": ok and not bad,
                    "detail": ("ログイン中：" + (au.get("detail") or "") if ok else "使えません：" + ("入っていません" if not au.get("installed") else "ログインしていません"))
                              + (f"／未対応のエラー {len(bad)} 件" if bad else "")})
    on = st.get("rules", {}).get("run_agents", True)
    out.append({"name": "裏で AI を自動で動かす", "ok": on, "detail": "入っています" if on else "止めています"})
    tool_bad = sorted({f"{r.get('episode') or ''} {r.get('stage') or ''}".strip() for r in runs if r["kind"] == "tool" and not r.get("resolved")})
    out.append({"name": "画面の機能", "ok": not tool_bad, "detail": "問題なし" if not tool_bad else "エラーが残っている所：" + "、".join(tool_bad)})
    return out


@app.post("/api/agents/{tool}/login")
def agents_login(tool: str):
    from . import agents_auth
    runner.wake()          # ログインし直したら、休ませていた AI をすぐ起こす
    return agents_auth.login(tool)


@app.post("/api/agents/wake")
def agents_wake():
    runner.wake()
    return {"ok": True}


class RunIn(BaseModel):
    run: bool


@app.post("/api/agents/run")
def agents_run(r: RunIn):
    """裏の AI を動かす／止める（AIスタッフ.json の rules.run_agents）。"""
    d = staff.settings()
    d.setdefault("rules", {})["run_agents"] = r.run
    staff.STAFF_FILE.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True}


@app.get("/api/agents/{agent}/log")
def agents_log(agent: str):
    p = config.DATA_DIR / "logs" / f"{agent}.log"
    return PlainTextResponse(p.read_text(encoding="utf-8", errors="replace")[-6000:] if p.exists() else "（まだ記録がありません）")


DOC_DIRS = {"00_正本": "正本・決定ログ", "01_シリーズ": "シリーズの方針", "04_制作ルール": "制作ルール", "06_設定": "キャラ・舞台の設定",
            "07_資料": "監督が入れた資料"}


@app.get("/api/docs")
def docs_list():
    """AI が読む資料（vault）。フォルダごと。"""
    out = []
    for d, label in DOC_DIRS.items():
        base = config.VAULT_DIR / d
        files = sorted(p for p in base.rglob("*") if p.is_file() and not p.name.startswith(".")) if base.exists() else []
        out.append({"dir": d, "label": label, "files": [{"name": str(p.relative_to(base)), "path": f"{d}/{p.relative_to(base).as_posix()}",
                                                         "size": p.stat().st_size, "text": p.suffix.lower() in (".md", ".txt", ".json")}
                                                        for p in files]})
    return out


@app.get("/api/docs/read")
def docs_read(path: str):
    p = (config.VAULT_DIR / path).resolve()
    if config.VAULT_DIR.resolve() not in p.parents:
        raise HTTPException(400, "vault の外は読めません")
    return PlainTextResponse(p.read_text(encoding="utf-8", errors="replace"))


@app.post("/api/docs/upload")
async def docs_upload(files: list[UploadFile] = File(...), note: str = Form("")):
    """AI に読んでほしい資料を入れる（vault の 07_資料）。Word は文字にしておく。制作進行が読んで、関係する所に反映する。"""
    base = config.VAULT_DIR / "07_資料"
    base.mkdir(parents=True, exist_ok=True)
    saved = []
    for f in files:
        data = await f.read()
        name = Path(f.filename or "資料").name
        dest = base / name
        dest.write_bytes(data)
        if dest.suffix.lower() == ".docx":
            (base / (dest.stem + ".md")).write_text(episodes_mod.docx_text(dest), encoding="utf-8")
            saved.append(f"07_資料/{dest.stem}.md")
        saved.append(f"07_資料/{name}")
    with db.session() as conn:
        rid = core.add_request(conn, f"[資料] 監督が資料を入れた：{'、'.join(saved)}。読んで、作品の知識（正本・設定・制作ルール）や各話の作業に関係する所を挙げ、"
                                     f"反映が要るものは監督にチャットか2択で確かめる。" + (f"監督のひとこと：{note}" if note else "") + " 終わったら request-done")
        db.update(conn, "requests", rid, {"role": "まとめ"})
    return {"saved": saved, "request": rid}


@app.get("/api/library")
def library_list():
    with db.session() as conn:
        return art.library(conn)


@app.get("/api/library/kinds")
def library_kinds():
    return art.LIB_KINDS


@app.post("/api/library")
async def library_add(files: list[UploadFile] = File(...), hint: str = Form(""), order_id: int | None = Form(None), kind: str = Form("")):
    """素材庫に入れる（画像を落とすだけ）。何の素材かと注意書きは、制作進行の AI が画像を見て書く。"""
    tmp_files = []
    try:
        for f in files:
            suffix = Path(f.filename or "x.png").suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(await f.read())
            tmp_files.append((Path(tmp.name), f.filename or tmp.name))
        with db.session() as conn:
            return art.add_library(conn, tmp_files, hint, order_id, kind)
    finally:
        for p_, _ in tmp_files:
            p_.unlink(missing_ok=True)


class AssetIn(BaseModel):
    name: str | None = None
    kind: str | None = None
    hint: str | None = None
    active: int | None = None


@app.patch("/api/library/{aid}")
def library_edit(aid: int, a: AssetIn):
    with db.session() as conn:
        db.update(conn, "assets", aid, a.model_dump(exclude_none=True))
    return {"ok": True}


class LinkIn(BaseModel):
    asset_id: int


@app.post("/api/art/orders/{oid}/link")
def art_link(oid: int, l: LinkIn):
    with db.session() as conn:
        art.link(conn, oid, l.asset_id, by="human")
    return {"ok": True}


class ScriptIn(BaseModel):
    text: str


class NoteIn(BaseModel):
    anchor: str
    note: str


@app.get("/api/episodes/{code}/script")
def script_get(code: str):
    with db.session() as conn:
        return scriptdoc.read(conn, code)


@app.put("/api/episodes/{code}/script")
def script_put(code: str, s_: ScriptIn):
    with db.session() as conn:
        return scriptdoc.save(conn, code, s_.text)


@app.post("/api/episodes/{code}/script/notes")
def script_note(code: str, n: NoteIn):
    with db.session() as conn:
        return {"id": scriptdoc.add_note(conn, code, n.anchor, n.note)}


@app.delete("/api/script/notes/{nid}")
def script_note_del(nid: int):
    with db.session() as conn:
        conn.execute("DELETE FROM script_notes WHERE id=?", (nid,))
    return {"ok": True}


@app.post("/api/episodes/{code}/art/plan")
def art_plan(code: str):
    with db.session() as conn:
        return art.plan(conn, code)


@app.post("/api/episodes/{code}/art/deliver")
async def art_deliver(code: str, file: UploadFile = File(...), kind: str = Form("bg"), name: str = Form(""),
                      order_id: int | None = Form(None), scenes: str = Form(""), use: str = Form("ref"), notes: str = Form("{}")):
    """監督がレンダー・撮処理した素材を渡す（どのコマに使うかと注意書きつき）。"""
    import tempfile
    suffix = Path(file.filename or "x.png").suffix or ".png"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
    try:
        with db.session() as conn:
            return art.deliver(conn, code, Path(tmp.name), kind, name, order_id, [s for s in scenes.split(",") if s],
                               use, json.loads(notes or "{}"))
    finally:
        Path(tmp.name).unlink(missing_ok=True)


class OrderIn(BaseModel):
    status: str


@app.patch("/api/art/orders/{oid}")
def art_order_status(oid: int, o: OrderIn):
    with db.session() as conn:
        db.update(conn, "art_orders", oid, {"status": o.status})
    return {"ok": True}


class DecideIn(BaseModel):
    approve: bool
    rule_text: str | None = None


@app.post("/api/learnings/{lid}")
def decide(lid: int, d: DecideIn):
    with db.session() as conn:
        core.decide_learning(conn, lid, d.approve, d.rule_text)
    return {"ok": True}


@app.get("/api/brief", response_class=PlainTextResponse)
def brief(episode: str | None = None):
    with db.session() as conn:
        return context.build(conn, episode)


@app.post("/api/episodes/{code}/export")
def export(code: str):
    with db.session() as conn:
        return core.export_timeline(conn, code)


@app.get("/api/events")
def events(limit: int = 50):
    with db.session() as conn:
        rows = db.rows(conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)))
    for r in rows:
        r["payload"] = json.loads(r.pop("payload_json") or "{}")
    return rows


# ---- 設計・予算・手直し・ライブ ----

class EpisodeIn(BaseModel):
    title: str | None = None
    target_seconds: float | None = None
    budget_credits: float | None = None
    deadline: str | None = None
    stage: str | None = None


@app.patch("/api/episodes/{code}")
def patch_episode(code: str, e: EpisodeIn):
    with db.session() as conn:
        ep = db.episode_by_code(conn, code)
        db.update(conn, "episodes", ep["id"], e.model_dump(exclude_none=True))
        db.log(conn, "human", "update_episode", {"episode": code, **e.model_dump(exclude_none=True)})
    return {"ok": True}


@app.get("/api/episodes/{code}/scenes")
def scenes(code: str):
    with db.session() as conn:
        return core.scenes(conn, code)


class SceneIn(BaseModel):
    status: str | None = None
    target_seconds: float | None = None
    blocking: str | None = None
    purpose: str | None = None
    change_before: str | None = None
    change_after: str | None = None
    turn: str | None = None
    beats: list[dict] | None = None        # 展開カーブで監督が高さ（level）や山場（peak）を動かしたとき


class BlockingIn(BaseModel):
    frames: list[dict]
    plan: str = ""
    by: str = "human"
    note: str = ""


class ChoiceIn(BaseModel):
    episode: str
    question: str
    options: list[str]
    scene: str = ""
    about: str = ""
    why: str = ""
    created_by: str = "agent"


class AnswerIn(BaseModel):
    pick: str
    note: str = ""
    keep: bool = False


class DecideIn(BaseModel):
    verdict: str            # adopt / keep / other
    note: str = ""


@app.get("/api/episodes/{code}/overview")
def ep_overview(code: str):
    with db.session() as conn:
        return overview.overview(conn, code)


@app.get("/api/episodes/{code}/versions")
def versions_list(code: str, status: str = "open"):
    with db.session() as conn:
        return versions.list_versions(conn, code, status)


@app.get("/api/versions/{vid}/compare")
def versions_compare(vid: int):
    with db.session() as conn:
        return versions.compare(conn, vid)


@app.post("/api/versions/{vid}/decide")
def versions_decide(vid: int, d: DecideIn):
    with db.session() as conn:
        return versions.decide(conn, vid, d.verdict, d.note)


class ChatIn(BaseModel):
    text: str
    episode: str = ""


class ActIn(BaseModel):
    message: int
    index: int


@app.get("/api/chat")
def chat_list(after: int = 0):
    with db.session() as conn:
        return {**chat.history(conn, after), "agents": runner.status()}


@app.post("/api/chat")
def chat_send(c: ChatIn):
    """監督 → 制作進行。返事は裏で Claude（この PC の Claude Code）が書く。画面は /api/chat を見て待つ。"""
    with db.session() as conn:
        return {"id": chat.send(conn, c.text.strip(), c.episode)}


@app.post("/api/chat/act")
def chat_act(a: ActIn):
    with db.session() as conn:
        return {"message": chat.act(conn, a.message, a.index)}


@app.post("/api/episodes/{code}/reset")
def episode_reset(code: str):
    """話数を空に戻す（枠は残る。脚本は 03_脚本/前の版 へ）。"""
    with db.session() as conn:
        episodes_mod.reset(conn, code)
    return {"ok": True}


@app.post("/api/episodes/new")
async def episode_new(file: UploadFile = File(...), code: str = Form(""), title: str = Form(""), target: float = Form(180)):
    """新しい話数：脚本（md/txt/pdf/docx）か字コンテ（xlsx）を落とすだけ。あとは制作進行が下書きから進める。"""
    suffix = Path(file.filename or "x.md").suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
    try:
        with db.session() as conn:
            return episodes_mod.create(conn, code, title, target, Path(tmp.name), file.filename or "script.md")
    finally:
        Path(tmp.name).unlink(missing_ok=True)


class DirectIn(BaseModel):
    verdict: str            # ok / redo
    note: str = ""


@app.get("/api/episodes/{code}/scenes/{scode}/segments")
def scene_segments(code: str, scode: str):
    """シーンを上映順に（いまの絵・動画で）。監督が映像会議の結論と一緒に見る。"""
    with db.session() as conn:
        return versions.segments(conn, code, scode, None)


@app.get("/api/episodes/{code}/flows")
def flows_list(code: str):
    with db.session() as conn:
        return {"flows": pipeline.flows(conn, code), "stages": pipeline.STAGES}


@app.post("/api/episodes/{code}/flows/{scene}/direct")
def flows_direct(code: str, scene: str, d: DirectIn):
    """監督の判断：映像会議の結論と映像を見て、OK か、こうしたい（一言）か。"""
    with db.session() as conn:
        return pipeline.direct(conn, code, scene, d.verdict, d.note)


class RoundIn(BaseModel):
    episode: str
    target: str = ""
    note: str = ""


@app.get("/api/rounds")
def rounds_list(episode: str | None = None, status: str = "open,closed"):
    with db.session() as conn:
        return staff.list_rounds(conn, episode, status)


@app.post("/api/rounds")
def rounds_open(r: RoundIn):
    """監督が「AI スタッフで検討して」を押したとき。監督が開く会議は回数の上限にかからない。"""
    with db.session() as conn:
        return {"id": staff.open_round(conn, r.episode, r.target, note=r.note, created_by="human")}


@app.get("/api/staff")
def staff_settings():
    return staff.settings()


@app.get("/api/plans")
def plans_list():
    return direction.plans()


@app.get("/api/episodes/{code}/scenes/{scode}/blocking")
def blocking_get(code: str, scode: str):
    with db.session() as conn:
        return direction.get_blocking(conn, code, scode)


@app.put("/api/episodes/{code}/scenes/{scode}/blocking")
def blocking_put(code: str, scode: str, b: BlockingIn):
    """配置図。監督が動かしたら、何が変わったかをレビューとしても積む（エージェントが次に読む）。"""
    with db.session() as conn:
        r = direction.set_blocking(conn, code, scode, b.frames, b.plan, b.by, b.note)
        if b.by == "human" and (r["diff"] or b.note):
            ep = db.episode_by_code(conn, code)
            core.add_review(conn, target_type="episode", target_id=ep["id"], verdict="修正", tags=["配置"],
                            comment=f"[配置図 {scode}] 監督が動かした：{' ／ '.join(r['diff']) or '―'}"
                                    + (f"　ひとこと：{b.note}" if b.note else ""))
        return r


@app.get("/api/choices")
def choices_list(episode: str | None = None, status: str = "open,answered"):
    with db.session() as conn:
        return direction.list_choices(conn, episode, status)


@app.post("/api/choices")
def choices_add(c: ChoiceIn):
    with db.session() as conn:
        return {"id": direction.ask(conn, c.episode, c.question, c.options, c.scene, c.about, c.why, c.created_by)}


@app.post("/api/choices/{cid}/answer")
def choices_answer(cid: int, a: AnswerIn):
    with db.session() as conn:
        return direction.answer(conn, cid, a.pick, a.note, a.keep)


@app.get("/api/episodes/{code}/scenes/{scode}/script")
def scene_script(code: str, scode: str):
    with db.session() as conn:
        return core.scene_script(conn, code, scode)


@app.patch("/api/episodes/{code}/scenes/{scode}")
def patch_scene(code: str, scode: str, s_: SceneIn):
    with db.session() as conn:
        core.set_scene(conn, code, scode, actor="human", **s_.model_dump(exclude_none=True))
        if s_.status == "approved":
            pipeline.start(conn, code, scode)      # 承認されたら、字コンテ会議へ（工程の自動進行）
    return {"ok": True}


@app.get("/api/episodes/{code}/awaiting")
def awaiting(code: str):
    with db.session() as conn:
        return core.awaiting_human(conn, code)


@app.get("/api/episodes/{code}/usage")
def usage(code: str):
    with db.session() as conn:
        ep = db.episode_by_code(conn, code)
        return {"spent": core.spent(conn, ep["id"]), "budget": ep["budget_credits"],
                "by_kind": db.rows(conn.execute(
                    "SELECT provider, kind, COUNT(*) n, SUM(credits) credits FROM usage WHERE episode_id=? "
                    "GROUP BY provider, kind", (ep["id"],)))}


class CutIn(BaseModel):
    seconds: float | None = None
    dialogue: str | None = None
    edit_memo: str | None = None


@app.patch("/api/cuts/{cut_id}")
def patch_cut(cut_id: int, c: CutIn):
    with db.session() as conn:
        core.update_cut(conn, cut_id, "human", **c.model_dump(exclude_none=True))
    return {"ok": True}


@app.get("/api/stream")
async def stream():
    """events を Server-Sent Events で流す。画面はこれで、エージェントがいま何をしているかを表示する。"""
    import asyncio

    async def gen():
        with db.session() as conn:
            last = conn.execute("SELECT COALESCE(MAX(id),0) FROM events").fetchone()[0]
        while True:
            with db.session() as conn:
                rows = db.rows(conn.execute("SELECT * FROM events WHERE id>? ORDER BY id", (last,)))
            for r in rows:
                last = r["id"]
                yield f"data: {json.dumps(r, ensure_ascii=False)}\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(gen(), media_type="text/event-stream")


# ---- 仮Vコン・ショット ----

@app.get("/api/episodes/{code}/playlist")
def playlist(code: str):
    with db.session() as conn:
        items = core.playlist(conn, code)
    for it in items:
        it["cut"].pop("takes", None)
    return items


@app.get("/api/episodes/{code}/shots")
def shots_list(code: str):
    from . import seedance
    with db.session() as conn:
        return seedance.list_shots(conn, code)


@app.patch("/api/episodes/{code}/shots/{scode}")
def shot_status(code: str, scode: str, s_: StatusIn):
    with db.session() as conn:
        ep = db.episode_by_code(conn, code)
        conn.execute("UPDATE shots SET status=? WHERE episode_id=? AND code=?", (s_.status, ep["id"], scode))
        db.log(conn, "human", "shot_status", {"episode": code, "shot": scode, "status": s_.status})
    return {"ok": True}


# ---- Premiere の中のパネルとのやりとり ----

@app.get("/api/premiere/commands")
def pr_pending(host: str = "premiere"):
    from . import premiere
    with db.session() as conn:
        return premiere.pending(conn, host)


class PrResult(BaseModel):
    ok: bool
    result: dict = {}


@app.post("/api/premiere/commands/{qid}/result")
def pr_result(qid: int, r: PrResult):
    from . import premiere
    with db.session() as conn:
        premiere.finish(conn, qid, r.ok, r.result)
        if r.ok and r.result.get("rendered") and r.result.get("take"):   # AE の書き出しをテイクに
            premiere.ae_rendered(conn, int(r.result["take"]), r.result["rendered"])
    return {"ok": True}


@app.post("/api/premiere/state/{code}")
def pr_state(code: str, state: dict):
    from . import premiere
    with db.session() as conn:
        return premiere.receive_state(conn, code, state)


@app.get("/api/episodes/{code}/stats")
def ep_stats(code: str):
    with db.session() as conn:
        return core.stats(conn, code)


# ---- 依頼 ----

class RequestIn(BaseModel):
    text: str
    episode: str = ""


@app.get("/api/requests")
def requests_list(status: str = "open,claimed,done"):
    with db.session() as conn:
        return list(reversed(core.list_requests(conn, status)))


@app.post("/api/requests")
def requests_add(r: RequestIn):
    with db.session() as conn:
        return {"id": core.add_request(conn, r.text, r.episode)}


@app.patch("/api/requests/{rid}")
def requests_cancel(rid: int, s_: StatusIn):
    with db.session() as conn:
        db.update(conn, "requests", rid, {"status": s_.status})
    return {"ok": True}


# ---- 外から使うときの鍵（TSUKI_TOKEN を設定したときだけ。自分の PC の中からは不要） ----

@app.middleware("http")
async def token_guard(request, call_next):
    import os
    from fastapi.responses import JSONResponse
    token = os.environ.get("TSUKI_TOKEN", "")
    local = request.client and request.client.host in ("127.0.0.1", "::1", "localhost")
    if token and not local:
        given = request.headers.get("authorization", "").removeprefix("Bearer ") or request.query_params.get("token", "")
        if given != token:
            return JSONResponse({"detail": "token が必要です"}, status_code=401)
    return await call_next(request)


@app.post("/api/adobe/hello")
def adobe_hello(info: dict):
    """Premiere / After Effects のパネルが起動したときの知らせ（アプリと版）。"""
    with db.session() as conn:
        db.log(conn, "human", "adobe_hello", info)
    return {"ok": True}


@app.get("/api/handoff", response_class=PlainTextResponse)
def handoff(request_id: int = 0, mode: str = "local"):
    """別の Claude に渡す依頼文。mode=local（この PC の Claude Code / Desktop）/ remote（クラウドの Claude）。"""
    import os
    with db.session() as conn:
        r = db.one(conn.execute("SELECT * FROM requests WHERE id=?", (request_id,))) if request_id else None
    what = f"依頼 #{r['id']}（{r['episode']}）：{r['text']}" if r else "月灯スタジオの未着手の依頼"
    common = ("あなたは『月灯りスピークイージー』の制作エージェントです。作るのはあなた、見るのは監督です。\n"
              f"{what} を進めてください。\n"
              "手順：brief を読む → next_request で依頼を取る（agent には自分の名前）→ 作る → 監督に見せる前に self_review → "
              "テイクとして登録 → finish_request に結果（テイク番号・残っていること）を書く。\n"
              "予算（1話5万円）と作り直しの上限で止まったら、迷っている点を書いて監督に回してください。\n")
    if mode == "remote":
        url = os.environ.get("TSUKI_PUBLIC_URL", "https://<トンネルの URL>") .rstrip("/") + "/mcp"
        return (common + f"\n接続：MCP サーバー {url} （ヘッダー Authorization: Bearer <監督から受け取った鍵>）。\n"
                "作品の資料（vault）と手順はリポジトリ mastermarisa71-arch/claudeclowdtest の CLAUDE.md と "
                ".claude/skills/tsukiakari-studio/SKILL.md にあります。")
    return (common + "\n場所：このリポジトリ（月灯スタジオが起動していること）。CLAUDE.md と "
            ".claude/skills/tsukiakari-studio/SKILL.md に従い、MCP の tsukiakari-studio の道具か "
            "python studio/cli.py を使ってください。")


@app.get("/api/cuts/{cut_id}/script")
def cut_script(cut_id: int):
    with db.session() as conn:
        return core.script_snippet(conn, cut_id)


@app.get("/api/episodes/{code}/marks")
def marks(code: str):
    with db.session() as conn:
        return core.episode_marks(conn, code)
