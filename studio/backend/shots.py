"""カットの生成：参照素材の棚、プロンプトの組み立て、ドラフト→拡大→本番の昇格。

生成の方式（2026-10-19 監督の決定）：
- 画像を開始フレームにしない。キャラの設定資料と Blender の背景を「参照画像」として渡し、立ち位置や芝居はプロンプトで制御する。
- まず 480p のドラフトを作り、監督が良しとしたものだけを、そのまま拡大（upscale）し、拡大版を入力に 1080p の本番を作る。
"""
import json
import shutil
from pathlib import Path

from . import config, core, db
from .importers import bible

CAST_ORDER = ["あかね", "朔奈", "まひる", "海凪", "暁", "おばあ", "ステラ", "先輩", "後輩"]

COMMON = """【共通】
『Bar 月灯り』のアニメのカット。ゲームのスチルやイラストではなく、映像から切り取った1ショットとして動かす。
人物の芝居は実際の人間の重心と物理に沿わせる。カメラを見ない。喋る人物だけ口を動かす。
主役を一人（一組）に決め、いちばん明るく、ピントを合わせる。主役以外は小さく、端か奥に置く。
画面に文字を描かない（黒板・メモの文字は編集で合成する）。黒の主線（#000000）を使わない。
【参照画像の使い方】これは開始フレームではない。
・背景の参照画像は、カメラ位置・画角・家具の配置をそのまま使う（配置を変えない、物を増やさない）。
・キャラの参照画像（設定資料）は、外見・髪・服・頭身・背の比率の正。ポーズや向きは写さず、下の【画面配置】と【芝居】に従う。"""

EMOTION_KEYS = {"不安・こわい": ("不安", "こわ", "怖", "緊張", "おび"), "うれしい": ("うれ", "嬉", "喜", "笑"),
                "照れ・ごまかし": ("照れ", "ごまか", "恥"), "決意": ("決意", "決め", "覚悟")}


# ---- 参照素材の棚 ----

def add_asset(conn, kind: str, name: str, file_path: str, meta: dict | None = None, note: str = "",
              replace: bool = True) -> int:
    """file_path は MEDIA_DIR 相対。ローカルのファイルを渡されたら MEDIA_DIR/assets にコピーする。"""
    src = Path(file_path)
    if src.is_absolute() or (src.exists() and not (config.MEDIA_DIR / file_path).exists()):
        rel = Path("assets") / kind / src.name
        (config.MEDIA_DIR / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, config.MEDIA_DIR / rel)
        file_path = rel.as_posix()
    if replace:
        conn.execute("UPDATE assets SET active=0 WHERE kind=? AND name=?", (kind, name))
    aid = db.insert(conn, "assets", {"kind": kind, "name": name, "file_path": file_path,
                                     "meta_json": json.dumps(meta or {}, ensure_ascii=False),
                                     "note": note, "created_at": db.now()})
    db.log(conn, "agent", "add_asset", {"asset": aid, "kind": kind, "name": name})
    return aid


def assets(conn, kind: str | None = None) -> list[dict]:
    q = "SELECT * FROM assets WHERE active=1" + (" AND kind=?" if kind else "") + " ORDER BY kind, name"
    return db.rows(conn.execute(q, (kind,) if kind else ()))


def _find_bg(conn, cut: dict, bg_name: str | None) -> dict | None:
    bgs = assets(conn, "bg")
    if bg_name:
        return next((a for a in bgs if a["name"] == bg_name), None)
    pos = (cut.get("camera_pos") or "").strip()[:1]
    if not pos:
        return None
    for a in bgs:   # 名前が「…:A」か、カメラ名が「CAM_A」「…_A」のもの
        cam = json.loads(a["meta_json"] or "{}").get("camera", "")
        if a["name"].endswith(f":{pos}") or cam.endswith(f"_{pos}") or a["name"].endswith(f"_{pos}"):
            return a
    return None


def cast_of(cut: dict) -> list[str]:
    """画面に映るキャラ。台詞は「話者「…」」の話者だけを見て、（OFF）の話者と台詞の中身は数えない。"""
    import re
    speakers = " ".join(m.group(1) for m in re.finditer(r"([^\s「」（）]+)(?:（[^）]*）)?「", cut.get("dialogue") or "")
                        if "（OFF）" not in m.group(0) and "(OFF)" not in m.group(0))
    text = " ".join(str(cut.get(k) or "") for k in ("picture", "layout", "acting")) + " " + speakers
    found = bible.characters_in(text)
    return sorted(found, key=lambda c: CAST_ORDER.index(c) if c in CAST_ORDER else 99)


