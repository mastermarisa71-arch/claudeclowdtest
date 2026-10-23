"""エージェント（Claude Code）が使う操作口。サーバーが動いていなくても DB を直接読み書きする。

リポジトリ直下で：  python studio/cli.py <コマンド> ...
  brief [EP01]                       作業前に読むブリーフ（資料・ルール・未対応レビュー・好み）
  import-jikonte EP09 <xlsx> --version 4分版
  episodes / cuts EP09
  reviews [--episode EP09] [--status open,working]
  take-add EP09 --cut 12 --kind image --prompt-file p.txt --file out.png --parent 3 --fixes 5,6 --note "…"
  generate EP09 --cut 12 --kind sheet --provider hamster --prompt-file p.txt --refs a.png,b.png
  respond 5 "左右の配置を直した。#31 を見てください" --take 31
  propose-rule "あかねの手は常にトレーを両手で" --scope character:あかね --from 5,8
  export EP09                        Premiere 用 XML と ffconcat を書き出す
  bible                              キャラ・舞台の設定を vault の 06_設定 に書き出す（シート更新後に再実行）
  episode-set EP09 --target 180 --budget 600 --deadline 2026-10-22 --stage 設計
  scene-set EP09 S1 --place 店内 --look B --target 35 --purpose "…" --blocking "…" --cameras A,C
  scenes EP09
  scene-set EP09 S1 --before "…" --after "…" --turn "…" --char "あかね|したいこと|すること|内心|4" --beat "6|あかね|…|…"
  blocking EP09 S1 [--file frames.json]          配置図（区切りごとの立ち位置）を見る／案を置く
  ask EP09 "あかねの打ち明け方" --opt "目を合わせない" --opt "正面から" --scene S1 --about あかね   監督に2択で聞く
  choices [EP09] [--status open]                 2択の一覧と答え
  scene-sheet EP09 [--file sheet.json] [--md]    シーン整理（脚本と字コンテの間）を取り込む／vault に書き出す
  self-review 31 --checks '{"意図":true,"芝居":"まひるがシェイカーを振っている"}' --comment "…"
  awaiting EP09                      AI が通して、監督がまだ見ていないテイク
  usage EP09
  cut-edit 12 --seconds 1.5          尺・台詞の手直し
  bg-render EP09 --blend 月灯り店内.blend --camera CAM_A [--cut 12] [--asset-name 店内:A] [-- --lens 28]
  contact 31                                    動画テイクから6フレームを並べた画像を作る（セルフレビュー用）
  attach 31 out.mp4                             外で作った結果（手作業の生成など）をテイクに付ける
  asset-add character あかね <設定資料.png>      参照素材の棚に足す（character/bg/layout/prop）
  assets [character]
  prompt-build 12 [--tier draft] [--bg 店内:A] [--out p.txt]   字コンテ・設計・設定・参照素材からプロンプトを組む
  shoot 12 --provider hamster [--kind video]     組んだプロンプトで 480p ドラフトを作る
  promote 31 [--to final]                       監督が採用したドラフトを入力に 1080p 本番
  promote-all EP09                              採用済みでまだ本番がないドラフトを順に 1080p に
  board-plan EP09 / board-prompt EP09 SB01 / board-shoot EP09 SB01 [--prompt-file] / board-split 31
                                                9コマの仮Vコン（ドラフトの前の確認段）
  shot-plan EP09 [--target 15] [--replace]       マルチショットの分け方のたたき台（1本30秒まで）
  shot-set EP09 SH03 S1-04 S1-05 --note "落として拾うまで1本で"
  shots EP09
  shot-brief EP09 SH03 [--out p.txt]             Seedance 2.5 の骨組み（ASSETS/SUMMARY/TIMELINE/…）
  shot-shoot EP09 SH03 --prompt-file p.txt       仕上げたプロンプトを点検して 480p ドラフトを作る
  budget-plan EP09                               ショットの秒数から1話の費用を見積もる
  stats EP09                                     工程ごとの回数・費用・生成の待ち時間・監督のレビューまでの時間
  audio-add EP09 --cut 12 --file v.mp3 --role voice|actor|sfx|music [--speaker あかね]
  pr-build EP09 [--selected]                     Premiere のパネルにシーケンスを組ませる（ドラフトの段階でも可）
  pr-read EP09                                   Premiere の今のタイムラインを読み取らせる
  pr-state EP09                                  監督が Premiere で直した差分（最後に届いた状態）
  pr-replace EP09 SH03 --take 52                 同じ位置・長さのまま新しいテイクに差し替える
  pr-marker EP09 --at 12.5 --comment "ここの溜めはどうしますか"
  adobe-status                                   Premiere / After Effects のパネルがつながっているか、版と命令の結果
  adobe-test [--host premiere|aftereffects]      パネルに動作確認の命令を送る
  ae-comp EP09 --take 52 [--text "チョコパン@0.5,0.4"] [--zoom 1.0:1.08] [--render]
                                                After Effects にコンポを作らせる（文字合成・寄り引き・書き出し）
  ae-read EP09                                   After Effects の今のコンポを読み取らせる
  requests [--all] / request-add "…" [--episode EP09] / request-claim [--id 3] --agent 名前 / request-done 3 "結果"
                                                監督の依頼（どの Claude が取っても同じ形で進める）
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from studio.backend import config, context, core, db, premiere, seedance, shots, storyboard  # noqa: E402
from studio.backend.importers import bible, jikonte  # noqa: E402


def _ids(s: str | None) -> list[int]:
    return [int(x) for x in s.split(",") if x] if s else []


def main(argv=None):
    ap = argparse.ArgumentParser(prog="studio")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("brief"); p.add_argument("episode", nargs="?")
    p = sub.add_parser("import-jikonte"); p.add_argument("episode"); p.add_argument("path")
    p.add_argument("--version", default="v1")
    sub.add_parser("episodes")
    p = sub.add_parser("cuts"); p.add_argument("episode")
    p = sub.add_parser("reviews"); p.add_argument("--episode"); p.add_argument("--status", default="open,working")

    for name in ("take-add", "generate"):
        p = sub.add_parser(name)
        p.add_argument("episode"); p.add_argument("--cut", type=int); p.add_argument("--kind", default="image")
        p.add_argument("--provider", default="manual"); p.add_argument("--model", default="")
        p.add_argument("--prompt", default=""); p.add_argument("--prompt-file")
        p.add_argument("--refs", default=""); p.add_argument("--params", default="{}")
        p.add_argument("--parent", type=int); p.add_argument("--fixes", default="")
        p.add_argument("--note", default=""); p.add_argument("--file")

    p = sub.add_parser("respond"); p.add_argument("review", type=int); p.add_argument("text")
    p.add_argument("--take", type=int); p.add_argument("--status", default="proposed")
    p = sub.add_parser("propose-rule"); p.add_argument("text"); p.add_argument("--scope", default="series")
    p.add_argument("--from", dest="src", default=""); p.add_argument("--vault-target", default="")
    p = sub.add_parser("export"); p.add_argument("episode")
    sub.add_parser("bible")
    p = sub.add_parser("episode-set"); p.add_argument("episode"); p.add_argument("--title")
    p.add_argument("--test", action="store_true", help="テストの回（予算を超えても止めない）")
    p.add_argument("--no-test", action="store_true")
    p.add_argument("--target", type=float); p.add_argument("--budget", type=float)
    p.add_argument("--deadline"); p.add_argument("--stage")
    p = sub.add_parser("scene-set"); p.add_argument("episode"); p.add_argument("scene")
    for f in ("place", "time", "look", "purpose", "emotion", "blocking", "cameras", "props", "status",
              "before", "after", "turn", "from", "to"):
        p.add_argument(f"--{f}")
    p.add_argument("--target", type=float)
    p.add_argument("--char", action="append", default=[],
                   help="名前|したいこと|すること|内心|温度1-5（キャラごとに繰り返す）")
    p.add_argument("--beat", action="append", default=[], help="秒|誰|すること|なぜ（区切りごとに繰り返す）")
    p = sub.add_parser("blocking"); p.add_argument("episode"); p.add_argument("scene")
    p.add_argument("--file", help='区切りごとの位置の JSON：[{"beat":0,"pos":{"あかね":[0.3,0.34]}}]（座標 0〜1、配置図.json の見取り図）')
    p.add_argument("--note", default="")
    p = sub.add_parser("ask"); p.add_argument("episode"); p.add_argument("question")
    p.add_argument("--opt", action="append", required=True, help="選択肢（2つ以上、繰り返す）")
    p.add_argument("--scene", default=""); p.add_argument("--about", default="", help="キャラ名（決まりにするときの行き先）")
    p.add_argument("--why", default="")
    p = sub.add_parser("choices"); p.add_argument("episode", nargs="?"); p.add_argument("--status", default="open,answered")
    p = sub.add_parser("scene-sheet"); p.add_argument("episode")
    p.add_argument("--file", help="シーン整理の JSON（[{scene, purpose, change_before, …, characters, beats}]）を取り込む")
    p.add_argument("--md", action="store_true", help="vault の 02_各話/EPxx/EPxx_シーン整理.md に書き出す")
    p = sub.add_parser("scenes"); p.add_argument("episode")
    p = sub.add_parser("self-review"); p.add_argument("take", type=int); p.add_argument("--checks", required=True)
    p.add_argument("--comment", default="")
    p = sub.add_parser("awaiting"); p.add_argument("episode")
    p = sub.add_parser("usage"); p.add_argument("episode")
    p = sub.add_parser("cut-edit"); p.add_argument("cut", type=int); p.add_argument("--seconds", type=float)
    p.add_argument("--dialogue"); p.add_argument("--edit-memo")
    p = sub.add_parser("bg-render"); p.add_argument("episode"); p.add_argument("--blend", required=True)
    p.add_argument("--camera", required=True); p.add_argument("--cut", type=int); p.add_argument("--note", default="")
    p.add_argument("--asset-name", default=""); p.add_argument("extra", nargs="*")
    p = sub.add_parser("contact"); p.add_argument("take", type=int); p.add_argument("--frames", type=int, default=6)
    p = sub.add_parser("attach"); p.add_argument("take", type=int); p.add_argument("file")
    p = sub.add_parser("asset-add"); p.add_argument("kind"); p.add_argument("name"); p.add_argument("file")
    p.add_argument("--note", default="")
    p = sub.add_parser("assets"); p.add_argument("kind", nargs="?")
    p = sub.add_parser("prompt-build"); p.add_argument("cut", type=int); p.add_argument("--tier", default="draft")
    p.add_argument("--bg"); p.add_argument("--out")
    p = sub.add_parser("shoot"); p.add_argument("cut", type=int); p.add_argument("--provider", default="hamster")
    p.add_argument("--kind", default="video"); p.add_argument("--model", default=""); p.add_argument("--bg")
    p.add_argument("--parent", type=int); p.add_argument("--fixes", default=""); p.add_argument("--note", default="")
    p.add_argument("--extra-prompt", default="", help="レビューを受けて足す指示（組んだプロンプトの末尾に足す）")
    p = sub.add_parser("promote"); p.add_argument("take", type=int); p.add_argument("--to", default="final",
                                                                                   choices=["upscale", "final"])
    p.add_argument("--provider"); p.add_argument("--note", default="")
    p = sub.add_parser("promote-all"); p.add_argument("episode"); p.add_argument("--provider")
    p = sub.add_parser("board-plan"); p.add_argument("episode"); p.add_argument("--replace", action="store_true")
    p = sub.add_parser("board-prompt"); p.add_argument("episode"); p.add_argument("board"); p.add_argument("--out")
    p = sub.add_parser("board-shoot"); p.add_argument("episode"); p.add_argument("board")
    p.add_argument("--provider", default="hamster"); p.add_argument("--prompt-file"); p.add_argument("--note", default="")
    p = sub.add_parser("board-split"); p.add_argument("take", type=int)
    p = sub.add_parser("shot-plan"); p.add_argument("episode"); p.add_argument("--target", type=float)
    p.add_argument("--replace", action="store_true")
    p = sub.add_parser("shot-set"); p.add_argument("episode"); p.add_argument("shot"); p.add_argument("cuts", nargs="+")
    p.add_argument("--note", default="")
    p = sub.add_parser("shots"); p.add_argument("episode")
    p = sub.add_parser("shot-brief"); p.add_argument("episode"); p.add_argument("shot"); p.add_argument("--out")
    p.add_argument("--tier", default="draft")
    p = sub.add_parser("shot-shoot"); p.add_argument("episode"); p.add_argument("shot")
    p.add_argument("--provider", default="hamster"); p.add_argument("--model", default="seedance-2.5")
    p.add_argument("--prompt-file"); p.add_argument("--parent", type=int); p.add_argument("--fixes", default="")
    p.add_argument("--note", default=""); p.add_argument("--force", action="store_true", help="点検の指摘を無視して送る")
    p = sub.add_parser("budget-plan"); p.add_argument("episode")
    p = sub.add_parser("stats"); p.add_argument("episode")
    p = sub.add_parser("audio-add"); p.add_argument("episode"); p.add_argument("--cut", type=int, required=True)
    p.add_argument("--file", required=True); p.add_argument("--role", default="voice",
                                                            choices=["voice", "actor", "sfx", "music"])
    p.add_argument("--speaker", default=""); p.add_argument("--note", default="")
    p = sub.add_parser("pr-build"); p.add_argument("episode"); p.add_argument("--selected", action="store_true")
    p = sub.add_parser("pr-read"); p.add_argument("episode")
    p = sub.add_parser("pr-state"); p.add_argument("episode")
    p = sub.add_parser("pr-replace"); p.add_argument("episode"); p.add_argument("clip"); p.add_argument("--take", type=int, required=True)
    sub.add_parser("adobe-status")
    p = sub.add_parser("adobe-test"); p.add_argument("--host", default="premiere", choices=["premiere", "aftereffects"])
    p = sub.add_parser("ae-comp"); p.add_argument("episode"); p.add_argument("--take", type=int, required=True)
    p.add_argument("--text", action="append", default=[], help="文字@x,y（0〜1）。複数可")
    p.add_argument("--zoom", default="", help="from:to 例 1.0:1.08"); p.add_argument("--render", action="store_true")
    p = sub.add_parser("ae-read"); p.add_argument("episode")
    p = sub.add_parser("requests"); p.add_argument("--all", action="store_true")
    p = sub.add_parser("request-add"); p.add_argument("text"); p.add_argument("--episode", default="")
    p = sub.add_parser("request-claim"); p.add_argument("--id", type=int); p.add_argument("--agent", required=True)
    p = sub.add_parser("request-done"); p.add_argument("id", type=int); p.add_argument("result")
    p.add_argument("--status", default="done", choices=["done", "cancelled", "open"])
    p = sub.add_parser("pr-marker"); p.add_argument("episode"); p.add_argument("--at", type=float, required=True)
    p.add_argument("--comment", default=""); p.add_argument("--name", default="AI")

    a = ap.parse_args(argv)
    db.init()
    with db.session() as conn:
        if a.cmd == "brief":
            print(context.build(conn, a.episode))
        elif a.cmd == "import-jikonte":
            print(json.dumps(jikonte.import_file(conn, a.episode, a.path, a.version), ensure_ascii=False))
        elif a.cmd == "episodes":
            for e in core.episodes(conn):
                print(f"{e['code']}  コマ{e['n_cuts']}  {e['seconds']}秒  テイク{e['n_takes']}  "
                      f"採用{e['n_selected']}/{e['n_cuts']}  未対応レビュー{e['n_open']}")
        elif a.cmd == "cuts":
            for c in core.episode_cuts(conn, a.episode)["cuts"]:
                sel = next((t["id"] for t in c["takes"] if t["selected"]), "-")
                print(f"[{c['id']}] {c['cut']}{c['panel']} {c['seconds']}s 採用#{sel} "
                      f"テイク{len(c['takes'])} | {c['picture'][:40]} | {c['dialogue'][:30]}")
        elif a.cmd == "reviews":
            for r in core.list_reviews(conn, a.episode, a.status):
                print(f"#{r['id']} [{r['status']}] {r['cut'] or ''}{r['panel'] or ''} {r['target_type']}:{r['target_id']}"
                      f" 【{r['verdict']}】[{r['tags']}] {r['comment']} {core.describe_region(r['region_json'] or '')}"
                      + (f"\n    画像：{r['attachment']}" if r.get("attachment") else "")
                      + (f"\n    ↳ agent: {r['agent_response']}" if r["agent_response"] else ""))
        elif a.cmd in ("take-add", "generate"):
            prompt = Path(a.prompt_file).read_text(encoding="utf-8") if a.prompt_file else a.prompt
            kw = dict(episode=a.episode, cut_id=a.cut, kind=a.kind, provider=a.provider, model=a.model,
                      prompt=prompt, refs=[r for r in a.refs.split(",") if r], params=json.loads(a.params),
                      parent_take_id=a.parent, fixes_review_ids=_ids(a.fixes), agent_note=a.note)
            if a.cmd == "generate":
                try:
                    tid = core.generate(conn, **kw)
                except core.Blocked as e:
                    print(f"止めました：{e}")
                    return 2
            else:
                tid = core.add_take(conn, **kw)
                if a.file:
                    core.attach_file(conn, tid, Path(a.file))
            print(json.dumps(db.one(conn.execute("SELECT id,status,error,file_path FROM takes WHERE id=?", (tid,))),
                             ensure_ascii=False))
        elif a.cmd == "respond":
            core.respond_review(conn, a.review, a.text, a.take, a.status)
            print("ok")
        elif a.cmd == "propose-rule":
            print(core.propose_learning(conn, a.text, a.scope, _ids(a.src), a.vault_target))
        elif a.cmd == "export":
            print(json.dumps(core.export_timeline(conn, a.episode), ensure_ascii=False, indent=1))
        elif a.cmd == "bible":
            print("\n".join(bible.write_all()))
        elif a.cmd == "episode-set":
            ep = db.get_or_create_episode(conn, a.episode)
            data = {k: v for k, v in {"title": a.title, "target_seconds": a.target, "budget_credits": a.budget,
                                      "deadline": a.deadline, "stage": a.stage,
                                      "is_test": 1 if a.test else 0 if a.no_test else None}.items() if v is not None}
            db.update(conn, "episodes", ep["id"], data)
            db.log(conn, "agent", "update_episode", {"episode": a.episode, **data})
            print(json.dumps(db.episode_by_code(conn, a.episode), ensure_ascii=False))
        elif a.cmd == "scene-set":
            fields = {f: getattr(a, f) for f in ("place", "time", "look", "purpose", "emotion", "blocking",
                                                 "cameras", "props", "status", "turn")}
            fields.update(change_before=a.before, change_after=a.after, script_from=getattr(a, "from"), script_to=a.to)
            if a.char:
                keys = ("name", "want", "does", "inner", "tension")
                fields["characters"] = [dict(zip(keys, x.split("|"))) for x in a.char]
            if a.beat:
                fields["beats"] = [dict(zip(("seconds", "who", "does", "why"), x.split("|"))) for x in a.beat]
            print(core.set_scene(conn, a.episode, a.scene, target_seconds=a.target, **fields))
        elif a.cmd == "blocking":
            from studio.backend import direction
            if a.file:
                r = direction.set_blocking(conn, a.episode, a.scene, json.loads(Path(a.file).read_text(encoding="utf-8")),
                                           by="agent", note=a.note)
                print("\n".join(r["after"]))
            else:
                b = direction.get_blocking(conn, a.episode, a.scene)
                print(f"見取り図：{b['plan'] or '（場所に合う図がない）'}　位置：{', '.join(b['plan_data'].get('spots', {}))}")
                print("\n".join(b["text"]) or "（まだ配置がない）")
        elif a.cmd == "ask":
            from studio.backend import direction
            print(direction.ask(conn, a.episode, a.question, a.opt, a.scene, a.about, a.why))
        elif a.cmd == "choices":
            from studio.backend import direction
            for c in direction.list_choices(conn, a.episode, a.status):
                ans = f" → {c['answer']} {c['note']}{'（決まり）' if c['keep'] else ''}" if c["status"] == "answered" else ""
                print(f"#{c['id']} [{c['status']}] {c['episode']} {c['scene']} {c['about']}：{c['question']}　"
                      + " ／ ".join(f"{o['label']} {o['text']}" for o in c["options"]) + ans)
        elif a.cmd == "scene-sheet":
            if a.file:
                for i, x in enumerate(json.loads(Path(a.file).read_text(encoding="utf-8")), 1):
                    x = dict(x)
                    code = x.pop("scene")
                    if "target" in x:
                        x["target_seconds"] = x.pop("target")
                    core.set_scene(conn, a.episode, code, **x)
                print(f"{i} シーンを取り込みました")
            if a.md:
                out = config.VAULT_DIR / "02_各話" / a.episode / f"{a.episode}_シーン整理.md"
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(core.scene_sheet_md(conn, a.episode) + "\n", encoding="utf-8")
                print(out)
            if not a.file and not a.md:
                print(core.scene_sheet_md(conn, a.episode))
        elif a.cmd == "scenes":
            sc = core.scenes(conn, a.episode)
            total = sum(s["target_seconds"] or 0 for s in sc["scenes"])
            print(f"{a.episode} 目標 {sc['episode']['target_seconds']}秒 / シーン合計 {total}秒 / 使用 {sc['spent']:.0f}")
            for s in sc["scenes"]:
                print(f"{s['code']} [{s['status']}] {s['target_seconds']}秒（今 {s['actual_seconds']}） {s['place']} "
                      f"{s['look']} {s['cameras']} | {s['purpose']}\n    動線：{s['blocking']}")
        elif a.cmd == "self-review":
            print(core.self_review(conn, a.take, json.loads(a.checks), a.comment))
        elif a.cmd == "awaiting":
            for t in core.awaiting_human(conn, a.episode):
                print(f"#{t['id']} {t['cut']}{t['panel']} {t['kind']} {t['file_path']} | AI：{t['ai_comment']}")
        elif a.cmd == "usage":
            ep = db.episode_by_code(conn, a.episode)
            print(f"使用 {core.spent(conn, ep['id']):,.0f}円 / 予算 {(ep['budget_credits'] or config.DEFAULT_BUDGET_YEN):,.0f}円"
                  + ("（テストの回）" if ep["is_test"] else ""))
            for r in db.rows(conn.execute("SELECT provider, kind, COUNT(*) n, SUM(credits) c FROM usage "
                                          "WHERE episode_id=? GROUP BY provider, kind", (ep["id"],))):
                print(f"  {r['provider']}/{r['kind']} {r['n']}回 {r['c']:,.0f}円")
        elif a.cmd == "cut-edit":
            core.update_cut(conn, a.cut, "agent", **{k: v for k, v in {"seconds": a.seconds, "dialogue": a.dialogue,
                                                                         "edit_memo": a.edit_memo}.items() if v is not None})
            print("ok")
        elif a.cmd == "contact":
            print(shots.contact_sheet(conn, a.take, a.frames))
        elif a.cmd == "attach":
            print(core.attach_file(conn, a.take, Path(a.file)))
        elif a.cmd == "asset-add":
            print(shots.add_asset(conn, a.kind, a.name, a.file, note=a.note))
        elif a.cmd == "assets":
            for x in shots.assets(conn, a.kind):
                print(f"[{x['id']}] {x['kind']} {x['name']} {x['file_path']} {x['note']}")
        elif a.cmd == "prompt-build":
            b = shots.build(conn, a.cut, a.tier, a.bg)
            if a.out:
                Path(a.out).write_text(b["prompt"], encoding="utf-8")
            print(b["prompt"] if not a.out else a.out)
            print("\n--- 参照画像（この順で渡す）")
            for i, (r, l) in enumerate(zip(b["refs"], b["ref_labels"]), 1):
                print(f"@image{i} {l}  {r}")
            if b["missing"]:
                print("--- 足りない参照：" + "、".join(b["missing"]))
        elif a.cmd == "shoot":
            b = shots.build(conn, a.cut, "draft", a.bg)
            cut = db.one(conn.execute("SELECT e.code FROM cuts c JOIN episodes e ON e.id=c.episode_id WHERE c.id=?",
                                      (a.cut,)))
            try:
                tid = core.generate(conn, episode=cut["code"], cut_id=a.cut, kind=a.kind, provider=a.provider,
                                    model=a.model, prompt=b["prompt"] + (f"\n【直し】{a.extra_prompt}" if a.extra_prompt else ""),
                                    refs=b["refs"], params={"duration": b["seconds"]}, tier="draft",
                                    parent_take_id=a.parent, fixes_review_ids=_ids(a.fixes), agent_note=a.note)
            except core.Blocked as e:
                print(f"止めました：{e}")
                return 2
            print(json.dumps(db.one(conn.execute("SELECT id,status,tier,error FROM takes WHERE id=?", (tid,))),
                             ensure_ascii=False))
            if b["missing"]:
                print("足りない参照：" + "、".join(b["missing"]))
        elif a.cmd == "promote-all":
            print("\n".join(shots.promote_all(conn, a.episode, a.provider)) or "対象なし")
        elif a.cmd == "board-plan":
            for b in storyboard.plan_boards(conn, a.episode, a.replace):
                print(f"{b['code']} {b['panels']}コマ {b['range']}")
        elif a.cmd == "board-prompt":
            b = storyboard.board_prompt(conn, a.episode, a.board)
            if a.out:
                Path(a.out).write_text(b["prompt"], encoding="utf-8")
            print(b["prompt"] if not a.out else a.out)
            print("--- 参照：" + "／".join(b["ref_labels"]) + ("\n--- 足りない参照：" + "、".join(b["missing"]) if b["missing"] else ""))
        elif a.cmd == "board-shoot":
            b = storyboard.board_prompt(conn, a.episode, a.board)
            prompt = Path(a.prompt_file).read_text(encoding="utf-8") if a.prompt_file else b["prompt"]
            try:
                tid = core.generate(conn, episode=a.episode, cut_id=b["cut_ids"][0], kind="sheet", provider=a.provider,
                                    prompt=prompt, refs=b["refs"], board_id=b["board_id"], tier="",
                                    agent_note=a.note or f"仮Vコン {a.board}")
            except core.Blocked as e:
                print(f"止めました：{e}")
                return 2
            print(json.dumps(db.one(conn.execute("SELECT id,status,error FROM takes WHERE id=?", (tid,))), ensure_ascii=False))
        elif a.cmd == "board-split":
            print(storyboard.split_sheet(conn, a.take))
        elif a.cmd == "shot-plan":
            for sh in seedance.plan_shots(conn, a.episode, a.target, a.replace):
                print(f"{sh['code']} {sh['seconds']}秒 {sh['cuts']}" + ("  ※30秒超" if sh["over"] else ""))
        elif a.cmd == "shot-set":
            print(json.dumps(seedance.set_shot(conn, a.episode, a.shot, a.cuts, a.note), ensure_ascii=False))
        elif a.cmd == "shots":
            for sh in seedance.list_shots(conn, a.episode):
                tk = " ".join(f"#{t['id']}{t['tier'][:1]}{'*' if t['selected'] else ''}" for t in sh["takes"])
                print(f"{sh['code']} [{sh['status']}] {sh['seconds']}秒 {sh['range']} {len(sh['cuts'])}コマ | {sh['note']} | {tk}")
        elif a.cmd in ("shot-brief", "shot-shoot"):
            ep = db.episode_by_code(conn, a.episode)
            sh = db.one(conn.execute("SELECT * FROM shots WHERE episode_id=? AND code=?", (ep["id"], a.shot)))
            b = seedance.build_brief(conn, sh["id"], getattr(a, "tier", "draft"))
            if a.cmd == "shot-brief":
                if a.out:
                    Path(a.out).write_text(b["prompt"], encoding="utf-8")
                print(b["prompt"] if not a.out else a.out)
                print(f"\n--- {b['duration']}秒 / 参照 {len(b['refs'])}枚：" + "、".join(b["ref_labels"]))
                for k, v in (("足りない参照", b["missing"]), ("上限で外した参照", b["dropped"])):
                    if v:
                        print(f"--- {k}：" + "、".join(v))
                return 0
            prompt = Path(a.prompt_file).read_text(encoding="utf-8") if a.prompt_file else b["prompt"]
            issues = seedance.lint(prompt, len(b["refs"]))
            if issues and not a.force:
                print("点検で止めました：\n- " + "\n- ".join(issues))
                return 2
            try:
                tid = core.generate(conn, episode=a.episode, cut_id=json.loads(sh["cut_ids_json"])[0], kind="video",
                                    provider=a.provider, model=a.model, prompt=prompt, refs=b["refs"],
                                    params={"duration": b["duration"]}, tier="draft", shot_id=sh["id"],
                                    parent_take_id=a.parent, fixes_review_ids=_ids(a.fixes), agent_note=a.note)
            except core.Blocked as e:
                print(f"止めました：{e}")
                return 2
            print(json.dumps(db.one(conn.execute("SELECT id,status,tier,error FROM takes WHERE id=?", (tid,))),
                             ensure_ascii=False))
        elif a.cmd == "stats":
            r = core.stats(conn, a.episode)
            print(f"{a.episode} 使用 {r['spent']:,}円 / 予算 {r['budget']:,.0f}円" + ("（テストの回）" if r["is_test"] else ""))
            print(f"  {'工程':<10} 回数 失敗 採用  費用      動画秒  生成待ち(平均/合計 分)  レビューまで(平均 分)")
            for s_ in r["stages"]:
                print(f"  {s_['stage']:<10} {s_['n']:>4} {s_['failed']:>4} {s_['adopted']:>4} {s_['yen']:>7,}円 {s_['video_seconds']:>6}"
                      f"   {s_['gen_wait_min'] or '-'} / {s_['gen_wait_total_min']}            {s_['review_wait_min'] or '-'}")
        elif a.cmd == "audio-add":
            print(core.add_audio(conn, episode=a.episode, cut_id=a.cut, src=Path(a.file), role=a.role,
                                 speaker=a.speaker, note=a.note))
        elif a.cmd == "pr-build":
            args = premiere.build_args(conn, a.episode, draft_ok=not a.selected)
            print(f"キュー #{premiere.enqueue(conn, a.episode, 'build', args)}：映像 {len(args['video'])} / 音 {len(args['audio'])} / {args['total']}秒")
        elif a.cmd == "pr-read":
            print(f"キュー #{premiere.enqueue(conn, a.episode, 'read', {})}（パネルが読み取ると pr-state で見られる）")
        elif a.cmd == "pr-state":
            st = premiere.last_state(conn, a.episode)
            if not st:
                print("まだ届いていません")
            else:
                print(f"{st['ts']} {st['actor']} {st['state'].get('note', '')}")
                for d in st["diff"]:
                    print(f"  {d['clip']}: {d['before']}秒 → {d['after']}秒 {d.get('note', '')}")
                print(f"  映像クリップ {len(st['state'].get('video', []))} / 音 {len(st['state'].get('audio', []))}")
        elif a.cmd == "pr-replace":
            t = db.one(conn.execute("SELECT file_path FROM takes WHERE id=?", (a.take,)))
            print(premiere.enqueue(conn, a.episode, "replace", {"name": a.clip,
                                                                "path": str((config.MEDIA_DIR / t["file_path"]).resolve())}))
        elif a.cmd == "adobe-status":
            for e in db.rows(conn.execute("SELECT * FROM events WHERE action='adobe_hello' ORDER BY id DESC LIMIT 4")):
                print(f"{e['ts']} つながった：{e['payload_json']}")
            for q in db.rows(conn.execute("SELECT * FROM premiere_queue ORDER BY id DESC LIMIT 8")):
                print(f"  #{q['id']} {q['host']} {q['command']} [{q['status']}] {q['result_json'][:120]}")
        elif a.cmd == "adobe-test":
            print(f"キュー #{premiere.enqueue(conn, '', 'hello', {}, a.host)}（パネルが取ると adobe-status に結果が出る）")
        elif a.cmd == "ae-comp":
            texts = []
            for tx in a.text:
                body, _, pos = tx.partition("@")
                x, _, y = pos.partition(",")
                texts.append({"text": body, "x": float(x or 0.5), "y": float(y or 0.5)})
            zoom = {}
            if a.zoom:
                f, _, t = a.zoom.partition(":")
                zoom = {"from": float(f), "to": float(t)}
            args = premiere.ae_comp_args(conn, a.take, texts, zoom, a.render)
            print(f"キュー #{premiere.enqueue(conn, a.episode, 'comp', args, 'aftereffects')}")
        elif a.cmd == "ae-read":
            print(f"キュー #{premiere.enqueue(conn, a.episode, 'read', {}, 'aftereffects')}")
        elif a.cmd == "requests":
            for r in core.list_requests(conn, "open,claimed,done,cancelled" if a.all else "open,claimed"):
                print(f"#{r['id']} [{r['status']}{'：' + r['claimed_by'] if r['claimed_by'] else ''}] {r['episode']} {r['text']}"
                      + (f"\n    → {r['result']}" if r["result"] else ""))
        elif a.cmd == "request-add":
            print(core.add_request(conn, a.text, a.episode))
        elif a.cmd == "request-claim":
            r = core.claim_request(conn, a.agent, a.id)
            print(json.dumps(r, ensure_ascii=False) if r else "取れる依頼はありません（ほかのエージェントが取った可能性）")
        elif a.cmd == "request-done":
            core.finish_request(conn, a.id, a.result, a.status)
            print("ok")
        elif a.cmd == "pr-marker":
            print(premiere.enqueue(conn, a.episode, "marker", {"at": a.at, "name": a.name, "comment": a.comment}))
        elif a.cmd == "budget-plan":
            ep = db.episode_by_code(conn, a.episode)
            shs = seedance.list_shots(conn, a.episode)
            secs = sum(min(config.SHOT_MAX_SECONDS, max(4, round(s["seconds"]))) for s in shs)
            nb = conn.execute("SELECT COUNT(*) FROM boards WHERE episode_id=?", (ep["id"],)).fetchone()[0]
            nb = nb or round(secs / 1.6 / 9)
            rows = [("仮Vコン（9コマシート）", nb * 1.3, core.estimate("hamster", "sheet")),
                    ("480p ドラフト（秒）", secs * 1.5, core.estimate("hamster", "video", tier="draft")),
                    ("1080p 本番（秒）", secs * 1.1, core.estimate("hamster", "video", tier="final")),
                    ("仮の声・効果音・劇伴（回）", 100, core.estimate("runway", "audio"))]
            total = 0
            print(f"{a.episode}：ショット {len(shs)}本 / 合計 {secs}秒（作り直し率：シート1.3・ドラフト1.5・本番1.1）")
            for name, n, unit in rows:
                total += n * unit
                print(f"  {name:<22} {n:7.0f} × {unit:6.1f}円 = {n * unit:9,.0f}円")
            budget = ep["budget_credits"] or config.DEFAULT_BUDGET_YEN
            print(f"  合計の見込み {total:,.0f}円 / 予算 {budget:,.0f}円" + ("（テストの回）" if ep["is_test"] else "")
                  + ("  ※超えます" if total > budget else ""))
            print("  動画は HAMSTER の 15秒の単価から換算（480p 250円・1080p 1,400円 / 15秒）。シートと音声は仮の値")
        elif a.cmd == "promote":
            try:
                tid = shots.promote(conn, a.take, a.to, a.provider, a.note)
            except core.Blocked as e:
                print(f"止めました：{e}")
                return 2
            print(json.dumps(db.one(conn.execute("SELECT id,status,tier,error FROM takes WHERE id=?", (tid,))),
                             ensure_ascii=False))
        elif a.cmd == "bg-render":
            tid = core.render_bg(conn, episode=a.episode, blend=a.blend, camera=a.camera, cut_id=a.cut,
                                 note=a.note, extra_args=a.extra, asset_name=a.asset_name)
            print(json.dumps(db.one(conn.execute("SELECT id,status,error,file_path FROM takes WHERE id=?", (tid,))),
                             ensure_ascii=False))


if __name__ == "__main__":
    sys.exit(main())
