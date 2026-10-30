"""美術・素材の受け渡し：監督が自分でレンダー・撮処理した素材を、どのコマにどう使うかと一緒に渡す。

1. AI が字コンテから、要る背景を「場所 × カメラ位置 × ルック」でまとめて並べる（発注：BG01 …）。何が映るか・使うコマも書く。
2. 監督はレンダーして撮処理した素材を、その発注に落とす。注意書き（光・撮処理の予定・レイヤー・気をつけること・使い方）をつける。
3. 生成の係は、コマの背景にその素材を使い、注意書きを守る（ブリーフとショットの骨組みに出る）。
キャラの設定資料・小物なども同じ口で渡せる（発注なしで、使うシーン・注意書きをつけて）。
"""
import json
import re
import shutil
import time
from pathlib import Path

from . import config, core, db, direction

# 注意書きの欄（素材の種類ごと）。監督の画面のフォームと、生成の係のブリーフに同じものが出る
NOTE_FIELDS = {
    "bg": [("light", "時間帯・光", "夕方。窓から斜めの光"),
           ("comp", "撮処理の予定（監督があとでかける）", "窓の光・奥のぼかし・色調整は撮処理で足す。生成では光を足しすぎない"),
           ("layers", "レイヤー", "手前のグラスとカウンターは別レイヤー"),
           ("avoid", "気をつけること", "左右反転しない。看板の文字は差し替える")],
    "character": [("look", "見るところ", "髪の色の塗り分け、エプロンの紐"),
                  ("break", "崩れやすいところ", "前髪の分け目、手の指の数"),
                  ("avoid", "気をつけること", "ハイライトは描かない")],
    "prop": [("look", "見るところ", "お客様ノートの表紙の色"), ("avoid", "気をつけること", "中の文字は読めないように")],
    "layout": [("look", "見るところ", "席の番号・カメラ位置"), ("avoid", "気をつけること", "図の文字・矢印は画面に描かない")],
    "effect": [("look", "見るところ", "光の向き"), ("avoid", "気をつけること", "")],
}
USES = {"ref": "生成の背景・参照に使う", "mood": "雰囲気の参考だけ", "comp": "編集で合成する（生成には使わない）"}


def _place(conn, eid: int, scene: str) -> tuple[str, str]:
    s = db.one(conn.execute("SELECT place, time FROM scenes WHERE episode_id=? AND code=?", (eid, scene)))
    return ((s or {}).get("place") or "", (s or {}).get("time") or "")


