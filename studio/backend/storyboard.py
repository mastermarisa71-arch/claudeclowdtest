"""9コマの仮Vコン。ドラフトの前に、エージェントが想像しているカットを監督と確かめる段。

1シート＝16:9 を 3×3 に等分した 9コマ（vault の制作ルール）。同じカットのコマは同じシートに入れる。
生成したシートは9枚に切り分け、各コマのテイク（kind=board）として登録する。編集画面では、
ドラフトがまだないコマはこの絵で映るので、そのまま仮Vコンとして通しで見られる。
"""
import json
import subprocess
from pathlib import Path

from . import config, core, db
from . import shots as shotlib

PANEL_MARK = "①②③④⑤⑥⑦⑧⑨"


def plan_boards(conn, code: str, replace: bool = False) -> list[dict]:
    ep = db.episode_by_code(conn, code)
    if replace:
        conn.execute("DELETE FROM boards WHERE episode_id=?", (ep["id"],))
    elif conn.execute("SELECT 1 FROM boards WHERE episode_id=?", (ep["id"],)).fetchone():
        raise ValueError("仮Vコンのシートがもうあります。作り直すなら --replace")
    cuts = db.rows(conn.execute("SELECT id, cut, panel FROM cuts WHERE episode_id=? ORDER BY seq", (ep["id"],)))
    groups = []
    for c in cuts:
        if groups and groups[-1][0]["cut"] == c["cut"]:
            groups[-1].append(c)
        else:
            groups.append([c])
    sheets, cur = [], []
    for g in groups:
        if len(cur) + len(g) > 9 and cur:
            sheets.append(cur)
            cur = []
        cur += g[:9]
    if cur:
        sheets.append(cur)
    out = []
    for i, cs in enumerate(sheets, 1):
        db.insert(conn, "boards", {"episode_id": ep["id"], "code": f"SB{i:02d}", "seq": i,
                                   "cut_ids_json": json.dumps([c["id"] for c in cs])})
        out.append({"code": f"SB{i:02d}", "panels": len(cs),
                    "range": f"{cs[0]['cut']}{cs[0]['panel']}〜{cs[-1]['cut']}{cs[-1]['panel']}"})
    db.log(conn, "agent", "plan_boards", {"episode": code, "sheets": len(out)})
    return out


def board_prompt(conn, code: str, board_code: str) -> dict:
    """シート1枚分の骨組み（日本語、既存の 9コマプロンプトの形）。エージェントが仕上げる。"""
    ep = db.episode_by_code(conn, code)
    b = db.one(conn.execute("SELECT * FROM boards WHERE episode_id=? AND code=?", (ep["id"], board_code)))
    ids = json.loads(b["cut_ids_json"])
    refs, labels, missing, cast = [], [], [], []
    lines = ["【共通】",
             f"『Bar 月灯り』の仮Vコン。16:9 の画面を 3×3 に等分した9コマに、左上から右へ順に描く。コマ同士は細い白線で区切る。",
             "各コマはアニメのカットの1フレーム。コマの中に文字・番号を描かない。空きのコマは無地のグレー。",
             "背景の参照画像はカメラ位置と家具の配置の正。キャラの参照画像は外見の正で、ポーズは各コマの指定に従う。", ""]
    body = []
    for n, cid in enumerate(ids):
        c = db.one(conn.execute("SELECT * FROM cuts WHERE id=?", (cid,)))
        head = db.one(conn.execute("SELECT * FROM cuts WHERE episode_id=? AND cut=? ORDER BY seq LIMIT 1",
                                   (ep["id"], c["cut"])))
        pos = c.get("camera_pos") or head.get("camera_pos") or ""
        for x in shotlib.cast_of(c):
            if x not in cast:
                cast.append(x)
        bg = shotlib._find_bg(conn, {"camera_pos": pos}, None)
        if bg and bg["file_path"] not in refs:
            refs.append(bg["file_path"]); labels.append(f"背景（{bg['name']}）")
        body.append(f"コマ{n + 1}（{c['cut']}{c['panel']}、カメラ位置 {pos or '-'}）：{c.get('picture') or ''}"
                    + (f"／配置：{c['layout']}" if c.get("layout") else "")
                    + (f"／芝居：{c['acting']}" if c.get("acting") else "")
                    + (f"／表情：{c['emotion']}" if c.get("emotion") else ""))
    chars = {a["name"]: a for a in shotlib.assets(conn, "character")}
    for x in sorted(cast, key=lambda v: shotlib.CAST_ORDER.index(v) if v in shotlib.CAST_ORDER else 99):
        if x in chars:
            refs.append(chars[x]["file_path"]); labels.append(f"{x}（設定資料）")
        else:
            missing.append(f"{x} の設定資料")
    for n in range(len(ids), 9):
        body.append(f"コマ{n + 1}：空き（無地のグレー）")
    lines.append("【参照画像】" + "／".join(f"@image{i + 1}＝{l}" for i, l in enumerate(labels)))
    lines += ["", "【コマ】"] + body
    return {"board": board_code, "prompt": "\n".join(lines), "refs": refs[:config.REF_LIMIT],
            "ref_labels": labels[:config.REF_LIMIT], "missing": missing, "board_id": b["id"], "cut_ids": ids}


def split_sheet(conn, take_id: int) -> list[int]:
    """3×3 のシート画像を9枚に切り、各コマのテイクとして登録する。"""
    t = db.one(conn.execute("SELECT t.*, e.code FROM takes t JOIN episodes e ON e.id=t.episode_id WHERE t.id=?",
                            (take_id,)))
    b = db.one(conn.execute("SELECT * FROM boards WHERE id=?", (t["board_id"],)))
    ids = json.loads(b["cut_ids_json"])
    src = config.MEDIA_DIR / t["file_path"]
    made = []
    for n, cid in enumerate(ids):
        r, c = divmod(n, 3)
        out = src.with_name(f"{src.stem}_k{n + 1}.png")
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(src), "-vf",
                        f"crop=iw/3:ih/3:{c}*iw/3:{r}*ih/3", "-frames:v", "1", str(out)], check=True)
        rel = out.relative_to(config.MEDIA_DIR).as_posix()
        tid = core.add_take(conn, episode=t["code"], cut_id=cid, kind="image", provider=t["provider"],
                            model=t["model"], prompt=f"{b['code']} {PANEL_MARK[n]}（シート #{take_id} から切り出し）",
                            parent_take_id=take_id, file_path=rel, agent_note="仮Vコン")
        db.update(conn, "takes", tid, {"tier": "board", "board_id": b["id"]})
        made.append(tid)
    return made
