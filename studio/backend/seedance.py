"""Seedance 2.5 向け：マルチショットの分け方、プロンプトの骨組み、プロンプトの点検。

プロンプトの書き方（Seedance 2.5 の公開ガイドの要点。HAMSTER 経由でも同じ前提）：
1. 参照の割り当て：@Image N ごとに役割を1つだけ書き、「何に使わないか」も書く
2. 1文の要約：誰が・どこで・何が起きる・画風・カメラ
3. タイムライン：整数秒の区切りを隙間なく（SHOT 1 [0-3s] …）。各区切りに画面・カメラ・動き・台詞・音
   区切りの秒数は目安で、フレーム単位の切れ目ではない。1区切り 3〜8秒が扱いやすい
4. 一貫性の注意：固定したい特徴（髪・服・小物）を区切りごとに言い直す
5. 台詞は「Dialogue (名前, Japanese): "…"」。字幕・BGM は「No subtitles. No background music.」と否定で書く
   画面の中身は否定形で書かず、望む画を肯定形で書く
Seedance はプロンプトに忠実に動くので、動きは秒単位で細かく書く。骨組みはツールが作り、エージェントが仕上げる。
"""
import json
import re

from . import config, db
from .importers import bible
from . import shots as shotlib

ROLE = {
    "bg": "the set: camera position, framing, furniture and props layout only. Keep this layout exactly; "
          "do not add or remove furniture. Do not copy any people from it",
    "layout": "the floor plan of the bar: character positions only. Never draw its text, arrows or circles",
    "character": "{name}'s appearance only (face, hairstyle, outfit, colors, head-to-body ratio, height). "
                 "Do not copy the pose, the turnaround layout, or the plain background of the sheet",
    "prop": "the design of the {name} only (shape, color, material). Do not copy its background",
}
# 英語のプロンプトでの呼び名（参照画像のファイル名に合わせる）
ROMAJI = {"あかね": "Akane", "朔奈": "Sakuna", "まひる": "Mahiru", "海凪": "Kairi", "暁": "Akira",
          "おばあ": "Obaa (the old baker)", "ステラ": "Stella (black cat)", "先輩": "Senpai (senior inspector)",
          "後輩": "Kohai (junior inspector)"}
HEIGHT_ORDER = "Kohai > Akira > Sakuna > Akane > Mahiru > Kairi > Obaa > Senpai > Stella"


def en(name: str) -> str:
    return ROMAJI.get(name, name)


# ---- マルチショットの分け方 ----

def _cut_groups(cuts: list[dict]) -> list[list[dict]]:
    """字コンテの1カット（①②③…）を1かたまりにする。"""
    groups = []
    for c in cuts:
        if groups and groups[-1][0]["cut"] == c["cut"]:
            groups[-1].append(c)
        else:
            groups.append([c])
    return groups


def plan_shots(conn, code: str, target: float | None = None, replace: bool = False) -> list[dict]:
    """同じシーンの中で、カットのかたまりを目安の秒数まで詰めてショットにする（最大30秒）。
    これはたたき台。エージェントが字コンテ・仮Vコンを並べて見て、つながりで分け直す（shot-set）。"""
    target = target or config.SHOT_TARGET_SECONDS
    ep = db.episode_by_code(conn, code)
    if replace:
        conn.execute("DELETE FROM shots WHERE episode_id=?", (ep["id"],))
    elif conn.execute("SELECT 1 FROM shots WHERE episode_id=?", (ep["id"],)).fetchone():
        raise ValueError("ショットがもうあります。作り直すなら --replace")
    cuts = db.rows(conn.execute("SELECT id, scene, cut, panel, seconds FROM cuts WHERE episode_id=? ORDER BY seq",
                                (ep["id"],)))
    shots, cur, cur_s, scene = [], [], 0.0, None
    for g in _cut_groups(cuts):
        gs = sum(c["seconds"] or 0 for c in g)
        if cur and (g[0]["scene"] != scene or cur_s + gs > target or cur_s + gs > config.SHOT_MAX_SECONDS):
            shots.append((cur, cur_s))
            cur, cur_s = [], 0.0
        cur += g
        cur_s += gs
        scene = g[0]["scene"]
    if cur:
        shots.append((cur, cur_s))
    out = []
    for i, (cs, secs) in enumerate(shots, 1):
        code_ = f"SH{i:02d}"
        db.insert(conn, "shots", {"episode_id": ep["id"], "code": code_, "seq": i,
                                  "cut_ids_json": json.dumps([c["id"] for c in cs]), "seconds": round(secs, 2),
                                  "note": "自動のたたき台"})
        out.append({"code": code_, "cuts": f"{cs[0]['cut']}{cs[0]['panel']}〜{cs[-1]['cut']}{cs[-1]['panel']}",
                    "seconds": round(secs, 1), "over": secs > config.SHOT_MAX_SECONDS})
    db.log(conn, "agent", "plan_shots", {"episode": code, "shots": len(out)})
    return out


