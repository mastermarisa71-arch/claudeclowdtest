"""AI スタッフ会議：複数の AI（Claude・Codex …）が役割を分けて、演出をレビューし合う。

流れ（1回の会議＝ラウンド）
1. 開く：対象（シーン S1 / ショット SH03 / テイク #31 / 話数全体）を決めて会議を開く。役ごとに「枠」ができる。
2. 1周目：各役（芝居・演出・見る）が、ほかの役の意見を見ずに所見を書く（つられないように）。
3. 2周目：ほかの役の所見を読んで、賛成・反対・補足を書く。
4. まとめ：まとめ役が、合意したもの→作り直しの依頼、割れたもの→監督への2択、弱いもの→見送り に分ける。

どの AI がどの役をやるかは 月灯_vault/04_制作ルール/AIスタッフ.json。各 AI は「枠を取る」→「ブリーフを読む」→「書く」だけ。
同じ対象の会議は、監督が何か返すまでに max_rounds_per_target 回まで（AI どうしで回り続けないように）。
"""
import json
import re

from . import config, core, db, direction, versions
from .importers import bible

STAFF_FILE = config.VAULT_DIR / "04_制作ルール" / "AIスタッフ.json"
REVIEW_ROLES = ("芝居", "演出", "見る")
LEAD = "まとめ"


def settings() -> dict:
    try:
        return json.loads(STAFF_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"roles": {}, "assign": {}, "agents": {}, "rules": {}}


def roles_of(agent: str) -> list[str]:
    return [r for r, a in settings().get("assign", {}).items() if a == agent]


def _last_human(conn, episode_id: int) -> str:
    """監督がこの話数に最後に何か返した時刻（レビュー・2択の答え・配置図）。"""
    ts = [conn.execute("SELECT MAX(created_at) FROM reviews WHERE episode_id=? AND created_by='human'", (episode_id,)).fetchone()[0],
          conn.execute("SELECT MAX(answered_at) FROM choices WHERE episode_id=? AND status='answered'", (episode_id,)).fetchone()[0]]
    return max([t for t in ts if t] or [""])


def open_round(conn, episode: str, target: str, title: str = "", roles: list[str] | None = None,
               created_by: str = "agent", made_by: str = "", note: str = "") -> int:
    """会議を開く。target は S1 / SH03 / #31（テイク）/ 空（話数全体）。made_by は対象を作った AI（「見る」役から外す）。"""
    ep = db.get_or_create_episode(conn, episode)
    rules = settings().get("rules", {})
    limit = int(rules.get("max_rounds_per_target", 2))
    if created_by != "human":
        since = _last_human(conn, ep["id"])
        n = conn.execute("SELECT COUNT(*) FROM rounds WHERE episode_id=? AND target=? AND status!='cancelled' AND created_at>?",
                         (ep["id"], target, since)).fetchone()[0]
        if n >= limit:
            raise core.Blocked(f"{episode} {target or '全体'} の会議は、監督が返すまでに {limit} 回まで。いまの所見を監督に見せて判断をもらう")
    rid = db.insert(conn, "rounds", {
        "episode_id": ep["id"], "target": target, "title": title or f"{target or episode} の検討",
        "note": note, "passes": int(rules.get("passes", 2)), "made_by": made_by, "created_by": created_by,
        "status": "open", "created_at": db.now()})
    for r in roles or REVIEW_ROLES:
        db.insert(conn, "round_slots", {"round_id": rid, "role": r, "pass": 1, "status": "open"})
    db.log(conn, created_by, "open_round", {"round": rid, "episode": episode, "target": target})
    return rid


