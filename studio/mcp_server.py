"""月灯スタジオの MCP サーバー。どの Claude からでも、同じ道具で制作を進められるようにする。

- 自分の PC の Claude Code / Claude Desktop：stdio で起動（リポジトリの .mcp.json に登録済み）
    python studio/mcp_server.py
- クラウドの Claude（claude.ai のコネクタ、別の PC のエージェント）：HTTP で起動して、トンネルで公開する
    set TSUKI_TOKEN=長いランダムな文字列
    python studio/mcp_server.py --http --port 8766      → https://<トンネル>/mcp  （Authorization: Bearer <TSUKI_TOKEN>）

道具は CLI（studio/cli.py）と同じ操作。エージェントは最初に `brief` と `next_request` を呼ぶ。
"""
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mcp.server.fastmcp import FastMCP, Image  # noqa: E402

from studio.backend import context, core, db, direction, premiere, seedance, shots, storyboard  # noqa: E402

mcp = FastMCP("tsukiakari-studio", instructions=(
    "『月灯りスピークイージー』の制作ツール。作るのはエージェント、見るのは監督。"
    "最初に brief(episode) を読み、next_request で監督の依頼を取る。作ったものは必ずテイクとして登録し、"
    "監督に見せる前に self_review する。手順の詳細は brief に書かれた資料と .claude/skills/tsukiakari-studio/SKILL.md。"))


def _s():
    db.init()
    return db.session()


def _episode_id(conn, code: str) -> int:
    ep = db.episode_by_code(conn, code)
    if not ep:
        raise ValueError(f"{code} がありません")
    return ep["id"]


# ---- 読む ----

@mcp.tool()
def brief(episode: str = "") -> str:
    """作業前に必ず読む：読むべき資料、話数の状態（設計・予算）、承認済みルール、未対応レビュー、比較の好み、最近の流れ。"""
    with _s() as conn:
        return context.build(conn, episode or None)


@mcp.tool()
def episodes() -> list[dict]:
    """話数の一覧（コマ数・尺・採用数・未対応レビュー）。"""
    with _s() as conn:
        return core.episodes(conn)


@mcp.tool()
def cuts(episode: str) -> list[dict]:
    """字コンテのコマ（上映順）。テイクは id・段階・採用だけ返す。"""
    with _s() as conn:
        out = []
        for c in core.episode_cuts(conn, episode)["cuts"]:
            c["takes"] = [{"id": t["id"], "kind": t["kind"], "tier": t["tier"], "selected": t["selected"],
                           "status": t["status"]} for t in c["takes"]]
            out.append(c)
        return out


@mcp.tool()
def reviews(episode: str = "", status: str = "open,working") -> list[dict]:
    """レビュー（監督とセルフレビュー）。status は open,working,proposed,resolved をカンマ区切り。"""
    with _s() as conn:
        return core.list_reviews(conn, episode or None, status)


@mcp.tool()
def stats(episode: str) -> dict:
    """工程ごとの回数・費用（円）・生成の待ち時間・監督のレビューまでの時間。"""
    with _s() as conn:
        return core.stats(conn, episode)


# ---- 依頼 ----

@mcp.tool()
def next_request(agent: str, request_id: int = 0) -> dict:
    """監督の依頼を1つ取る（agent は自分の名前、例「claude-cloud-1」）。取れなければ空。同じ依頼を二重に進めない。"""
    with _s() as conn:
        return core.claim_request(conn, agent, request_id or None) or {}


@mcp.tool()
def finish_request(request_id: int, result: str, status: str = "done") -> str:
    """依頼を終える。result に何をしたか（テイク番号・残っていること）を書く。"""
    with _s() as conn:
        core.finish_request(conn, request_id, result, status)
    return "ok"


# ---- 設計・ショット ----