def set_shot(conn, code: str, shot_code: str, cut_names: list[str], note: str = "") -> dict:
    """cut_names は「S1-04」（カットの全コマ）か「S1-04②」（1コマ）。上映順に並べ直して保存する。"""
    ep = db.episode_by_code(conn, code)
    cuts = db.rows(conn.execute("SELECT id, cut, panel, seconds, seq FROM cuts WHERE episode_id=? ORDER BY seq",
                                (ep["id"],)))
    ids = [c["id"] for c in cuts if any(n in (c["cut"], f"{c['cut']}{c['panel']}") for n in cut_names)]
    if not ids:
        raise ValueError(f"コマが見つかりません：{cut_names}")
    secs = sum(c["seconds"] or 0 for c in cuts if c["id"] in ids)
    if secs > config.SHOT_MAX_SECONDS:
        raise ValueError(f"{secs:.1f}秒。1本は {config.SHOT_MAX_SECONDS}秒まで")
    # ほかのショットから外す
    for sh in db.rows(conn.execute("SELECT * FROM shots WHERE episode_id=? AND code!=?", (ep["id"], shot_code))):
        rest = [i for i in json.loads(sh["cut_ids_json"]) if i not in ids]
        if not rest:
            conn.execute("DELETE FROM shots WHERE id=?", (sh["id"],))
        elif len(rest) != len(json.loads(sh["cut_ids_json"])):
            rs = sum(c["seconds"] or 0 for c in cuts if c["id"] in rest)
            db.update(conn, "shots", sh["id"], {"cut_ids_json": json.dumps(rest), "seconds": round(rs, 2)})
    row = db.one(conn.execute("SELECT id FROM shots WHERE episode_id=? AND code=?", (ep["id"], shot_code)))
    seq = min(c["seq"] for c in cuts if c["id"] in ids)
    data = {"cut_ids_json": json.dumps(ids), "seconds": round(secs, 2), "note": note, "seq": seq}
    if row:
        db.update(conn, "shots", row["id"], data)
    else:
        db.insert(conn, "shots", {"episode_id": ep["id"], "code": shot_code, **data})
    db.log(conn, "agent", "set_shot", {"episode": code, "shot": shot_code, "cuts": cut_names})
    return {"shot": shot_code, "seconds": round(secs, 1), "panels": len(ids)}


def list_shots(conn, code: str) -> list[dict]:
    ep = db.episode_by_code(conn, code)
    cuts = {c["id"]: c for c in db.rows(conn.execute("SELECT * FROM cuts WHERE episode_id=?", (ep["id"],)))}
    out = []
    for sh in db.rows(conn.execute("SELECT * FROM shots WHERE episode_id=? ORDER BY seq", (ep["id"],))):
        cs = [dict(cuts[i]) for i in json.loads(sh["cut_ids_json"]) if i in cuts]
        for c in cs:     # 仮Vコンのコマ（あれば）を並べて見せる
            c.pop("raw_json", None)
            r = conn.execute("SELECT file_path FROM takes WHERE cut_id=? AND shot_id IS NULL AND file_path!='' "
                             "ORDER BY selected DESC, id DESC LIMIT 1", (c["id"],)).fetchone()
            c["thumb"] = r[0] if r else ""
        takes = db.rows(conn.execute("SELECT id, tier, status, selected FROM takes WHERE shot_id=? ORDER BY id",
                                     (sh["id"],)))
        out.append({**sh, "cuts": cs, "takes": takes,
                    "range": f"{cs[0]['cut']}{cs[0]['panel']}〜{cs[-1]['cut']}{cs[-1]['panel']}" if cs else ""})
    return out


