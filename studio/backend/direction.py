"""演出のやり取り：配置図（区切りごとの立ち位置と動き）と、AI からの2択（選んだものを学ぶ）。

基本は AI が案を出し、監督が選ぶ／自分の案を出す。
- 配置図：シーンの区切りごとに、キャラが見取り図のどこにいるか。エージェントが案を置き、監督がコマを動かして直す。
  動きは「区切り2：あかね 席1→入口の横」のように言葉になって、字コンテとプロンプトに入る。
- 2択：迷ったところ（芝居・しぐさ・間）を A／B で聞く。選んだものは好みとして残り、
  「キャラの決まりにする」を選ぶと、キャラのノート（06_設定/キャラ/<名前>.md）の「## 追記」に書き足す。
"""
import json
import math

from . import config, db
from .importers import bible

PLAN_FILE = config.VAULT_DIR / "06_設定" / "舞台" / "配置図.json"


def plans() -> dict:
    try:
        data = json.loads(PLAN_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {k: v for k, v in data.items() if not k.startswith("_")}


def plan_for(place: str) -> tuple[str, dict]:
    """シーンの場所（「月灯り店内→控室」など）から見取り図を選ぶ。最初に書かれた場所を使う。"""
    first = (place or "").split("→")[0]
    for name, p in plans().items():
        if any(a in first for a in p.get("aliases", [name])):
            return name, p
    return "", {}


def spot_name(p: dict, xy) -> str:
    """座標にいちばん近い、名前のついた位置。遠ければ「客席の中央あたり」のように言う。"""
    if not xy or not p.get("spots"):
        return "?"
    name, (sx, sy) = min(p["spots"].items(), key=lambda kv: math.dist(kv[1], xy))
    return name if math.dist((sx, sy), xy) < 0.07 else f"{name}のあたり"


def _scene(conn, episode: str, scene: str) -> dict:
    ep = db.episode_by_code(conn, episode)
    sc = db.one(conn.execute("SELECT * FROM scenes WHERE episode_id=? AND code=?", (ep["id"], scene)))
    if not sc:
        raise ValueError(f"{episode} {scene} がない")
    return sc


def get_blocking(conn, episode: str, scene: str) -> dict:
    sc = _scene(conn, episode, scene)
    data = json.loads(sc.get("blocking_json") or "{}")
    name, p = plan_for(data.get("plan") or sc["place"])
    data.setdefault("plan", name)
    data.setdefault("frames", [])
    data["plan_data"] = plans().get(data["plan"], p)
    data["beats"] = json.loads(sc.get("beats_json") or "[]")
    data["text"] = blocking_text(data)
    return data


def set_blocking(conn, episode: str, scene: str, frames: list[dict], plan: str = "", by: str = "agent",
                 note: str = "") -> dict:
    """frames：[{"beat": 0, "pos": {"あかね": [x, y], …}}, …] 区切りごとの位置（0〜1）。
    エージェントの案は agent_frames にも残し、監督が動かしたあとでも「AI の案」と比べられるようにする。"""
    sc = _scene(conn, episode, scene)
    old = json.loads(sc.get("blocking_json") or "{}")
    data = {"plan": plan or old.get("plan") or plan_for(sc["place"])[0], "frames": frames, "by": by,
            "agent_frames": frames if by == "agent" else old.get("agent_frames", old.get("frames", [])),
            "note": note, "updated_at": db.now()}
    db.update(conn, "scenes", sc["id"], {"blocking_json": json.dumps(data, ensure_ascii=False)})
    before = blocking_text({**old, "plan": data["plan"]}) if old.get("frames") else []
    after = blocking_text(data)
    db.log(conn, by, "set_blocking", {"episode": episode, "scene": scene})
    return {"before": before, "after": after, "diff": [a for a in after if a not in before]}


def blocking_text(data: dict) -> list[str]:
    """区切りごとの立ち位置と動きを言葉にする（字コンテ・プロンプト・ブリーフ用）。"""
    p = plans().get(data.get("plan", ""), {})
    out, prev = [], {}
    for f in sorted(data.get("frames", []), key=lambda f: f.get("beat", 0)):
        parts = []
        for who, xy in f.get("pos", {}).items():
            here = spot_name(p, xy)
            if who in prev and math.dist(prev[who], xy) > 0.04 and spot_name(p, prev[who]) != here:
                parts.append(f"{who} {spot_name(p, prev[who])}→{here}")
            elif who not in prev:
                parts.append(f"{who}＝{here}")
        if parts:
            out.append(f"区切り{f.get('beat', 0) + 1}：" + "、".join(parts))
        prev.update(f.get("pos", {}))
    return out


# ---- AI からの2択 ----

def ask(conn, episode: str, question: str, options: list[str], scene: str = "", about: str = "",
        why: str = "", created_by: str = "agent") -> int:
    """迷ったところを A／B（3つ以上も可）で聞く。options は「目を合わせない。裾を握ったまま床を見る」のような短い文。"""
    ep = db.get_or_create_episode(conn, episode)
    cid = db.insert(conn, "choices", {
        "episode_id": ep["id"], "scene": scene, "about": about, "question": question, "why": why,
        "options_json": json.dumps([{"label": "ABCDE"[i], "text": t} for i, t in enumerate(options)], ensure_ascii=False),
        "created_by": created_by, "created_at": db.now()})
    db.log(conn, created_by, "ask_choice", {"choice": cid, "episode": episode, "scene": scene})
    return cid


def list_choices(conn, episode: str | None = None, status: str = "open,answered") -> list[dict]:
    st = status.split(",")
    q = f"SELECT c.*, e.code AS episode FROM choices c JOIN episodes e ON e.id=c.episode_id WHERE c.status IN ({','.join('?' * len(st))})"
    args = list(st)
    if episode:
        q += " AND e.code=?"
        args.append(episode)
    rows = db.rows(conn.execute(q + " ORDER BY c.status='open' DESC, c.id", args))
    for r in rows:
        r["options"] = json.loads(r.pop("options_json") or "[]")
    return rows


def answer(conn, choice_id: int, pick: str, note: str = "", keep: bool = False) -> dict:
    """監督の答え。pick は A/B/…、自分の案なら "other"（note に中身）。
    選んだものは好み（learnings, 承認済み）として残る。keep=True ならキャラのノートの「## 追記」にも書く。"""
    c = db.one(conn.execute("SELECT c.*, e.code AS episode FROM choices c JOIN episodes e ON e.id=c.episode_id WHERE c.id=?",
                            (choice_id,)))
    opts = {o["label"]: o["text"] for o in json.loads(c["options_json"] or "[]")}
    chosen = note if pick == "other" else opts.get(pick, "")
    if pick != "other" and note:
        chosen += f"（{note}）"
    rule = f"{c['question']} → {chosen}"
    where = f"（{c['episode']} {c['scene']}）" if c["scene"] else f"（{c['episode']}）"
    scope = f"character:{c['about']}" if keep and c["about"] else (f"episode:{c['episode']}" if not keep else "series")
    lid = db.insert(conn, "learnings", {"scope": scope, "rule_text": rule + where, "status": "approved",
                                        "source_review_ids": "[]", "created_at": db.now(), "decided_at": db.now(),
                                        "vault_target": f"06_設定/キャラ/{c['about']}.md" if keep and c["about"] else ""})
    written = ""
    if keep and c["about"]:
        written = append_character_note(c["about"], f"- {rule}{where}（監督が選択 {db.now()[:10]}）")
    db.update(conn, "choices", choice_id, {"answer": pick, "note": note, "keep": 1 if keep else 0,
                                           "status": "answered", "answered_at": db.now(), "learning_id": lid})
    db.log(conn, "human", "answer_choice", {"choice": choice_id, "pick": pick, "keep": keep})
    return {"learning": lid, "rule": rule, "written": written}


def append_character_note(name: str, line: str) -> str:
    """キャラのノートの「## 追記」の下に一行足す（bible の再生成でも残る場所）。"""
    path = config.VAULT_DIR / "06_設定" / "キャラ" / f"{name}.md"
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8").rstrip("\n")
    if bible.KEEP_MARK not in text:
        text += f"\n\n{bible.KEEP_MARK}\n"
    path.write_text(text + "\n" + line + "\n", encoding="utf-8")
    return str(path.relative_to(config.VAULT_DIR))
