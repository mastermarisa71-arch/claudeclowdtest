"""エージェントへの「ブリーフ」を組み立てる。

エージェントは作業の前に必ずこれを読む：
1. 作品の正（vault のどのファイルを読むべきか）
2. 承認済みのルール（learnings）
3. まだ対応していないレビュー（どのテイクの、どこが、なぜ）
4. 比較で分かった好み（AよりBが良い、その理由）
5. 前回までの流れ（最近のイベント）
"""
import json

from . import config, db

CANON_FILES = [
    "00_正本/通し設計_正本.md",
    "00_正本/決定ログ.md",
    "00_正本/未決リスト.md",
    "04_制作ルール/生成と字コンテのルール.md",
    "01_シリーズ/映像の作り方の方針.md",
    "03_脚本/いまの版/INDEX.md",
]


def _region(r: dict) -> str:
    if not r.get("region_json"):
        return ""
    g = json.loads(r["region_json"])
    if "t_in" in g:
        return f"（{g['t_in']:.1f}〜{g.get('t_out', g['t_in']):.1f}秒）"
    return f"（画面の x{g['x']:.2f} y{g['y']:.2f} 幅{g['w']:.2f} 高{g['h']:.2f}）"


def build(conn, episode_code: str | None = None) -> str:
    ep = db.episode_by_code(conn, episode_code) if episode_code else None
    out = ["# 月灯りスピークイージー 制作ブリーフ", ""]

    out += ["## 1. 先に読む資料（vault）"]
    for f in CANON_FILES:
        mark = "" if (config.VAULT_DIR / f).exists() else "（見つからない）"
        out.append(f"- {config.VAULT_DIR.name}/{f}{mark}")
    if ep:
        out.append(f"- {config.VAULT_DIR.name}/02_各話/{ep['code']}/ と 03_脚本/いまの版/{ep['code']}_脚本_いまの版.md")
    out.append("")

    out += ["## 2. 承認済みのルール（必ず守る）"]
    learned = db.rows(conn.execute("SELECT * FROM learnings WHERE status='approved' ORDER BY id"))
    out += [f"- [{l['scope']}] {l['rule_text']}" for l in learned] or ["- （まだなし）"]
    out.append("")

    where = "WHERE r.status IN ('open','working')" + (" AND r.episode_id=?" if ep else "")
    args = (ep["id"],) if ep else ()
    open_reviews = db.rows(conn.execute(f"""
        SELECT r.*, t.kind AS take_kind, t.prompt AS take_prompt, c.cut, c.panel
        FROM reviews r
        LEFT JOIN takes t ON r.target_type='take' AND t.id=r.target_id
        LEFT JOIN cuts c ON c.id = COALESCE(t.cut_id, CASE WHEN r.target_type='cut' THEN r.target_id END)
        {where} ORDER BY r.id""", args))
    out += [f"## 3. 未対応のレビュー（{len(open_reviews)}件）"]
    for r in open_reviews:
        where_s = f"{r['cut'] or ''}{r['panel'] or ''} " if r.get("cut") else ""
        out.append(f"- #{r['id']} {where_s}{r['target_type']}:{r['target_id']} 【{r['verdict']}】"
                   f"[{r['tags']}] {r['comment']}{_region(r)}")
    if not open_reviews:
        out.append("- （なし）")
    out.append("")

    comps = db.rows(conn.execute(
        "SELECT * FROM comparisons" + (" WHERE episode_id=?" if ep else "") + " ORDER BY id DESC LIMIT 20", args))
    out += ["## 4. 比較で分かった好み（新しい順）"]
    for c in comps:
        axes = json.loads(c["axes_json"] or "{}")
        axes_s = "、".join(f"{k}→#{v}" for k, v in axes.items())
        out.append(f"- テイク {json.loads(c['take_ids_json'])} → 勝ち #{c['winner_take_id']}"
                   f"{'（' + axes_s + '）' if axes_s else ''}：{c['reason']}")
    if not comps:
        out.append("- （まだなし）")
    out.append("")

    out += ["## 5. 最近の流れ"]
    for e in db.rows(conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT 15")):
        out.append(f"- {e['ts']} {e['actor']} {e['action']} {e['payload_json']}")
    return "\n".join(out) + "\n"