# ---- プロンプトの骨組み ----

def _segments(cs: list[dict]) -> list[tuple[int, int, list[dict]]]:
    """コマの秒数を積み上げて整数秒の区切りにする。1区切りは同じカットのコマをまとめ、最低1秒。"""
    segs, t = [], 0.0
    for g in _cut_groups(cs):
        start = round(t)
        t += sum(c["seconds"] or 1 for c in g)
        end = max(start + 1, round(t))
        segs.append((start, end, g))
        t = max(t, end)
    return segs


def build_brief(conn, shot_id: int, tier: str = "draft") -> dict:
    sh = db.one(conn.execute("SELECT * FROM shots WHERE id=?", (shot_id,)))
    ids = json.loads(sh["cut_ids_json"])
    cuts = {c["id"]: c for c in db.rows(conn.execute(
        f"SELECT * FROM cuts WHERE id IN ({','.join('?' * len(ids))})", ids))}
    cs = [cuts[i] for i in ids]
    # カットの②③…はカメラ位置などを①から引き継ぐ
    heads = {}
    for c in cs:
        heads.setdefault(c["cut"], c)
        for k in ("camera_pos", "look", "camerawork", "layout"):
            if not c.get(k):
                c[k] = heads[c["cut"]].get(k)
    scene = db.one(conn.execute("SELECT * FROM scenes WHERE episode_id=? AND code=?", (sh["episode_id"], cs[0]["scene"])))

    # 参照：背景（カメラ位置ごと）→ 配置図 → キャラ（1人1枚）→ 小物。上限 REF_LIMIT
    cast, cams, refs, missing = [], [], [], []
    for c in cs:
        cast += [x for x in shotlib.cast_of(c) if x not in cast]
        pos = (c.get("camera_pos") or "").strip()
        if pos and pos not in cams and "寄り" not in pos and "俯瞰" not in pos:   # 寄り・俯瞰は同じ場所の背景を使う
            cams.append(pos)
    cast.sort(key=lambda x: shotlib.CAST_ORDER.index(x) if x in shotlib.CAST_ORDER else 99)
    for pos in cams:
        bg = shotlib._find_bg(conn, {"camera_pos": pos}, None)
        if bg and all(r[2] != bg["file_path"] for r in refs):   # 同じ画像は1回だけ渡す
            refs.append(("bg", bg["name"], bg["file_path"]))
        elif not bg:
            missing.append(f"背景（カメラ位置 {pos}）")
    layout = next(iter(shotlib.assets(conn, "layout")), None)
    if layout and "店" in f"{scene and scene['place']}":
        refs.append(("layout", layout["name"], layout["file_path"]))
    chars = {a["name"]: a for a in shotlib.assets(conn, "character")}
    for c in cast:
        if c in chars:
            refs.append(("character", c, chars[c]["file_path"]))
        else:
            missing.append(f"{c} の設定資料")
    text = " ".join(f"{c.get('picture')} {c.get('acting')} {c.get('layout')}" for c in cs)
    for p in shotlib.assets(conn, "prop"):
        if p["name"] in text:
            refs.append(("prop", p["name"], p["file_path"]))
    dropped = []
    while len(refs) > config.REF_LIMIT:   # 落とす順：小物 → 配置図 → 2枚目以降の背景
        for kind in ("prop", "layout", "bg"):
            idx = [i for i, r in enumerate(refs) if r[0] == kind]
            if idx and (kind != "bg" or len(idx) > 1):
                dropped.append(refs.pop(idx[-1])[1])
                break
        else:
            break
    tag = {}
    lines = ["ASSETS"]
    for i, (kind, name, _) in enumerate(refs, 1):
        tag[(kind, name)] = f"@Image {i}"
        lines.append(f"@Image {i}: {ROLE[kind].format(name=en(name) if kind == 'character' else name)}.")

    total = _segments(cs)[-1][1] if cs else 4
    duration = min(config.SHOT_MAX_SECONDS, max(4, total))
    lines += ["", "FORMAT", f"16:9 Japanese TV anime, cel-shaded, {duration} seconds, "
              f"{'480p draft' if tier == 'draft' else '1080p'}. Anime drawing with soft cel shadows, "
              "no pure black (#000000) outlines.", ""]
    look = {"B": "warm honey-colored bar light, shadows shifted to blue-violet",
            "C": "the same place one stop darker, shadows shifted to blue, quiet tension",
            "E": "delicate light gradation, beams through windows, dust in the light",
            "F": "desaturated cool town colors, faceless pedestrians walking the same way",
            "N": "only white and blue-gray, no warm colors"}
    summary = (f"SUMMARY\n{scene['place'] if scene else ''} {scene['time'] if scene else ''}。"
               f"{scene['purpose'] if scene else cs[0].get('intent') or ''}"
               f"（{'・'.join(cast) or '人物なし'}）。Look: {look.get((cs[0].get('look') or '')[:1], 'as described')}.")
    lines += [summary, "", "TIMELINE"]
    dict_rows = {}
    try:
        dict_rows = bible.acting_dictionary()
    except (OSError, IndexError):
        pass
    intent_done = set()
    for n, (a, b, g) in enumerate(_segments(cs), 1):
        c0 = g[0]
        who = [x for x in cast if any(x in f"{c.get('picture')}{c.get('acting')}{c.get('layout')}" for c in g)]
        ref_note = ", ".join(f"{en(x)} = {tag[('character', x)]}" for x in who if ('character', x) in tag)
        bg0 = shotlib._find_bg(conn, c0, None)
        bgtag = next((tag[(r[0], r[1])] for r in refs if r[0] == "bg" and bg0 and r[2] == bg0["file_path"]), "")
        lines.append(f"SHOT {n} [{a}-{b}s] {c0['cut']}  camera position {c0.get('camera_pos') or '-'}"
                     + (f" (set {bgtag})" if bgtag else "") + f", {c0.get('camerawork') or 'locked-off'}")
        if ref_note:
            lines.append(f"  Characters: {ref_note}")
        if c0.get("layout"):
            lines.append(f"  Screen layout: {c0['layout']}")
        for c in g:
            lines.append(f"  {c['panel']} ({c.get('seconds') or 1}s): {c.get('picture') or ''}"
                         + (f" / 芝居: {c['acting']}" if c.get("acting") else "")
                         + (f" / 表情: {c['emotion']}" if c.get("emotion") else ""))
            if c.get("dialogue"):
                for m in re.finditer(r"([^\s「」]+?)(（[^）]*）)?「([^」]*)」", c["dialogue"]):
                    off = " (off-screen voice; show the listener's reaction)" if m.group(2) and "OFF" in m.group(2) else ""
                    lines.append(f'  Dialogue ({en(m.group(1))}, Japanese){off}: "{m.group(3)}"')
            if c.get("sound"):
                lines.append(f"  SFX: {c['sound']}")
        for x in who:
            # シーン整理の「内心・したいこと」。英語の見える芝居（視線・手・間）に訳してから消す（点検で日本語が残ると止まる）
            ch = next((c for c in (json.loads(scene.get("characters_json") or "[]") if scene else []) if c.get("name") == x), None)
            if ch and x not in intent_done:
                intent_done.add(x)
                lines.append(f"  [translate to visible acting, then delete] {en(x)}: want={ch.get('want', '')} / "
                             f"inner={ch.get('inner', '')} / tension {ch.get('tension', '')}/5")
            row = dict_rows.get(x)
            if row:
                lines.append(f"  {en(x)} habits: {row['歩き方・立ち方']} / {row['物の持ち方']}")
    lines += ["", "CONTINUITY",
              "Each character's face, hair, outfit and colors follow their @Image sheet in every shot, "
              "including after cuts and angle changes.",
              f"Height order (tallest first): {HEIGHT_ORDER}.",
              "The bar interior is screen-right, the outside town is screen-left. Keep the camera on one side of "
              "the action within a shot unless the timeline says the camera is behind the counter (mirrored).",
              "Stella is an all-black cat including paws and tail tip."]
    if scene and scene.get("blocking"):
        lines.append(f"Blocking at scene start: {scene['blocking']}")
    if scene and scene.get("props"):
        lines.append(f"Props state: {scene['props']}")
    lines += ["", "AUDIO", "Dialogue lip-sync only. No background music. No subtitles.", "",
              "CONSTRAINTS", "No on-screen text, no subtitles, no logos. Hands with five fingers, objects stay in "
              "the hands that hold them."]
    if tier == "final":
        lines = ["EDIT", "Preserve the composition, camera position, timing, performance and lip movement of @Video 1. "
                 "Only re-render at 1080p with cleaner line art, color and fine detail.", ""] + lines
    return {"shot": sh["code"], "prompt": "\n".join(lines), "refs": [r[2] for r in refs],
            "ref_labels": [f"{r[0]}:{r[1]}" for r in refs], "duration": duration, "missing": missing,
            "dropped": dropped, "cast": cast}