def plan(conn, episode: str) -> list[dict]:
    """字コンテから要る背景をまとめる。渡し済み・使わないの発注はそのまま残し、まだのものだけ作り直す。"""
    ep = db.episode_by_code(conn, episode)
    cuts = db.rows(conn.execute("SELECT * FROM cuts WHERE episode_id=? ORDER BY seq", (ep["id"],)))
    groups: dict[tuple, list[dict]] = {}
    head: dict[tuple, dict] = {}
    for c in cuts:
        # 同じカットの②③…は、カメラ位置とルックを①から引き継ぐ（字コンテは①にだけ書いてある）
        h0 = head.setdefault((c["scene"], c["cut"]), c)
        cam_raw = (c["camera_pos"] or h0["camera_pos"] or "").strip()
        look = ((c["look"] or h0["look"] or "") or (db.one(conn.execute(
            "SELECT look FROM scenes WHERE episode_id=? AND code=?", (ep["id"], c["scene"]))) or {}).get("look") or "")[:1]
        place, time_ = _place(conn, ep["id"], c["scene"])
        cam = cam_raw[:1] if cam_raw[:1] in "ABCDEF" else ""
        places = place.split("→")
        # 「控室→月灯り店内」のようなシーンは、カメラ位置 A〜F（店内の位置）なら店内の素材
        place = next((p for p in places if "店内" in p), places[0]) if cam else places[0]
        place = place or "（場所未定）"
        if re.search(r"フラッシュ|【パーツ】|INSERT", f"{c['camerawork']}{c['picture']}"):
            continue        # パーツ・フラッシュは背景がほぼ映らない（引きの素材で足りる）
        groups.setdefault((place, cam, look), []).append({**c, "time": time_, "cam_raw": cam_raw})
    keep = {(o["place"], o["camera"], o["look"]): o for o in db.rows(conn.execute(
        "SELECT * FROM art_orders WHERE episode_id=? AND status!='open'", (ep["id"],)))}
    conn.execute("DELETE FROM art_orders WHERE episode_id=? AND status='open'", (ep["id"],))
    used = {o["code"] for o in keep.values()}
    n = 0
    for (place, cam, look), cs in sorted(groups.items(), key=lambda kv: kv[1][0]["seq"]):
        ids = [c["id"] for c in cs]
        if (place, cam, look) in keep:
            db.update(conn, "art_orders", keep[(place, cam, look)]["id"], {"cut_ids_json": json.dumps(ids)})
            continue
        n += 1
        while f"BG{n:02d}" in used:
            n += 1
        scenes = sorted({c["scene"] for c in cs}, key=lambda s: int(re.sub(r"\D", "", s) or 0))
        wide = next((c for c in cs if re.search(r"引き|全景|FIX", f"{c['camerawork']}")), cs[0])
        from collections import Counter
        raw = [r for r, _ in Counter(c["cam_raw"] for c in cs if c["cam_raw"]).most_common(3)]
        what = (f"{place}・{'カメラ' + cam if cam else ('／'.join(raw) or 'カメラ位置の書きなし') + '（字コンテの書き方）'}・ルック{look or '―'}（{cs[0]['time']}）。"
                f"{'・'.join(scenes)} の {len(cs)}コマで使う。いちばん引きの画：{wide['picture'][:60]}")
        db.insert(conn, "art_orders", {"episode_id": ep["id"], "code": f"BG{n:02d}", "place": place, "camera": cam, "look": look,
                                       "time": cs[0]["time"], "cut_ids_json": json.dumps(ids), "what": what,
                                       "status": "open", "created_at": db.now()})
    db.log(conn, "agent", "art_plan", {"episode": episode})
    return orders(conn, episode)


def orders(conn, episode: str) -> list[dict]:
    ep = db.episode_by_code(conn, episode)
    rows = db.rows(conn.execute("SELECT * FROM art_orders WHERE episode_id=? ORDER BY code", (ep["id"],)))
    for o in rows:
        ids = json.loads(o.pop("cut_ids_json") or "[]")
        cs = db.rows(conn.execute(f"SELECT id, scene, cut, panel, seconds, picture FROM cuts WHERE id IN ({','.join('?' * len(ids)) or 'NULL'}) ORDER BY seq", ids))
        o["cuts"] = [{"id": c["id"], "code": f"{c['cut']}{(c['panel'] or '').strip('―')}", "scene": c["scene"],
                      "seconds": c["seconds"], "picture": c["picture"]} for c in cs]
        o["scenes"] = sorted({c["scene"] for c in cs}, key=lambda s: int(re.sub(r"\D", "", s) or 0))
        o["camera_xy"] = direction.plans().get(direction.plan_for(o["place"])[0], {}).get("cameras", {}).get(o["camera"])
        o["plan"] = direction.plan_for(o["place"])[0]
        o["asset"] = _asset(conn, o["asset_id"]) if o["asset_id"] else None
    return rows


def _asset(conn, asset_id: int) -> dict | None:
    a = db.one(conn.execute("SELECT * FROM assets WHERE id=?", (asset_id,)))
    if not a:
        return None
    u = db.one(conn.execute("SELECT * FROM asset_uses WHERE asset_id=? ORDER BY id DESC LIMIT 1", (asset_id,)))
    a["use"] = (u or {}).get("use", "ref")
    a["notes"] = json.loads((u or {}).get("notes_json") or "{}")
    return a