@mcp.tool()
def set_scene(episode: str, scene: str, place: str = "", time: str = "", look: str = "", target_seconds: float = 0,
              purpose: str = "", emotion: str = "", blocking: str = "", cameras: str = "", props: str = "",
              change_before: str = "", change_after: str = "", turn: str = "",
              characters: list[dict] | None = None, beats: list[dict] | None = None,
              script_from: str = "", script_to: str = "") -> int:
    """シーン整理と設計。脚本を読んだら、字コンテより先にシーンごとに作り、監督の「シーン整理」で承認をもらう。
    change_before→change_after：このシーンで何が変わるか（状況・関係・気持ち）。turn：変わるきっかけ。
    characters：[{name, want（したいこと）, does（見える芝居）, inner（内心）, tension（1〜5）}]。
    beats：[{seconds, who, does, why, level（展開の高さ1〜5）, peak（山場なら名前）}] シーンの中の小さな区切り。script_from/script_to：脚本の範囲を一節で指す。
    ほかに狙い・目標尺・感情の流れ・立ち位置と動線・カメラ位置・小物。"""
    fields = {k: v for k, v in dict(place=place, time=time, look=look, purpose=purpose, emotion=emotion,
                                     blocking=blocking, cameras=cameras, props=props, change_before=change_before,
                                     change_after=change_after, turn=turn, characters=characters, beats=beats,
                                     script_from=script_from, script_to=script_to).items() if v}
    with _s() as conn:
        return core.set_scene(conn, episode, scene, target_seconds=target_seconds or None, **fields)


@mcp.tool()
def get_blocking(episode: str, scene: str) -> dict:
    """配置図：シーンの見取り図（名前のついた位置 spots と座標）と、区切りごとの立ち位置。text は言葉にしたもの。"""
    with _s() as conn:
        return direction.get_blocking(conn, episode, scene)


@mcp.tool()
def set_blocking(episode: str, scene: str, frames: list[dict], note: str = "") -> dict:
    """配置図の案を置く。frames=[{"beat": 0, "pos": {"あかね": [0.30, 0.34], …}}, …]（区切りごと、座標 0〜1）。
    監督は画面でコマを動かして直す。監督が動かした結果は「[配置図 S1] …」のレビューで届く。"""
    with _s() as conn:
        return direction.set_blocking(conn, episode, scene, frames, by="agent", note=note)


@mcp.tool()
def ask_director(episode: str, question: str, options: list[str], scene: str = "", about: str = "", why: str = "") -> int:
    """迷ったら、決めつけずに2択（3つまで）で監督に聞く。芝居・しぐさ・間・動線など。about はキャラ名。
    監督が選んだものは承認済みの好みとしてブリーフに載り、「キャラの決まり」にされたものはキャラのノートに書かれる。"""
    with _s() as conn:
        return direction.ask(conn, episode, question, options, scene, about, why)


@mcp.tool()
def list_choices(episode: str = "", status: str = "open,answered") -> list[dict]:
    """2択の一覧と監督の答え（answer, note, keep）。"""
    with _s() as conn:
        return direction.list_choices(conn, episode or None, status)


@mcp.tool()
def plan_shots(episode: str, target_seconds: float = 15, replace: bool = False) -> list[dict]:
    """ショット分けのたたき台（同じシーンで目安の秒数まで詰める）。このあと set_shot でつながりを見て分け直す。"""
    with _s() as conn:
        return seedance.plan_shots(conn, episode, target_seconds, replace)


@mcp.tool()
def set_shot(episode: str, shot: str, cuts: list[str], note: str = "") -> dict:
    """ショットに入れるコマを決める。cuts は ["S1-06", "S1-07②"] のように。1本30秒まで。"""
    with _s() as conn:
        return seedance.set_shot(conn, episode, shot, cuts, note)


@mcp.tool()
def list_shots(episode: str) -> list[dict]:
    """ショットの一覧（範囲・秒数・テイク）。"""
    with _s() as conn:
        out = []
        for sh in seedance.list_shots(conn, episode):
            sh["cuts"] = [f"{c['cut']}{c['panel']}" for c in sh["cuts"]]
            out.append(sh)
        return out


@mcp.tool()
def budget_plan(episode: str) -> dict:
    """ショットの秒数から1話の費用を見積もる（円）。"""
    from studio.backend import config
    with _s() as conn:
        ep = db.episode_by_code(conn, episode)
        secs = sum(min(config.SHOT_MAX_SECONDS, max(4, round(s["seconds"]))) for s in seedance.list_shots(conn, episode))
        draft = secs * 1.5 * core.estimate("hamster", "video", tier="draft")
        final = secs * 1.1 * core.estimate("hamster", "video", tier="final")
        return {"seconds": secs, "draft_yen": round(draft), "final_yen": round(final),
                "total_yen": round(draft + final + 2000), "budget_yen": ep["budget_credits"] or config.DEFAULT_BUDGET_YEN,
                "spent_yen": round(core.spent(conn, ep["id"]))}