def claim(conn, agent: str, roles: list[str] | None = None, round_id: int | None = None) -> dict | None:
    """自分の役の、空いている枠を1つ取る（いちばん古いもの）。ほかの AI と同じ枠は取れない。"""
    roles = roles or roles_of(agent)
    if not roles:
        return None
    q = (f"SELECT s.*, r.made_by FROM round_slots s JOIN rounds r ON r.id=s.round_id WHERE s.status='open' AND r.status='open' "
         f"AND s.role IN ({','.join('?' * len(roles))})" + (" AND s.round_id=?" if round_id else "") + " ORDER BY s.id")
    for s in db.rows(conn.execute(q, [*roles, *([round_id] if round_id else [])])):
        if s["role"] == "見る" and s["made_by"] and s["made_by"] == agent:
            continue   # 作った本人は「見る」をやらない
        cur = conn.execute("UPDATE round_slots SET status='claimed', agent=?, claimed_at=? WHERE id=? AND status='open'",
                           (agent, db.now(), s["id"]))
        if cur.rowcount == 1:
            db.log(conn, agent, "claim_slot", {"slot": s["id"], "round": s["round_id"], "role": s["role"]})
            return {**s, "status": "claimed", "agent": agent}
    return None


def _round(conn, round_id: int) -> dict:
    r = db.one(conn.execute("SELECT r.*, e.code AS episode FROM rounds r JOIN episodes e ON e.id=r.episode_id WHERE r.id=?",
                            (round_id,)))
    if not r:
        raise ValueError(f"会議 #{round_id} がない")
    return r


def _posts(conn, round_id: int) -> list[dict]:
    rows = db.rows(conn.execute("SELECT * FROM round_posts WHERE round_id=? ORDER BY id", (round_id,)))
    for p in rows:
        p["items"] = json.loads(p.pop("items_json") or "[]")
    return rows


# ---- ブリーフ：役ごとに、見るものと書き方 ----

