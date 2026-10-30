"""AI スタッフ会議の見張り番。自分の役の枠が空いたら、その AI（Claude Code / Codex の CLI）を起こして取らせる。

  python studio/staff_watch.py codex            # AIスタッフ.json の assign で codex の役（演出）を見張る
  python studio/staff_watch.py claude-b --once  # 1回だけ見て、枠があれば起こして終わる
  python studio/staff_watch.py claude-a --dry   # 起こすコマンドを表示するだけ

起こすコマンドは 月灯_vault/04_制作ルール/AIスタッフ.json の agents.<名前>.command（{prompt} に指示が入る）。
AI は自分で `staff-claim` → ブリーフ → `staff-post` を、枠がなくなるまで繰り返す。
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from studio.backend import db, staff  # noqa: E402

PROMPT = ("月灯スタジオの AI スタッフ会議に参加する。あなたの名前は {agent}、役は {roles}。"
          "手順は studio/docs/AIスタッフ会議.md。python studio/cli.py staff-claim --agent {agent} で枠を取り、"
          "出てきたブリーフの書き方に沿って JSON を書き、staff-post（まとめ役なら staff-summarize）で出す。"
          "取れる枠がなくなるまで繰り返す。作品のルールは CLAUDE.md（Codex は AGENTS.md）。")


def waiting(agent: str, roles: list[str]) -> list[dict]:
    with db.session() as conn:
        return [s for s in staff.open_slots(conn)
                if s["role"] in roles and not (s["role"] == "見る" and s["made_by"] == agent)]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("agent")
    ap.add_argument("--every", type=int, default=60, help="何秒ごとに見るか")
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    db.init()
    st = staff.settings()
    roles = staff.roles_of(a.agent)
    cmd = st.get("agents", {}).get(a.agent, {}).get("command")
    if not roles or not cmd:
        sys.exit(f"{a.agent} の役か command が AIスタッフ.json にありません（assign と agents を見る）")
    print(f"{a.agent}（{'・'.join(roles)}）の枠を見張ります。止めるときは Ctrl+C")
    while True:
        slots = waiting(a.agent, roles)
        if slots:
            line = cmd.replace("{prompt}", PROMPT.format(agent=a.agent, roles="・".join(roles)))
            print(f"{time.strftime('%H:%M')} 枠 {len(slots)} 件 → {a.agent} を起こします")
            if a.dry:
                print(line)
            else:
                try:
                    subprocess.run(line, shell=True, cwd=ROOT, timeout=45 * 60)
                except subprocess.TimeoutExpired:
                    print("45分で打ち切りました（枠は claimed のまま。staff-rounds で確かめる）")
        if a.once:
            return
        time.sleep(a.every)


if __name__ == "__main__":
    main()
