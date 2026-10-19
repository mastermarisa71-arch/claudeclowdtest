"""字コンテ（xlsx）を cuts に取り込む。

版によって列名と並びが違う（EP01 v6 は「画（大きさ…）」「動画化」あり、EP09 4分版は「見せる人／視点」あり）ので、
列名の言い換え表で吸収する。CUT 列が空の行は直前のカットのコマ（②③…）として扱う。
"""
import json
import re
from pathlib import Path

import openpyxl

from .. import db

# cuts の列 → 字コンテの列名の候補（前方一致）
COLUMN_ALIASES = {
    "cut": ["CUT"],
    "panel": ["コマ"],
    "seconds": ["コマ尺"],
    "look": ["ルック"],
    "viewpoint": ["見せる人", "画（大きさ"],
    "camera_pos": ["カメラ位置"],
    "layout": ["画面配置", "配置"],
    "camerawork": ["カメラワーク"],
    "to_video": ["動画化"],
    "picture": ["画面（構図）", "画面・芝居", "画面"],
    "acting": ["芝居"],
    "emotion": ["表情"],
    "dialogue": ["台詞"],
    "sound": ["音"],
    "intent": ["演出意図", "ねらい"],
    "edit_memo": ["編集メモ"],
    "scene": ["シーン"],
}

CUT_RE = re.compile(r"^[SN]\d+-\d+")
SCENE_RE = re.compile(r"^([SN]\d+)\s")


def _map_columns(header: list) -> dict[str, int]:
    names = [str(h or "").strip() for h in header]
    mapping: dict[str, int] = {}
    for field, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            idx = next((i for i, n in enumerate(names)
                        if n.startswith(alias) and i not in mapping.values()), None)
            if idx is not None:
                mapping[field] = idx
                break
    return mapping


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def parse(path: str | Path) -> list[dict]:
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.worksheets[0]
    it = ws.iter_rows(values_only=True)
    header = list(next(it))
    cols = _map_columns(header)
    if "cut" not in cols or "panel" not in cols:
        raise ValueError(f"字コンテの見出し行に CUT / コマ が見つかりません: {header}")

    out, scene, current_cut = [], "", ""
    for row in it:
        cell = lambda f: str(row[cols[f]]).strip() if f in cols and row[cols[f]] is not None else ""
        cut_val = cell("cut")
        m = SCENE_RE.match(cut_val)
        if m and not cell("panel"):
            scene = m.group(1)           # 「S1 ○月灯り・店内・夕方」のような見出し行
            continue
        if CUT_RE.match(cut_val):
            current_cut = cut_val
        elif cut_val or not cell("panel"):
            continue                      # 「見せたいもの：…」「流れ：…」などのメモ行
        rec = {f: cell(f) for f in cols if f not in ("cut", "seconds")}
        rec["cut"] = current_cut
        rec["scene"] = cell("scene") or scene or current_cut.split("-")[0]
        rec["seconds"] = _num(cell("seconds"))
        rec["raw_json"] = json.dumps(
            {str(header[i]): (str(v) if v is not None else "") for i, v in enumerate(row) if i < len(header)},
            ensure_ascii=False)
        out.append(rec)
    return out


def import_file(conn, episode_code: str, path: str | Path, version: str, vault_rel: str = "") -> dict:
    ep = db.get_or_create_episode(conn, episode_code)
    doc_id = db.insert(conn, "documents", {
        "episode_id": ep["id"], "kind": "jikonte", "version": version,
        "path": vault_rel or str(path), "created_by": "human", "created_at": db.now(),
        "summary": "既存の字コンテを取り込み",
    })
    records = parse(path)
    for seq, rec in enumerate(records, start=1):
        db.insert(conn, "cuts", {**rec, "episode_id": ep["id"], "document_id": doc_id, "seq": seq})
    db.log(conn, "human", "import_jikonte", {"episode": episode_code, "version": version, "rows": len(records)})
    return {"episode": episode_code, "document_id": doc_id, "rows": len(records),
            "seconds": round(sum(r["seconds"] or 0 for r in records), 1)}