def _target_material(conn, r: dict) -> list[str]:
    ep_code, target = r["episode"], r["target"] or ""
    sc_all = core.scenes(conn, ep_code)["scenes"]
    out, scene_codes, cut_rows, takes = [], [], [], []
    if re.fullmatch(r"S\d+", target):
        scene_codes = [target]
    elif re.fullmatch(r"SH\d+", target):
        sh = db.one(conn.execute("SELECT * FROM shots WHERE episode_id=? AND code=?", (r["episode_id"], target)))
        if sh:
            ids = json.loads(sh["cut_ids_json"])
            cut_rows = db.rows(conn.execute(f"SELECT * FROM cuts WHERE id IN ({','.join('?' * len(ids))}) ORDER BY seq", ids))
            scene_codes = sorted({c["scene"] for c in cut_rows})
            takes = db.rows(conn.execute("SELECT * FROM takes WHERE shot_id=? ORDER BY id DESC LIMIT 3", (sh["id"],)))
            out += [f"### ショット {target}（{sh['seconds']}秒）：{sh['note']}"]
    elif re.fullmatch(r"#?\d+", target):
        t = db.one(conn.execute("SELECT * FROM takes WHERE id=?", (int(target.lstrip("#")),)))
        if t:
            takes = [t]
            if t.get("cut_id"):
                cut_rows = db.rows(conn.execute("SELECT * FROM cuts WHERE id=?", (t["cut_id"],)))
                scene_codes = [cut_rows[0]["scene"]] if cut_rows else []
    else:
        out += ["### 話数全体（シーンごとの変化と展開のカーブ）"]
        for s in sc_all:
            peaks = [f"★{b['peak']}" for b in s["beats"] if b.get("peak")]
            out.append(f"- {s['code']} {s['target_seconds']}秒 [{s['status']}] {s['change_before']} → {s['change_after']} "
                       f"高さ {[b.get('level') for b in s['beats']]} {' '.join(peaks)}")
    for code in scene_codes:
        s = next((x for x in sc_all if x["code"] == code), None)
        if not s:
            continue
        out += [f"### シーン整理 {code}（{s['place']}・{s['time']}、目標 {s['target_seconds']}秒、今の字コンテ {s['actual_seconds']}秒）",
                f"- 見せたいもの：{s['purpose']}", f"- 変化：{s['change_before']} → {s['change_after']}（きっかけ：{s['turn']}）"]
        out += [f"- {c.get('name')}：したい＝{c.get('want')}／する＝{c.get('does')}／内心＝{c.get('inner')}／温度{c.get('tension')}"
                for c in s["characters"]]
        out += [f"- 区切り{k + 1}（{b.get('seconds')}秒・高さ{b.get('level', '?')}{'・★' + b['peak'] if b.get('peak') else ''}）"
                f"{b.get('who')}：{b.get('does')} ― {b.get('why', '')}" for k, b in enumerate(s["beats"])]
        out += [f"- 配置図 {t}" for t in s["blocking_text"]]
        try:
            acting = bible.acting_dictionary()
        except (OSError, IndexError):
            acting = {}
        for c in s["characters"]:
            row = acting.get(c.get("name"))
            if row:
                out.append(f"- {c['name']}の芝居の辞書：" + "／".join(f"{k}＝{v}" for k, v in row.items()))
            note = config.VAULT_DIR / "06_設定" / "キャラ" / f"{c.get('name')}.md"
            if note.exists() and bible.KEEP_MARK in note.read_text(encoding="utf-8"):
                tail = [l for l in note.read_text(encoding="utf-8").split(bible.KEEP_MARK, 1)[1].splitlines()
                        if l.strip() and not l.strip().startswith("（")]
                if tail:
                    out.append(f"- {c['name']}の決まり（追記）：" + " ".join(tail[-6:]))
        if not cut_rows or len(scene_codes) == 1 and not re.fullmatch(r"SH\d+|#?\d+", target):
            cut_rows = db.rows(conn.execute("SELECT * FROM cuts WHERE episode_id=? AND scene=? ORDER BY seq", (r["episode_id"], code)))
        script = core.scene_script(conn, ep_code, code)
        if script["found"]:
            out += ["", f"脚本（{script['heading']}）："] + [f"  {l}" for l in script["lines"][:40]]
    if cut_rows:
        out += ["", "### 字コンテ（コマ／秒／カメラ位置／カメラワーク／画面／芝居／台詞）"]
        out += [f"- {c['cut']}{c['panel'] or ''} {c['seconds']}s {c['camera_pos'] or ''} {c['camerawork'] or ''}｜{c['picture'] or ''}"
                f"｜{c['acting'] or ''}｜{c['dialogue'] or ''}" for c in cut_rows]
        if not takes:
            ids = [c["id"] for c in cut_rows]
            takes = db.rows(conn.execute(f"SELECT * FROM takes WHERE cut_id IN ({','.join('?' * len(ids))}) AND file_path!='' "
                                         f"ORDER BY id DESC LIMIT 6", ids))
    if takes:
        out += ["", "### できたもの（見る役は必ず画像を見る）"]
        for t in takes:
            hint = (f"`python studio/cli.py contact {t['id']} --frames 12`（コマ送りの画像を作って見る）" if t["kind"] == "video"
                    else f"{config.MEDIA_DIR / t['file_path']}" if t["file_path"] else "（まだファイルがない）")
            out.append(f"- テイク #{t['id']} {t['kind']} {t.get('tier') or ''} {t['status']}：{t['agent_note'] or ''}　→ {hint}")
    else:
        out += ["", "（まだ絵・動画はない。文章・配置図・字コンテの段でレビューする）"]
    return out


def _director_intent(conn, r: dict) -> list[str]:
    out = ["### 監督の意図（これに合っているかで見る）"]
    target = r["target"] or ""
    revs = db.rows(conn.execute("SELECT comment, verdict FROM reviews WHERE episode_id=? AND created_by='human' "
                                "ORDER BY id DESC LIMIT 30", (r["episode_id"],)))
    revs = [v for v in revs if not re.fullmatch(r"S\d+", target) or target in v["comment"]] or revs[:8]
    out += [f"- レビュー（{v['verdict']}）：{v['comment']}" for v in revs[:12]] or ["- （まだレビューなし）"]
    ch = [c for c in direction.list_choices(conn, r["episode"], "answered") if not c["scene"] or not target or c["scene"] == target]
    out += [f"- 2択で選んだもの：{c['question']} → "
            + (c["note"] if c["answer"] == "other" else next((o["text"] for o in c["options"] if o["label"] == c["answer"]), ""))
            for c in ch]
    learned = db.rows(conn.execute("SELECT scope, rule_text FROM learnings WHERE status='approved' ORDER BY id DESC LIMIT 20"))
    out += [f"- 承認済みのルール [{l['scope']}]：{l['rule_text']}" for l in learned]
    if r["note"]:
        out.append(f"- この会議で見てほしいこと：{r['note']}")
    return out