# ---- 点検 ----

def lint(prompt: str, n_refs: int) -> list[str]:
    """エージェントが仕上げたプロンプトを、送る前に点検する。"""
    issues = []
    bound = {int(m) for m in re.findall(r"^@Image\s*(\d+)\s*:", prompt, re.M)}
    used = {int(m) for m in re.findall(r"@Image\s*(\d+)", prompt)}
    if n_refs and bound != set(range(1, n_refs + 1)):
        issues.append(f"参照 {n_refs} 枚のうち役割が書かれていないもの：{sorted(set(range(1, n_refs + 1)) - bound)}")
    if used - set(range(1, n_refs + 1)):
        issues.append(f"渡していない参照を使っている：{sorted(used - set(range(1, n_refs + 1)))}")
    if n_refs > config.REF_LIMIT:
        issues.append(f"参照が {n_refs} 枚。上限は {config.REF_LIMIT} 枚")
    spans = [(int(a), int(b)) for a, b in re.findall(r"\[(\d+)\s*-\s*(\d+)s\]", prompt)]
    if not spans:
        issues.append("タイムライン（SHOT n [a-bs]）がない")
    else:
        t = 0
        for a, b in spans:
            if a != t:
                issues.append(f"タイムラインに隙間か重なり：{t}s のあとが {a}s から")
            if b <= a:
                issues.append(f"区切り [{a}-{b}s] の長さが0以下")
            t = b
        if t > config.SHOT_MAX_SECONDS:
            issues.append(f"合計 {t}秒。1本は {config.SHOT_MAX_SECONDS}秒まで")
    if "[translate to visible acting" in prompt:
        issues.append("シーン整理の意図（[translate to visible acting…]）が残っている。見える芝居に訳して消す")
    if "No subtitles" not in prompt:
        issues.append("「No subtitles.」がない")
    if re.search(r"Dialogue \((?![^)]*Japanese)", prompt):
        issues.append("台詞に言語（Japanese）の指定がない行がある")
    # プロンプトは英語（台詞の中身だけ日本語）。骨組みの日本語（字コンテの文）が残っていないか
    jp = sum(len(re.findall(r"[\u3040-\u30ff\u4e00-\u9fff]", re.sub(r"\([^)]*\)", "", ln)))
             for ln in prompt.splitlines() if not ln.strip().startswith("Dialogue"))
    if jp > 20:
        issues.append(f"台詞以外に日本語が {jp} 文字。英語に直す（字コンテの文をそのまま残さない）")
    return issues