def _acting_lines(cast: list[str], cut: dict) -> list[str]:
    dict_rows = {}
    try:
        dict_rows = bible.acting_dictionary()
    except (OSError, IndexError):
        pass
    emo = f"{cut.get('emotion') or ''} {cut.get('intent') or ''}"
    lines = []
    for c in cast:
        row = dict_rows.get(c)
        if not row:
            continue
        hit = [k for k, keys in EMOTION_KEYS.items() if any(w in emo for w in keys)]
        parts = [f"立ち方={row['歩き方・立ち方']}", f"持ち方={row['物の持ち方']}"] + [f"{k}={row[k]}" for k in hit]
        lines.append(f"・{c}：" + "／".join(parts))
    return lines


# ---- プロンプトの組み立て ----

def build(conn, cut_id: int, tier: str = "draft", bg_name: str | None = None) -> dict:
    """字コンテ1行＋設計（動線）＋設定（芝居の辞書）＋参照素材から、プロンプトと参照画像の並びを作る。"""
    cut = db.one(conn.execute("SELECT * FROM cuts WHERE id=?", (cut_id,)))
    # 字コンテでは②③…のコマはカメラ位置・ルック・カメラワークを空欄にして①を引き継ぐ
    head = db.one(conn.execute("SELECT * FROM cuts WHERE episode_id=? AND cut=? ORDER BY seq LIMIT 1",
                               (cut["episode_id"], cut["cut"])))
    for k in ("camera_pos", "look", "camerawork"):
        if not cut.get(k) and head:
            cut[k] = head[k]
    scene = db.one(conn.execute("SELECT * FROM scenes WHERE episode_id=? AND code=?", (cut["episode_id"], cut["scene"])))
    cast = cast_of(cut)
    refs, labels, missing = [], [], []

    bg = _find_bg(conn, cut, bg_name)
    if bg:
        refs.append(bg["file_path"]); labels.append(f"背景（{bg['name']}）")
    else:
        missing.append(f"背景（カメラ位置 {cut.get('camera_pos') or '未指定'}）")
    layout = next(iter(assets(conn, "layout")), None)
    if layout and (cut.get("camera_pos") or "").strip()[:1] in "ABCDEF" and "店" in f"{scene and scene['place']}{cut.get('layout')}":
        refs.append(layout["file_path"]); labels.append(f"配置図（{layout['name']}。文字・矢印は描かない）")
    chars = {a["name"]: a for a in assets(conn, "character")}
    for c in cast:
        if c in chars:
            refs.append(chars[c]["file_path"]); labels.append(f"{c}（設定資料）")
        else:
            missing.append(f"{c} の設定資料")

    bg_meta = json.loads(bg["meta_json"] or "{}") if bg else {}
    seen = "、".join(v["name"] for v in bg_meta.get("visible_objects", [])[:8])
    secs = cut.get("seconds") or 2
    parts = [COMMON, "",
             "【参照画像】" + "／".join(f"@image{i + 1}＝{l}" for i, l in enumerate(labels)), "",
             f"【このカット】{cut['cut']}{cut['panel']}　{secs}秒　カメラ位置 {cut.get('camera_pos') or '-'}　ルック {cut.get('look') or '-'}",
             f"カメラワーク：{cut.get('camerawork') or 'FIX'}" + (f"（{cut['to_video']}）" if cut.get("to_video") else "")]
    if seen:
        parts.append(f"背景に映っている物（手前から）：{seen}")
    parts += ["", "【画面配置】" + (cut.get("layout") or "（字コンテに指定なし。主役を中央に）")]
    if scene and scene.get("blocking"):
        parts.append(f"シーン頭の立ち位置と動線：{scene['blocking']}")
    parts += ["", "【画面】" + (cut.get("picture") or ""),
              "【芝居】" + (cut.get("acting") or "") + (f"　表情・感情：{cut['emotion']}" if cut.get("emotion") else "")]
    parts += _acting_lines(cast, cut)
    if cut.get("dialogue"):
        parts.append(f"【台詞】{cut['dialogue']}（話者が画面にいれば口を動かす。OFF なら画面の人物の表情で受ける）")
    if cut.get("intent"):
        parts.append(f"【ねらい】{cut['intent']}")
    if tier == "draft":
        parts.append("\n【出力】480p のドラフト。構図・立ち位置・芝居の確認用")
    elif tier == "final":
        parts.append("\n【出力】1080p の本番。入力動画（承認したドラフトの拡大版）の構図・動き・タイミングを変えず、線と色と細部を仕上げる")
    return {"cut_id": cut_id, "prompt": "\n".join(parts), "refs": refs, "ref_labels": labels,
            "cast": cast, "missing": missing, "tier": tier, "seconds": secs}


# ---- ドラフト → 拡大 → 本番 ----

def _human_approved(conn, take_id: int) -> bool:
    return bool(conn.execute("SELECT 1 FROM reviews WHERE target_type='take' AND target_id=? AND created_by='human' "
                             "AND verdict IN ('良い','採用')", (take_id,)).fetchone())


