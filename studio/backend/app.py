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

from . import config, context, core, db

db.init()
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
        return core.episodes(conn)


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


@app.patch("/api/episodes/{code}/scenes/{scode}")
def patch_scene(code: str, scode: str, s_: SceneIn):
    with db.session() as conn:
        core.set_scene(conn, code, scode, **s_.model_dump(exclude_none=True))
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