POST_FORMAT = """### 書き方（これだけ守る）
所見は `python studio/cli.py staff-post <枠> --agent <自分の名前> --file post.json`（MCP なら staff_post）で出す。post.json：
{"summary": "ひとことで（1行）",
 "items": [{"severity": "必須|提案|好み", "at": "S1 区切り2 / S1-04 / 12.5秒 など", "what": "何が問題か（見たまま）",
            "fix": "どう直すか（具体的に。秒・カメラ・芝居・配置）", "agree": "（2周目のみ）賛成/反対/補足 と相手の役"}]}
- 必須＝直さないと意図が伝わらない。提案＝良くなる。好み＝どちらでもよい
- 自分の役の観点だけ書く（ほかの役の仕事に踏み込まない）。指摘は多くても5つまで、重い順
- 監督の意図・2択で決まったこと・承認済みのルールに反する提案はしない（変えたいなら「好み」で理由を書く）"""

LEAD_FORMAT = """### まとめの書き方
**監督は文章より「やった版」を見たい。** 直す（do）には、できるだけ version（直した並び）をつける。割れた（ask）には versions（A の版・B の版）をつける。
今の並びは `python studio/cli.py version-base <話数> <シーン>` で出る。それを直して version.entries にする：
  {"cut": "S1-05③", "seconds": 2.0, "move": "track_in"}（今のコマ・変えるところだけ）／ {"new": "黒板（前の日のまま）", "seconds": 0.8}（新しいコマ）／ 書かなかったコマは削る
  move：track_in（寄る）/ track_out（引く）/ pan_left / pan_right / tilt_up / tilt_down

`python studio/cli.py staff-summarize <枠> --agent <自分の名前> --file summary.json`（MCP なら staff_summarize）。summary.json：
{"summary": "会議の結論（2〜3行）",
 "items": [{"decision": "do",   "text": "作り直し・直しの内容（そのまま依頼になる）"},
           {"decision": "do",   "text": "S1 を30秒に詰める", "version": {"title": "30秒に詰めた版", "entries": [ … ]}},
           {"decision": "ask",  "text": "監督への質問", "options": ["A の案", "B の案"], "about": "キャラ名か演出", "why": "どの役とどの役で割れたか",
            "versions": [{"title": "A の版", "entries": [ … ]}, {"title": "B の版", "entries": [ … ]}]},
           {"decision": "drop", "text": "見送るもの", "why": "理由"}]}
- 役どうしで割れたものは、勝手に決めずに ask（2択）。同じことを前にも聞いていないか、ブリーフの「2択で選んだもの」を見る
- do は安い工程（シーン整理・配置図・字コンテ・9コマ・480p）だけ。1080p は監督の採用なしに進めない
- 必須が残っているのに do にできない（予算・作り直しの上限）ときは ask で監督に回す"""