def promote(conn, take_id: int, to: str = "final", provider: str | None = None, note: str = "") -> int:
    """採用したドラフトを入力に 1080p の本番を作る（Seedance は入力動画をそのまま大きく作り直す）。
    監督の「良い／採用」がないドラフトは進めない。upscale は単純な拡大が別に要るときだけ使う。"""
    t = db.one(conn.execute("SELECT t.*, e.code FROM takes t JOIN episodes e ON e.id=t.episode_id WHERE t.id=?",
                            (take_id,)))
    if t["status"] != "done" or not t["file_path"]:
        raise core.Blocked(f"テイク #{take_id} はまだ出来上がっていません（{t['status']}）")
    if to not in ("upscale", "final"):
        raise ValueError(to)
    if t["tier"] == "draft":
        draft_id = take_id
    elif t["tier"] == "upscale" and to == "final":
        draft_id = t["source_take_id"] or t["parent_take_id"]
    else:
        raise core.Blocked(f"テイク #{take_id}（{t['tier'] or '段階なし'}）からは {to} に進めません")
    if not _human_approved(conn, draft_id):
        raise core.Blocked(f"ドラフト #{draft_id} は監督の「良い／採用」がまだです")
    params = json.loads(t["params_json"] or "{}")
    audio_refs = []
    if to == "final" and t.get("shot_id"):
        from . import seedance
        prompt = seedance.build_brief(conn, t["shot_id"], "final")["prompt"]
        # 声優の声が届いていれば、その音声に口を合わせて作る
        sh = db.one(conn.execute("SELECT * FROM shots WHERE id=?", (t["shot_id"],)))
        offset = 0.0
        for cid in json.loads(sh["cut_ids_json"]):
            c = db.one(conn.execute("SELECT * FROM cuts WHERE id=?", (cid,)))
            a = db.one(conn.execute("SELECT * FROM takes WHERE cut_id=? AND kind='audio' AND role='actor' "
                                    "AND file_path!='' ORDER BY selected DESC, id DESC LIMIT 1", (cid,)))
            if a:
                audio_refs.append({"file": a["file_path"], "at": round(offset, 2), "speaker": a["prompt"]})
            offset += c["seconds"] or 0
        if audio_refs:
            prompt += "\n\nVOICE (lip-sync)\n" + "\n".join(
                f"@Audio {i}: {r['speaker'] or 'dialogue'} voice actor recording, starts at {r['at']}s. "
                "Match lip movement to this audio exactly; use it as the dialogue track."
                for i, r in enumerate(audio_refs, 1))
    elif to == "final":
        prompt = build(conn, t["cut_id"], "final")["prompt"]
    else:
        prompt = t["prompt"]
    return core.generate(
        conn, episode=t["code"], cut_id=t["cut_id"], kind=t["kind"], provider=provider or t["provider"],
        model=t["model"], prompt=prompt, refs=json.loads(t["refs_json"] or "[]"),
        params={"duration": params.get("duration", 5), "upscale": to == "upscale", "audio_refs": audio_refs}, tier=to,
        source_take_id=take_id, parent_take_id=take_id, shot_id=t.get("shot_id"),
        agent_note=note or f"#{take_id} から {to}")


def promote_all(conn, code: str, provider: str | None = None) -> list[str]:
    """監督が採用したドラフトのうち、まだ本番がないものを順に 1080p にする。"""
    out = []
    rows = db.rows(conn.execute("""
        SELECT t.id, t.shot_id, t.cut_id FROM takes t JOIN episodes e ON e.id=t.episode_id
        WHERE e.code=? AND t.tier='draft' AND t.status='done'
          AND EXISTS (SELECT 1 FROM reviews r WHERE r.target_type='take' AND r.target_id=t.id
                      AND r.created_by='human' AND r.verdict IN ('良い','採用'))
          AND NOT EXISTS (SELECT 1 FROM takes f WHERE f.source_take_id=t.id AND f.tier='final'
                          AND f.status NOT IN ('failed'))
        ORDER BY t.id""", (code,)))
    for r in rows:
        try:
            out.append(f"#{r['id']} → #{promote(conn, r['id'], 'final', provider)}")
        except core.Blocked as e:
            out.append(f"#{r['id']} 止めました：{e}")
            break
    return out


# ---- セルフレビュー用のコンタクトシート ----

def contact_sheet(conn, take_id: int, frames: int = 6) -> str:
    """動画テイクから等間隔に frames 枚を抜き出し、1枚の画像に並べる（エージェントが見る用。動画を丸ごと読ませない）。"""
    import subprocess
    t = db.one(conn.execute("SELECT * FROM takes WHERE id=?", (take_id,)))
    src = config.MEDIA_DIR / t["file_path"]
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                str(src)], capture_output=True, text=True, check=True).stdout.strip() or 1)
    out = src.with_name(f"{src.stem}_contact.jpg")
    cols = 3
    rows = (frames + cols - 1) // cols
    fps = frames / max(dur, 0.1)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(src), "-vf",
                    f"fps={fps:.4f},scale=640:-1,tile={cols}x{rows}", "-frames:v", "1", str(out)], check=True)
    return str(out)
