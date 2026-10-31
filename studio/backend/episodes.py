"""新しい話数を、脚本（または字コンテ）を落とすだけで作る。あとは工程の流れに乗る。

- md / txt：そのまま vault の「03_脚本/いまの版/EPxx_脚本_いまの版.md」になる
- xlsx：字コンテとして読み込む（いまの字コンテの列のまま）
- pdf / docx など：vault の「03_脚本/原稿/」に置き、制作進行が書き起こす
そのあと制作進行の仕事として「シーン整理の下書き（芯・物語の流れ・シーンごと）と美術の発注」を自動で積む。
"""
import re
import shutil
from pathlib import Path

from . import config, core, db


def _rel(p: Path) -> str:
    return f"{config.VAULT_DIR.name}/{p.relative_to(config.VAULT_DIR).as_posix()}"


def next_code(conn) -> str:
    nums = [int(re.sub(r"\D", "", e["code"]) or 0) for e in db.rows(conn.execute("SELECT code FROM episodes"))]
    return f"EP{(max(nums) + 1 if nums else 1):02d}"


def create(conn, code: str, title: str, target: float, src: Path, filename: str) -> dict:
    code = code.upper().strip() or next_code(conn)
    ep = db.get_or_create_episode(conn, code)
    db.update(conn, "episodes", ep["id"], {k: v for k, v in {"title": title, "target_seconds": target or None}.items() if v})
    ext = Path(filename).suffix.lower()
    did = []
    if ext in (".md", ".txt"):
        text = src.read_text(encoding="utf-8", errors="replace")
        out = config.VAULT_DIR / "03_脚本" / "いまの版" / f"{code}_脚本_いまの版.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        if not text.startswith("---"):
            text = f'---\ntitle: "{code} 脚本（いまの版）"\ndate: {db.now()[:10]}\ntags: [脚本, {code}]\n---\n# {title or code}\n\n' + text
        out.write_text(text, encoding="utf-8")
        did.append(f"脚本を {_rel(out)} に置きました")
        job = "脚本（いまの版）を読み、"
    elif ext in (".xlsx",):
        from .importers import jikonte
        dest = config.VAULT_DIR / "02_各話" / code / Path(filename).name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
        r = jikonte.import_file(conn, code, dest, Path(filename).stem, str(dest.relative_to(config.VAULT_DIR)))
        did.append(f"字コンテを読み込みました（{r.get('cuts', '')}コマ）")
        job = "字コンテと（あれば）脚本を読み、"
    else:
        dest = config.VAULT_DIR / "03_脚本" / "原稿" / f"{code}_{Path(filename).name}"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
        did.append(f"原稿を {_rel(dest)} に置きました")
        job = f"原稿（{_rel(dest)}）を「03_脚本/いまの版/{code}_脚本_いまの版.md」に書き起こしてから、"
    rid = core.add_request(conn, f"[新しい話数 {code}] {job}シーン整理の下書きを作る：この話の芯・物語の流れ（story-set）と、"
                                 "シーンごとの ①伝えたいこと ②変化 ③あらすじ ④キャラ（scene-sheet / scene-set、脚本の範囲 --from/--to も）。"
                                 "字コンテがあれば art-plan で美術の発注も。終わったら request-done", code)
    db.update(conn, "requests", rid, {"role": "まとめ"})
    db.log(conn, "human", "create_episode", {"episode": code, "file": filename})
    return {"episode": code, "did": did, "request": rid}