# ---- 仮Vコン ----

@mcp.tool()
def board_prompt(episode: str, board: str) -> dict:
    """9コマ仮Vコンのシートの骨組み（日本語）と参照画像。plan は board-plan で先に作る。"""
    with _s() as conn:
        if not conn.execute("SELECT 1 FROM boards WHERE episode_id=?", (_episode_id(conn, episode),)).fetchone():
            storyboard.plan_boards(conn, episode)
        return storyboard.board_prompt(conn, episode, board)


@mcp.tool()
def board_shoot(episode: str, board: str, prompt: str, provider: str = "hamster", note: str = "") -> dict:
    """仕上げたプロンプトで9コマシートを生成する。出来上がったら board_split でコマに切る。"""
    with _s() as conn:
        b = storyboard.board_prompt(conn, episode, board)
        tid = core.generate(conn, episode=episode, cut_id=b["cut_ids"][0], kind="sheet", provider=provider,
                            prompt=prompt, refs=b["refs"], board_id=b["board_id"], agent_note=note or f"仮Vコン {board}")
        return db.one(conn.execute("SELECT id, status, error FROM takes WHERE id=?", (tid,)))


@mcp.tool()
def board_split(take_id: int) -> list[int]:
    """9コマシートをコマごとのテイクに切り出す。"""
    with _s() as conn:
        return storyboard.split_sheet(conn, take_id)


# ---- ドラフト・本番 ----

@mcp.tool()
def shot_brief(episode: str, shot: str, tier: str = "draft") -> dict:
    """Seedance 2.5 のプロンプトの骨組み・参照画像・秒数・足りない参照。英語に仕上げてから shot_shoot に渡す。"""
    with _s() as conn:
        sh = db.one(conn.execute("SELECT id FROM shots WHERE episode_id=? AND code=?", (_episode_id(conn, episode), shot)))
        return seedance.build_brief(conn, sh["id"], tier)


@mcp.tool()
def shot_shoot(episode: str, shot: str, prompt: str, provider: str = "hamster", note: str = "",
               parent_take_id: int = 0, fixes_review_ids: list[int] | None = None, force: bool = False) -> dict:
    """仕上げたプロンプトを点検して 480p ドラフトを作る。点検の指摘があれば送らずに返す（force で無視）。"""
    with _s() as conn:
        sh = db.one(conn.execute("SELECT * FROM shots WHERE episode_id=? AND code=?", (_episode_id(conn, episode), shot)))
        b = seedance.build_brief(conn, sh["id"], "draft")
        issues = seedance.lint(prompt, len(b["refs"]))
        if issues and not force:
            return {"sent": False, "issues": issues}
        try:
            tid = core.generate(conn, episode=episode, cut_id=json.loads(sh["cut_ids_json"])[0], kind="video",
                                provider=provider, model="seedance-2.5", prompt=prompt, refs=b["refs"],
                                params={"duration": b["duration"]}, tier="draft", shot_id=sh["id"],
                                parent_take_id=parent_take_id or None, fixes_review_ids=fixes_review_ids or [],
                                agent_note=note)
        except core.Blocked as e:
            return {"sent": False, "blocked": str(e)}
        return {"sent": True, **db.one(conn.execute("SELECT id, status, tier, error FROM takes WHERE id=?", (tid,)))}


@mcp.tool()
def contact_sheet(take_id: int, frames: int = 6) -> Image:
    """動画テイクから等間隔にフレームを抜いて並べた画像（セルフレビュー用。動画を丸ごと見ない）。"""
    with _s() as conn:
        t = db.one(conn.execute("SELECT kind, file_path FROM takes WHERE id=?", (take_id,)))
        from studio.backend import config
        path = shots.contact_sheet(conn, take_id, frames) if t["kind"] == "video" else str(config.MEDIA_DIR / t["file_path"])
    return Image(path=path)


@mcp.tool()
def review_image(review_id: int) -> Image:
    """監督が矢印や囲みを描いて止めた画面の画像。レビューのコメントと合わせて、どこをどう直すかを読む。"""
    from studio.backend import config
    with _s() as conn:
        r = db.one(conn.execute("SELECT attachment FROM reviews WHERE id=?", (review_id,)))
    if not r or not r["attachment"]:
        raise ValueError("このレビューには画像がありません")
    return Image(path=str(config.MEDIA_DIR / r["attachment"]))


