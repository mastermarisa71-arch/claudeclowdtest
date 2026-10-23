"""エージェントへの「ブリーフ」を組み立てる。

エージェントは作業の前に必ずこれを読む：
1. 作品の正（vault のどのファイルを読むべきか）
2. 承認済みのルール（learnings）
3. まだ対応していないレビュー（どのテイクの、どこが、なぜ）
4. 比較で分かった好み（AよりBが良い、その理由）
5. 前回までの流れ（最近のイベント）
"""
import json

from . import config, core, db, direction
from .importers import bible

CANON_FILES = [
    "00_正本/通し設計_正本.md",
    "00_正本/決定ログ.md",
    "00_正本/未決リスト.md",
    "04_制作ルール/生成と字コンテのルール.md",
    "01_シリーズ/映像の作り方の方針.md",
    "03_脚本/いまの版/INDEX.md",
    "06_設定/INDEX.md",
]

SELF_REVIEW = """生成したら、監督に見せる前に必ず自分で見る（`self-review`）。観点ごとに true か、だめな理由を書く：
- 意図：字コンテの「演出意図」「表情・感情」が画面から読めるか
- 配置・左右：カメラ位置と画面配置どおりか（店＝右、外＝左、Bは反転）
- 芝居：そのキャラの性格・テンションと、06_設定の芝居の辞書に合うしぐさか
- キャラ崩れ：外見・頭身・背の順・小物（ステラは全身黒、先輩の紋章は左腕）
- 光・色：ルック（B日常/C緊迫/E情景/F外/N最も冷たい）どおりか
- つなぎ：前後のコマと立ち位置・小物の状態がつながるか
不合格は自分で直す（作り直しは上限まで）。上限を超えたら、迷っている点を書いて監督に回す。"""


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
    out.append("- studio/docs/Seedance2.5_プロンプトの書き方.md（ショットのプロンプトを書く前に）")
    if ep:
        out.append(f"- {config.VAULT_DIR.name}/02_各話/{ep['code']}/ と 03_脚本/いまの版/{ep['code']}_脚本_いまの版.md")
    out.append("")

    if ep:
        sc = core.scenes(conn, ep["code"])
        budget = ep.get("budget_credits") or config.DEFAULT_BUDGET_YEN
        out += [f"## 話数の状態：{ep['code']}", f"- 目標尺 {ep['target_seconds']}秒 / 締切 {ep.get('deadline') or '未設定'}"
                f" / 使用 {sc['spent']:,.0f}円 / 予算 {budget:,.0f}円（残り {budget - sc['spent']:,.0f}円）"
                + ("（テストの回：超えても止めない）" if ep.get("is_test") else "")]
        out += ["", "### シーン整理と設計（字コンテのカットの意図は、ここから引く）"]
        for s_ in sc["scenes"]:
            out.append(f"- {s_['code']} [{s_['status']}] {s_['place']} {s_['time']} ルック{s_['look']} "
                       f"目標{s_['target_seconds']}秒/今{s_['actual_seconds']}秒：{s_['purpose']}"
                       + (f"\n  変化：{s_['change_before']} → {s_['change_after']}（きっかけ：{s_['turn'] or '―'}）"
                          if s_["change_before"] or s_["change_after"] else "\n  変化：（未整理）")
                       + "".join(f"\n  {c.get('name')}：したい＝{c.get('want', '')}／する＝{c.get('does', '')}"
                                 f"／内心＝{c.get('inner', '')}／温度{c.get('tension', '')}" for c in s_["characters"])
                       + (f"\n  動線：{s_['blocking']}" if s_["blocking"] else "")
                       + "".join(f"\n  配置図 {t}" for t in s_["blocking_text"]))
        if not sc["scenes"]:
            out.append("- （まだシーン整理がない。脚本を読んだら字コンテより先に scene-set / scene-sheet で作り、監督の承認をもらう）")
        open_c = direction.list_choices(conn, ep["code"], "open")
        out += ["", f"### 監督に聞いている2択（{len(open_c)}件、答えを待つ間はほかを進める）"]
        out += [f"- #{c['id']} {c['scene']} {c['about']}：{c['question']}　"
                + " ／ ".join(f"{o['label']} {o['text']}" for o in c["options"]) for c in open_c] or ["- （なし）"]
        cast = sorted({c for r in conn.execute("SELECT picture, dialogue, layout, acting FROM cuts WHERE episode_id=?",
                                                (ep["id"],)) for c in bible.characters_in(" ".join(map(str, r)))})
        out += ["", "### この話に出るキャラ（生成とセルフレビューの前に読む）"]
        out += [f"- {config.VAULT_DIR.name}/06_設定/キャラ/{c}.md" for c in cast] or ["- （字コンテ未取り込み）"]
        out.append("")

    out += ["## セルフレビュー", SELF_REVIEW, ""]

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
                   f"[{r['tags']}] {r['comment']}{core.describe_region(r.get('region_json') or '')}"
                   + (f"\n  監督が印をつけた画面：{config.MEDIA_DIR.name}/{r['attachment']}（MCP review_image で見られる）"
                      if r.get("attachment") else ""))
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
