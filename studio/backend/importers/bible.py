"""設定（キャラ・舞台）を vault の 06_設定 に書き出し、ツールとエージェントが同じものを読めるようにする。

- キャラ：キャラクターシート.pdf（pdftotext）＋「映像の作り方の方針」の芝居の辞書
- 舞台：店内配置とカメラ位置 A〜F、Blender の舞台フォルダ
キャラクターシートや辞書が更新されたら、もう一度実行すれば上書きされる。
生成後に人やエージェントが書き足すのは「## 追記」より下だけにする（再生成で消えないように残す）。
"""
import re
import subprocess
from pathlib import Path

from .. import config

SHEET = "03_脚本/キャラクターシート.pdf"
METHOD = "01_シリーズ/映像の作り方の方針.md"
OUT = "06_設定"
KEEP_MARK = "## 追記"

# キャラクターシートの名前 → ツール内の呼び名（字コンテ・辞書で使う名前）
SHORT = {"捜査官 A（先輩）": "先輩", "捜査官 B（後輩）": "後輩"}
DICT_COLS = ["歩き方・立ち方", "物の持ち方", "不安・こわい", "うれしい", "照れ・ごまかし", "決意"]


def _sheet_text() -> str:
    pdf = config.VAULT_DIR / SHEET
    return subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True,
                          check=True).stdout


def split_sheet(text: str) -> dict[str, str]:
    """「名前」行で区切る。末尾の目次（名前の羅列）は捨てる。"""
    blocks, name, buf = {}, None, []
    for line in text.splitlines():
        m = re.match(r"^\s*名前\s+(.+?)\s*$", line)
        if m:
            if name:
                blocks[name] = "\n".join(buf).rstrip()
            name, buf = m.group(1), []
            continue
        if name:
            buf.append(line.rstrip())
    if name:
        blocks[name] = "\n".join(buf).rstrip()
    out = {}
    for full, body in blocks.items():
        body = re.split(r"\n\s*背の順", body)[0]         # 最後のキャラの後ろの「背の順」と目次を切る
        short = SHORT.get(full, full.split()[-1])
        out[short] = (full, body.strip("\n"))
    return out


def acting_dictionary() -> dict[str, dict[str, str]]:
    text = (config.VAULT_DIR / METHOD).read_text(encoding="utf-8")
    sec = text.split("## キャラの芝居の辞書", 1)[1].split("\n## ", 1)[0]
    rows = {}
    for line in sec.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 7 and cells[0] not in ("キャラ", "---"):
            rows[cells[0]] = dict(zip(DICT_COLS, cells[1:]))
    return rows


def _keep_tail(path: Path, what: str = "このキャラの描き方") -> str:
    if path.exists():
        old = path.read_text(encoding="utf-8")
        if KEEP_MARK in old:
            return old[old.index(KEEP_MARK):]
    return f"{KEEP_MARK}\n\n（エージェントのセルフレビューや監督のレビューで分かった、{what}の注意をここに足す）\n"


def character_md(short: str, full: str, body: str, acting: dict | None, tail: str) -> str:
    lines = ["---", f'title: "{short}"', "tags: [設定, キャラ]", "---", "",
             f"# {full}", "", f"> 出典：[キャラクターシート](../../{SHEET})"
             + (f"・[芝居の辞書](../../{METHOD})" if acting else "") + "（自動生成。下の「追記」より上は再生成で上書き）", ""]
    lines += ["## シート", "", "```text", body, "```", ""]
    if acting:
        lines += ["## 芝居の辞書", "", "| 場面 | しぐさ |", "| --- | --- |"]
        lines += [f"| {k} | {v} |" for k, v in acting.items()]
        lines += [""]
    lines += ["## セルフレビューで見ること", "",
              "- 性格・テンションに合った動きか（シートの性格、立ち位置、語尾と合うか）",
              "- その感情のときに、辞書のしぐさ（またはそれに近い癖）になっているか" if acting else
              "- 外見と頭身が参照画像どおりか",
              "- 持ち方・歩き方がこのキャラのものか（ほかのキャラの所作になっていないか）",
              "- 背の順と外見（身長差、髪、服、小物）が崩れていないか", ""]
    return "\n".join(lines) + "\n" + tail


STAGE_MD = """---
title: "舞台"
tags: [設定, 舞台]
---

# 舞台

> 自動生成の土台。配置とカメラ位置の正は[生成と字コンテのルール](../../04_制作ルール/生成と字コンテのルール.md)と[映像の作り方の方針](../../01_シリーズ/映像の作り方の方針.md)。

## 月灯り 店内

- 配置：ピアノ（手前左）、席1〜6、カウンターの内側（朔奈＝席2の前、まひる＝席4の前）、暁＝席6、あかね＝暁のすぐ左の床（門番）、入口。
- カメラ位置：A 客席の後ろからカウンター正面／B カウンターの内側から客席（Aと左右が反転）／C カウンターの右端の外／D ピアノ側／E 斜め俯瞰／F 真俯瞰。
- 画面の方向：店（扉の内側）＝右、外（町）＝左。
- 光：日常は蜂蜜色の暖色（ルックB）、緊迫は一段落として青へ（C）、裏方（厨房・控室）は白い LED。

## Blender の舞台

{blender}

背景はエージェントが Blender でカメラ位置ごとにレンダーし、参照画像として登録する（`python studio/cli.py bg-render`）。

{tail}"""


def write_all() -> list[str]:
    out_dir = config.VAULT_DIR / OUT
    (out_dir / "キャラ").mkdir(parents=True, exist_ok=True)
    (out_dir / "舞台").mkdir(parents=True, exist_ok=True)
    sheet, acting = split_sheet(_sheet_text()), acting_dictionary()
    written = []
    for short, (full, body) in sheet.items():
        p = out_dir / "キャラ" / f"{short}.md"
        p.write_text(character_md(short, full, body, acting.get(short), _keep_tail(p)), encoding="utf-8")
        written.append(str(p.relative_to(config.VAULT_DIR)))

    stages = sorted({d.name.rsplit("_v", 1)[0] for d in config.REPO_ROOT.glob("月灯り_*_v*") if d.is_dir()})
    blender = "\n".join(f"- {s}（最新：{max(config.REPO_ROOT.glob(s + '_v*'), key=lambda d: int(d.name.rsplit('_v', 1)[1])).name}）" for s in stages)
    p = out_dir / "舞台" / "店と町.md"
    p.write_text(STAGE_MD.format(blender=blender or "- （なし）", tail=_keep_tail(p, "舞台の描き方")), encoding="utf-8")
    written.append(str(p.relative_to(config.VAULT_DIR)))

    idx = ["---", 'title: "設定"', "tags: [index]", "---", "",
           "キャラと舞台の設定。エージェントは生成とセルフレビューの前に、そのカットに出るキャラと舞台のノートを読む。", ""]
    idx += [f"- [{Path(w).stem}]({Path(w).relative_to(OUT).as_posix()})" for w in written]
    (out_dir / "INDEX.md").write_text("\n".join(idx) + "\n", encoding="utf-8")
    return written


def characters() -> list[str]:
    d = config.VAULT_DIR / OUT / "キャラ"
    return sorted(p.stem for p in d.glob("*.md")) if d.exists() else []


def characters_in(text: str) -> list[str]:
    """字コンテの文からそのコマに出るキャラを拾う（呼び名の一致だけの素朴な判定）。"""
    return [c for c in characters() if c in (text or "")]