def brief(conn, slot_id: int) -> str:
    s = db.one(conn.execute("SELECT * FROM round_slots WHERE id=?", (slot_id,)))
    r = _round(conn, s["round_id"])
    st = settings()
    role = st.get("roles", {}).get(s["role"], {})
    out = [f"# AI スタッフ会議 #{r['id']}　{r['title']}　（{r['episode']} {r['target'] or '全体'}）",
           f"あなたの役：**{role.get('name', s['role'])}**（{s['pass']}周目）" if s["role"] != LEAD else "あなたの役：**まとめ**",
           f"見るところ：{role.get('focus', '')}", ""]
    out += ["### この役の見方"] + [f"- {c}" for c in role.get("checklist", [])] + [""]
    out += _director_intent(conn, r) + [""]
    out += _target_material(conn, r) + [""]
    posts = _posts(conn, r["id"])
    if s["role"] == LEAD or s["pass"] >= 2:
        out += ["### ほかの役の所見"]
        for p in posts:
            if p["kind"] == "まとめ":
                continue
            out.append(f"- [{p['role']}・{p['pass']}周目・{p['agent']}] {p['summary']}")
            out += [f"    - ({i.get('severity')}) {i.get('at', '')}：{i.get('what', '')} → {i.get('fix', '')}"
                    + (f"［{i['agree']}］" if i.get("agree") else "") for i in p["items"]]
        out.append("")
    if s["role"] == LEAD:
        out.append(LEAD_FORMAT)
    else:
        out.append(POST_FORMAT.replace("<枠>", str(slot_id)))
        if s["pass"] >= 2:
            out.append("- 2周目：ほかの役の指摘に、自分の役の観点から 賛成／反対／補足 を書く（agree に）。新しい指摘は必須のものだけ")
    out.append(f"\n枠の番号：{slot_id}")
    return "\n".join(out).replace("<枠>", str(slot_id))


# ---- 書く・まとめる ----

def post(conn, slot_id: int, agent: str, summary: str, items: list[dict]) -> dict:
    s = db.one(conn.execute("SELECT * FROM round_slots WHERE id=?", (slot_id,)))
    if not s or s["status"] == "done":
        raise ValueError(f"枠 {slot_id} はもう終わっているか、ない")
    if s["role"] == LEAD:
        raise ValueError("まとめの枠は staff-summarize で")
    if s["agent"] and s["agent"] != agent:
        raise ValueError(f"枠 {slot_id} は {s['agent']} が取っている")
    pid = db.insert(conn, "round_posts", {"round_id": s["round_id"], "role": s["role"], "pass": s["pass"], "agent": agent,
                                          "kind": "所見" if s["pass"] == 1 else "討議", "summary": summary,
                                          "items_json": json.dumps(items, ensure_ascii=False), "created_at": db.now()})
    db.update(conn, "round_slots", slot_id, {"status": "done", "agent": agent, "done_at": db.now()})
    db.log(conn, agent, "staff_post", {"round": s["round_id"], "role": s["role"], "pass": s["pass"]})
    return {"post": pid, "next": _advance(conn, s["round_id"])}


def _advance(conn, round_id: int) -> str:
    """周回を進める：1周目が全部そろったら2周目の枠、最後の周が終わったら、まとめの枠を作る。"""
    r = _round(conn, round_id)
    slots = db.rows(conn.execute("SELECT * FROM round_slots WHERE round_id=?", (round_id,)))
    cur = max(x["pass"] for x in slots if x["role"] != LEAD)
    if any(x["status"] != "done" for x in slots if x["pass"] == cur and x["role"] != LEAD):
        return "ほかの役を待っています"
    if any(x["role"] == LEAD for x in slots):
        return "まとめを待っています"
    if cur < r["passes"]:
        for x in slots:
            if x["pass"] == cur and x["role"] != LEAD:
                db.insert(conn, "round_slots", {"round_id": round_id, "role": x["role"], "pass": cur + 1, "status": "open"})
        db.update(conn, "rounds", round_id, {"stage": f"{cur + 1}周目"})
        return f"{cur + 1}周目（討議）の枠を作りました"
    db.insert(conn, "round_slots", {"round_id": round_id, "role": LEAD, "pass": cur + 1, "status": "open"})
    db.update(conn, "rounds", round_id, {"stage": "まとめ"})
    return "まとめの枠を作りました"


