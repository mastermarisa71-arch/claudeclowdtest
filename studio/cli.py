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
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from studio.backend import context, core, db  # noqa: E402
from studio.backend.importers import jikonte  # noqa: E402


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
                tid = core.generate(conn, **kw)
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


if __name__ == "__main__":
    main()