@mcp.tool()
def self_review(take_id: int, checks: dict, comment: str = "") -> int:
    """監督に見せる前のセルフレビュー。checks は {"意図": true, "芝居": "だめな理由", ...}。true 以外があれば不合格。"""
    with _s() as conn:
        return core.self_review(conn, take_id, checks, comment)


@mcp.tool()
def respond_review(review_id: int, text: str, take_id: int = 0, status: str = "proposed") -> str:
    """監督のレビューに返答する（何をどう直したか／直せない理由）。"""
    with _s() as conn:
        core.respond_review(conn, review_id, text, take_id or None, status)
    return "ok"


@mcp.tool()
def promote(take_id: int) -> dict:
    """監督が採用したドラフトを入力に 1080p 本番を作る（声優の声があれば口を合わせる）。"""
    with _s() as conn:
        try:
            tid = shots.promote(conn, take_id, "final")
        except core.Blocked as e:
            return {"blocked": str(e)}
        return db.one(conn.execute("SELECT id, status, tier, error FROM takes WHERE id=?", (tid,)))


@mcp.tool()
def promote_all(episode: str) -> list[str]:
    """採用済みでまだ本番がないドラフトを順に 1080p にする。"""
    with _s() as conn:
        return shots.promote_all(conn, episode)


@mcp.tool()
def propose_rule(text: str, scope: str = "series", from_reviews: list[int] | None = None) -> int:
    """同じ種類の指摘が続いたら「次からのルール」を提案する。監督が承認したものだけが効く。"""
    with _s() as conn:
        return core.propose_learning(conn, text, scope, from_reviews or [])


# ---- Premiere / After Effects ----

@mcp.tool()
def premiere_build(episode: str, selected_only: bool = False) -> str:
    """Premiere のパネルにシーケンスを組ませる（ドラフトの段階から）。"""
    with _s() as conn:
        args = premiere.build_args(conn, episode, draft_ok=not selected_only)
        return f"queue #{premiere.enqueue(conn, episode, 'build', args)}"


@mcp.tool()
def premiere_state(episode: str) -> dict:
    """監督が Premiere で直した最後の状態と差分。続きを作る前に読む。監督の手直しは正。"""
    with _s() as conn:
        return premiere.last_state(conn, episode) or {}


@mcp.tool()
def premiere_marker(episode: str, at_seconds: float, comment: str) -> str:
    """Premiere のタイムラインにマーカー（監督への質問・メモ）を置く。"""
    with _s() as conn:
        return f"queue #{premiere.enqueue(conn, episode, 'marker', {'at': at_seconds, 'name': 'AI', 'comment': comment})}"


@mcp.tool()
def ae_comp(episode: str, take_id: int, texts: list[dict] | None = None, zoom_from: float = 0, zoom_to: float = 0,
            render: bool = False) -> str:
    """After Effects にコンポを作らせる。texts=[{"text":"チョコパン","x":0.5,"y":0.4,"t_in":0,"t_out":2}]、
    zoom は編集での小さな寄り引き（1.0→1.08 など）。render で書き出してテイクに戻す。"""
    zoom = {"from": zoom_from, "to": zoom_to} if zoom_to else {}
    with _s() as conn:
        args = premiere.ae_comp_args(conn, take_id, texts or [], zoom, render)
        return f"queue #{premiere.enqueue(conn, episode, 'comp', args, 'aftereffects')}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--http", action="store_true", help="HTTP で起動（クラウドの Claude から使うとき）")
    ap.add_argument("--port", type=int, default=8766)
    ap.add_argument("--host", default="127.0.0.1")
    a = ap.parse_args()
    if not a.http:
        mcp.run()
        return
    import uvicorn
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.responses import JSONResponse

    token = os.environ.get("TSUKI_TOKEN", "")
    if not token:
        print("TSUKI_TOKEN を設定してください（外から使うときの鍵）")
        sys.exit(2)

    class Guard(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            if request.headers.get("authorization", "") != f"Bearer {token}":
                return JSONResponse({"detail": "token が必要です"}, status_code=401)
            return await call_next(request)

    app = mcp.streamable_http_app()
    app.add_middleware(Guard)
    uvicorn.run(app, host=a.host, port=a.port)


if __name__ == "__main__":
    main()