def summarize(conn, slot_id: int, agent: str, summary: str, items: list[dict]) -> dict:
    """まとめ：do → 作り直しの依頼、ask → 監督への2択、drop → 見送り（記録だけ）。会議を閉じる。"""
    s = db.one(conn.execute("SELECT * FROM round_slots WHERE id=?", (slot_id,)))
    if not s or s["role"] != LEAD or s["status"] == "done":
        raise ValueError(f"枠 {slot_id} はまとめの枠ではないか、もう終わっている")
    if s["agent"] and s["agent"] != agent:
        raise ValueError(f"枠 {slot_id} は {s['agent']} が取っている")
    r = _round(conn, s["round_id"])
    scene = r["target"] if re.fullmatch(r"S\d+", r["target"] or "") else ""
    made = {"requests": [], "choices": [], "versions": []}
    vscene = scene or next((i.get("scene") for i in items if i.get("scene")), "")
    reasons = [{"role": p["role"], "text": p["summary"]} for p in _posts(conn, r["id"]) if p["kind"] == "所見"]
    # 案（直した版）がついた do は、作り直しの前に監督が今の版と並べて見る
    for i in items:
        if i.get("decision") == "do" and i.get("version") and vscene:
            vv = i["version"]
            made["versions"].append(versions.add(conn, r["episode"], vv.get("scene", vscene), vv.get("title") or i["text"][:30],
                                                 vv["entries"], i["text"], r["id"], vv.get("by_role", ""), agent, reasons))
    todo = [i["text"] for i in items if i.get("decision") == "do" and not i.get("version")]
    if todo:
        made["requests"].append(core.add_request(
            conn, f"[AI スタッフ会議 #{r['id']} {r['target'] or '全体'}] 次を直して、テイクの --note に会議の番号を書く：\n"
                  + "\n".join(f"- {t}" for t in todo), r["episode"]))
    for i in items:
        if i.get("decision") == "ask" and len(i.get("options") or []) >= 2:
            cid = direction.ask(conn, r["episode"], i["text"], i["options"], scene, i.get("about", ""),
                                i.get("why", "") + f"（AI スタッフ会議 #{r['id']}）", created_by=agent)
            made["choices"].append(cid)
            # 選択肢ごとの版（versions）があれば、2択を「並べて見て選ぶ」にする
            for k, vv in enumerate(i.get("versions") or []):
                if vv and vscene:
                    made["versions"].append(versions.add(conn, r["episode"], vv.get("scene", vscene), vv.get("title") or i["options"][k][:30],
                                                         vv["entries"], i["options"][k], r["id"], "", agent, reasons,
                                                         choice_id=cid, option="ABCDE"[k]))
    db.insert(conn, "round_posts", {"round_id": r["id"], "role": LEAD, "pass": s["pass"], "agent": agent, "kind": "まとめ",
                                    "summary": summary, "items_json": json.dumps(items, ensure_ascii=False), "created_at": db.now()})
    db.update(conn, "round_slots", slot_id, {"status": "done", "agent": agent, "done_at": db.now()})
    db.update(conn, "rounds", r["id"], {"status": "closed", "stage": "済み", "result_json": json.dumps(made), "closed_at": db.now()})
    db.log(conn, agent, "staff_summarize", {"round": r["id"], **made})
    return made


def list_rounds(conn, episode: str | None = None, status: str = "open,closed") -> list[dict]:
    st = status.split(",")
    q = (f"SELECT r.*, e.code AS episode FROM rounds r JOIN episodes e ON e.id=r.episode_id "
         f"WHERE r.status IN ({','.join('?' * len(st))})" + (" AND e.code=?" if episode else "") + " ORDER BY r.id DESC")
    rows = db.rows(conn.execute(q, [*st, *([episode] if episode else [])]))
    for r in rows:
        r["slots"] = db.rows(conn.execute("SELECT * FROM round_slots WHERE round_id=? ORDER BY pass, id", (r["id"],)))
        r["posts"] = _posts(conn, r["id"])
        r["result"] = json.loads(r.pop("result_json") or "{}")
    return rows


def open_slots(conn) -> list[dict]:
    return db.rows(conn.execute("SELECT s.*, r.made_by FROM round_slots s JOIN rounds r ON r.id=s.round_id "
                                "WHERE s.status='open' AND r.status='open' ORDER BY s.id"))