def deliver(conn, episode: str, src: Path, kind: str = "bg", name: str = "", order_id: int | None = None,
            scenes: list[str] | None = None, use: str = "ref", notes: dict | None = None, created_by: str = "human") -> dict:
    """素材を渡す。ファイルは月灯スタジオの素材置き場にコピーし、参照素材の棚（assets）に入れて、使うコマと注意書きを結ぶ。"""
    ep = db.episode_by_code(conn, episode)
    o = db.one(conn.execute("SELECT * FROM art_orders WHERE id=?", (order_id,))) if order_id else None
    name = name or (f"{o['place']}:{o['camera'] or o['code']}" if o else src.stem)
    rel = Path("assets") / kind / f"{episode}_{(o or {}).get('code') or re.sub(r'[^\w]+', '_', name)}_{int(time.time())}{src.suffix.lower()}"
    (config.MEDIA_DIR / rel).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, config.MEDIA_DIR / rel)
    if o and o["asset_id"]:
        conn.execute("UPDATE assets SET active=0 WHERE id=?", (o["asset_id"],))   # 差し替え
    meta = {"camera": f"CAM_{o['camera']}" if o and o["camera"] else "", "place": (o or {}).get("place", ""), "look": (o or {}).get("look", "")}
    aid = db.insert(conn, "assets", {"kind": kind, "name": name, "file_path": rel.as_posix(), "meta_json": json.dumps(meta, ensure_ascii=False),
                                     "note": " ／ ".join(f"{v}" for v in (notes or {}).values() if v), "active": 1, "created_at": db.now()})
    cut_ids = json.loads(o["cut_ids_json"]) if o else [r[0] for r in conn.execute(
        f"SELECT id FROM cuts WHERE episode_id=? AND scene IN ({','.join('?' * len(scenes or [])) or 'NULL'})", [ep["id"], *(scenes or [])])]
    db.insert(conn, "asset_uses", {"asset_id": aid, "episode_id": ep["id"], "order_id": order_id, "cut_ids_json": json.dumps(cut_ids),
                                   "use": use, "notes_json": json.dumps(notes or {}, ensure_ascii=False), "created_by": created_by,
                                   "created_at": db.now()})
    if o:
        db.update(conn, "art_orders", o["id"], {"status": "delivered", "asset_id": aid, "delivered_at": db.now()})
    core.add_review(conn, target_type="episode", target_id=ep["id"], verdict="良い", tags=["素材"],
                    comment=f"[素材 {(o or {}).get('code') or kind}] 監督が渡した：{name}（{USES.get(use, use)}）"
                            + "".join(f"　{k}：{v}" for k, v in (notes or {}).items() if v)) if created_by == "human" else None
    db.log(conn, created_by, "deliver_asset", {"asset": aid, "order": order_id, "episode": episode})
    return {"asset": aid, "file": rel.as_posix()}


def materials(conn, episode: str) -> list[dict]:
    """この話数で渡された素材（キャラ・小物なども）と、使うコマ・注意書き。"""
    ep = db.episode_by_code(conn, episode)
    rows = db.rows(conn.execute("""SELECT a.*, u.use, u.notes_json, u.cut_ids_json, u.order_id FROM asset_uses u
        JOIN assets a ON a.id=u.asset_id WHERE u.episode_id=? AND a.active=1 ORDER BY a.kind, a.id""", (ep["id"],)))
    for r in rows:
        r["notes"] = json.loads(r.pop("notes_json") or "{}")
        ids = json.loads(r.pop("cut_ids_json") or "[]")
        r["scenes"] = sorted({x[0] for x in conn.execute(
            f"SELECT scene FROM cuts WHERE id IN ({','.join('?' * len(ids)) or 'NULL'})", ids)}, key=lambda s: int(re.sub(r"\D", "", s) or 0))
        r["n_cuts"] = len(ids)
    return rows


def for_cut(conn, cut_id: int, kind: str = "bg") -> dict | None:
    """このコマに監督が結んだ素材（生成の係が最初に使う）。編集で合成するもの（comp）は生成には使わない。"""
    for r in db.rows(conn.execute("""SELECT a.*, u.use, u.notes_json, u.cut_ids_json FROM asset_uses u JOIN assets a ON a.id=u.asset_id
            WHERE a.kind=? AND a.active=1 ORDER BY u.id DESC""", (kind,))):
        if cut_id in json.loads(r["cut_ids_json"] or "[]"):
            r["notes"] = json.loads(r.pop("notes_json") or "{}")
            return r
    return None


def notes_text(notes: dict, kind: str = "bg") -> str:
    labels = {k: l for k, l, _ in NOTE_FIELDS.get(kind, [])}
    return " ／ ".join(f"{labels.get(k, k)}：{v}" for k, v in notes.items() if v)
