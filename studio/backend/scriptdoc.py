"""脚本をツールの中で読み・直し・注をつける。シーンへの分割は脚本の「○場所（時間）」の行から自動で。"""
import json
import re
import shutil
import time

from . import config, core, db


def path(code: str):
    return config.VAULT_DIR / "03_脚本" / "いまの版" / f"{code}_脚本_いまの版.md"


def read(conn, code: str) -> dict:
    p = path(code)
    ep = db.episode_by_code(conn, code)
    notes = db.rows(conn.execute("SELECT * FROM script_notes WHERE episode_id=? ORDER BY id", (ep["id"],))) if ep else []
    return {"exists": p.exists(), "text": p.read_text(encoding="utf-8") if p.exists() else "",
            "path": f"{config.VAULT_DIR.name}/{p.relative_to(config.VAULT_DIR).as_posix()}", "notes": notes}


def save(conn, code: str, text: str, by: str = "human") -> dict:
    """監督が脚本を直した。前の版は 03_脚本/前の版 に取っておき、制作進行にシーン整理の見直しを頼む。"""
    p = path(code)
    old = p.read_text(encoding="utf-8") if p.exists() else ""
    if old == text:
        return {"changed": False}
    if old:
        keep = config.VAULT_DIR / "03_脚本" / "前の版" / f"{code}_脚本_{db.now()[:10]}_{int(time.time())}.md"
        keep.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, keep)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    ep = db.episode_by_code(conn, code)
    o, n = old.splitlines(), text.splitlines()
    gone = [l for l in o if l not in n and l.strip()][:8]
    came = [l for l in n if l not in o and l.strip()][:8]
    core.add_review(conn, target_type="episode", target_id=ep["id"], verdict="修正", tags=["意図"],
                    comment="[脚本] 監督が直した（正）：" + " ／ ".join([f"「{a}」→「{b}」" for a, b in zip(gone, came)]
                                                       + [f"足した「{b}」" for b in came[len(gone):]] + [f"消した「{a}」" for a in gone[len(came):]]))
    added = split(conn, code, only_new=True)
    if by == "human":
        rid = core.add_request(conn, f"[脚本の直し {code}] 監督が脚本を直した。直った所に関わるシーン整理（あらすじ・変化・キャラ）と、"
                                     "できていれば字コンテを見直す。監督が直した欄は書き換えない。", code)
        db.update(conn, "requests", rid, {"role": "まとめ"})
    return {"changed": True, "new_scenes": added}


def add_note(conn, code: str, anchor: str, note: str) -> int:
    """脚本の行に注をつける（監督のメモ。AI は脚本と一緒に読む）。"""
    ep = db.episode_by_code(conn, code)
    nid = db.insert(conn, "script_notes", {"episode_id": ep["id"], "anchor": anchor, "note": note, "created_at": db.now()})
    core.add_review(conn, target_type="episode", target_id=ep["id"], verdict="修正", tags=["意図"],
                    comment=f"[脚本の注] 「{anchor[:40]}」に：{note}")
    return nid


HEAD = re.compile(r"^(?:#+\s*)?[○〇◯]\s*(.+?)\s*$")


def scenes_in(text: str) -> list[dict]:
    """「○場所（時間）」の行で区切る。同じ場所でも行が変われば別のシーン。"""
    lines = text.splitlines()
    heads = [(i, HEAD.match(l.strip())) for i, l in enumerate(lines)]
    heads = [(i, m) for i, m in heads if m]
    out = []
    for k, (i, m) in enumerate(heads):
        end = heads[k + 1][0] if k + 1 < len(heads) else len(lines)
        body = [l for l in lines[i + 1:end] if l.strip() and l.strip() not in ("×××", "× × ×")]
        title = m.group(1)
        tm = re.search(r"[（(]([^）)]+)[）)]\s*$", title)
        out.append({"heading": title, "place": re.sub(r"[（(][^）)]*[）)]\s*$", "", title).strip(),
                    "time": tm.group(1) if tm else "", "script_from": lines[i].lstrip("# ").strip(),
                    "script_to": body[-1].replace("**", "").strip() if body else lines[i].lstrip("# ").strip(),
                    "lines": len(body)})
    return out


def split(conn, code: str, only_new: bool = False) -> int:
    """脚本からシーンを作る（S1, S2 …）。すでにあるシーンは触らない（only_new のときは、まだシーンがない話数だけ）。"""
    ep = db.episode_by_code(conn, code)
    have = conn.execute("SELECT COUNT(*) FROM scenes WHERE episode_id=?", (ep["id"],)).fetchone()[0]
    if have and only_new:
        return 0
    p = path(code)
    if not p.exists():
        return 0
    sc = scenes_in(p.read_text(encoding="utf-8"))
    total = sum(s["lines"] for s in sc) or 1
    for k, s in enumerate(sc, 1):
        core.set_scene(conn, code, f"S{k}", actor="studio", seq=k, place=s["place"], time=s["time"], script_from=s["script_from"],
                       script_to=s["script_to"], status="draft",
                       target_seconds=round((ep.get("target_seconds") or 180) * s["lines"] / total))
    db.log(conn, "studio", "split_scenes", {"episode": code, "scenes": len(sc)})
    return len(sc)
