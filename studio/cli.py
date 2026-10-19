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
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from studio.backend import config, context, core, db, seedance, shots, storyboard  # noqa: E402
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
    for f in ("place", "time", "look", "purpose", "emotion", "blocking", "cameras", "props", "status"):
        p.add_argument(f"--{f}")
    p.add_argument("--target", type=float)
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
                      f" 【{r['verdict']}】[{r['tags']}] {r['comment']} {r['region_json']}"
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
                                                 "cameras", "props", "status")}
            print(core.set_scene(conn, a.episode, a.scene, target_seconds=a.target, **fields))
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
        elif a.cmd == "budget-plan":
            ep = db.episode_by_code(conn, a.episode)
            shs = seedance.list_shots(conn, a.episode)
            secs = sum(min(config.SHOT_MAX_SECONDS, max(4, round(s["seconds"]))) for s in shs)
            nb = conn.execute("SELECT COUNT(*) FROM boards WHERE episode_id=?", (ep["id"],)).fetchone()[0]
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
            print("  単価は config.COST_TABLE / TIERS の仮の値。実際の単価に直すと正確になる")
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
