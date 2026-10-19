"""SQLite のスキーマと小さなヘルパー。

中心になる考え方：
- 「作るのはエージェント、見るのは人」。どの工程の成果物（脚本・字コンテ・プロンプト・画像・動画・音声・編集）も
  take として残し、それに review をつける。
- review は「どこが」「なぜ」を構造化して残す（verdict・観点タグ・画面上の範囲・タイムコード）。
- comparison は「AとBならAが良い、理由はこう」を観点ごとに残す。エージェントへ好みを伝える一番強い手段。
- learning は、レビューのくり返しからエージェントが提案する「次からのルール」。人が承認したものだけ使う。
"""
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS episodes (
  id INTEGER PRIMARY KEY,
  code TEXT UNIQUE NOT NULL,           -- EP01
  title TEXT DEFAULT '',
  target_seconds REAL DEFAULT 180,     -- 目標尺
  stage TEXT DEFAULT '脚本',           -- 脚本/設計/字コンテ/プロンプト/生成/編集/完成
  note TEXT DEFAULT ''
);

-- 文章の成果物（脚本・演出設計・字コンテ・9コマプロンプト・指示書）。版ごとに1行。
CREATE TABLE IF NOT EXISTS documents (
  id INTEGER PRIMARY KEY,
  episode_id INTEGER REFERENCES episodes(id),
  kind TEXT NOT NULL,                  -- script/design/jikonte/prompt/instruction
  version TEXT NOT NULL,               -- v6, 楓華案 など
  path TEXT,                           -- vault 内の相対パス
  parent_id INTEGER REFERENCES documents(id),
  created_by TEXT DEFAULT 'agent',     -- agent/human
  summary TEXT DEFAULT '',             -- エージェントが書く「前の版から何を変えたか」
  created_at TEXT
);

-- 字コンテの1行＝1コマ。cut は S1-02、panel は ①。
CREATE TABLE IF NOT EXISTS cuts (
  id INTEGER PRIMARY KEY,
  episode_id INTEGER REFERENCES episodes(id),
  document_id INTEGER REFERENCES documents(id),
  seq INTEGER,                         -- 上映順
  scene TEXT, cut TEXT, panel TEXT,
  seconds REAL,                        -- コマ尺
  look TEXT, viewpoint TEXT, camera_pos TEXT, layout TEXT, camerawork TEXT,
  to_video TEXT,                       -- 動画化（始点・終点のコマとカメラの動き）
  picture TEXT, acting TEXT, emotion TEXT, dialogue TEXT, sound TEXT,
  intent TEXT, edit_memo TEXT,
  raw_json TEXT                        -- 元の行（列名→値）
);

-- 生成結果・成果物の1回分。parent_take_id で「何を直して作り直したか」の系譜をたどる。
CREATE TABLE IF NOT EXISTS takes (
  id INTEGER PRIMARY KEY,
  episode_id INTEGER REFERENCES episodes(id),
  cut_id INTEGER REFERENCES cuts(id),  -- シート（9コマ）など複数コマにまたがるときは NULL
  kind TEXT NOT NULL,                  -- sheet/image/video/audio/edit/text
  provider TEXT DEFAULT 'manual',      -- hamster/runway/elevenlabs/seedance/comfyui/manual
  model TEXT DEFAULT '',
  prompt TEXT DEFAULT '',
  params_json TEXT DEFAULT '{}',
  refs_json TEXT DEFAULT '[]',         -- 参照画像（添付順を保つ）
  parent_take_id INTEGER REFERENCES takes(id),
  fixes_review_ids TEXT DEFAULT '[]',  -- このテイクで直そうとしたレビュー
  agent_note TEXT DEFAULT '',          -- エージェントの意図（何を狙い、何を変えたか）
  status TEXT DEFAULT 'done',          -- queued/running/awaiting_upload/done/failed
  external_job_id TEXT DEFAULT '',
  error TEXT DEFAULT '',
  file_path TEXT DEFAULT '',           -- MEDIA_DIR からの相対パス
  selected INTEGER DEFAULT 0,          -- このコマに採用中
  created_by TEXT DEFAULT 'agent',
  created_at TEXT
);

-- レビュー。対象はテイク・コマ・文書・話数のどれでもよい。
CREATE TABLE IF NOT EXISTS reviews (
  id INTEGER PRIMARY KEY,
  episode_id INTEGER REFERENCES episodes(id),
  target_type TEXT NOT NULL,           -- take/cut/document/episode
  target_id INTEGER NOT NULL,
  verdict TEXT DEFAULT '修正',         -- 採用/良い/保留/修正/却下
  score INTEGER,                       -- 1〜5（任意）
  tags TEXT DEFAULT '',                -- 構図,芝居,表情,キャラ崩れ,配置,光,尺,意図 …（カンマ区切り）
  comment TEXT DEFAULT '',
  region_json TEXT DEFAULT '',         -- {"x":0.1,"y":0.2,"w":0.3,"h":0.2} 正規化座標 / {"t_in":1.2,"t_out":2.0}
  status TEXT DEFAULT 'open',          -- open/working/proposed/resolved/wontfix
  agent_response TEXT DEFAULT '',      -- エージェントの返答（どう直したか／直せない理由）
  resolved_by_take_id INTEGER REFERENCES takes(id),
  created_by TEXT DEFAULT 'human',
  created_at TEXT, updated_at TEXT
);

-- 並べて比べた結果。観点ごとの勝ちと理由を残す。
CREATE TABLE IF NOT EXISTS comparisons (
  id INTEGER PRIMARY KEY,
  episode_id INTEGER REFERENCES episodes(id),
  cut_id INTEGER REFERENCES cuts(id),
  take_ids_json TEXT NOT NULL,
  winner_take_id INTEGER REFERENCES takes(id),
  axes_json TEXT DEFAULT '{}',         -- {"構図": take_id, "表情": take_id, ...}
  reason TEXT DEFAULT '',
  created_at TEXT
);

-- レビューから導いた「次からのルール」。エージェントが提案し、人が承認する。
CREATE TABLE IF NOT EXISTS learnings (
  id INTEGER PRIMARY KEY,
  scope TEXT DEFAULT 'series',         -- series/episode:EP01/character:あかね/stage:prompt
  rule_text TEXT NOT NULL,
  source_review_ids TEXT DEFAULT '[]',
  status TEXT DEFAULT 'proposed',      -- proposed/approved/rejected
  vault_target TEXT DEFAULT '',        -- 承認後に書き出す先（04_制作ルール/… など）
  created_at TEXT, decided_at TEXT
);

-- 各話の設計：シーンごとの狙い・尺の配分・動線と立ち位置。字コンテより先にここで合意する。
CREATE TABLE IF NOT EXISTS scenes (
  id INTEGER PRIMARY KEY,
  episode_id INTEGER REFERENCES episodes(id),
  seq INTEGER,
  code TEXT,                           -- S1
  place TEXT DEFAULT '', time TEXT DEFAULT '', look TEXT DEFAULT '',
  target_seconds REAL DEFAULT 0,
  purpose TEXT DEFAULT '',             -- このシーンで見せたいもの
  emotion TEXT DEFAULT '',             -- 感情の流れ（誰がどこからどこへ）
  blocking TEXT DEFAULT '',            -- 頭の立ち位置と動線（配置図の席・カメラ位置で書く）
  cameras TEXT DEFAULT '',             -- 使うカメラ位置 A〜F
  props TEXT DEFAULT '',               -- 小物の状態
  status TEXT DEFAULT 'draft',         -- draft/review/approved
  UNIQUE(episode_id, code)
);

-- 参照素材の棚：キャラの設定資料（三面図など）、Blender の背景、配置図、小物。
-- 生成は開始フレームを使わず、ここから選んだ参照画像とプロンプトで行う。
CREATE TABLE IF NOT EXISTS assets (
  id INTEGER PRIMARY KEY,
  kind TEXT NOT NULL,                  -- character/bg/layout/prop
  name TEXT NOT NULL,                  -- あかね / 店内:A / 店内配置図
  file_path TEXT NOT NULL,             -- MEDIA_DIR からの相対パス
  meta_json TEXT DEFAULT '{}',         -- bg はカメラの位置・向き・映っている物（render_shot.py の JSON）
  note TEXT DEFAULT '',
  active INTEGER DEFAULT 1,            -- 差し替えたら古いものは 0
  created_at TEXT
);

-- 生成の単位（マルチショット）。字コンテのコマを並べて、1本の動画（Seedance は最大30秒）に何を入れるかを決める。
-- 物を落として拾うなど、カットが変わっても1本で出した方がつながるものは同じショットに入れる。
CREATE TABLE IF NOT EXISTS shots (
  id INTEGER PRIMARY KEY,
  episode_id INTEGER REFERENCES episodes(id),
  code TEXT,                           -- SH01
  seq INTEGER,
  cut_ids_json TEXT NOT NULL,          -- cuts.id の並び（上映順）
  seconds REAL DEFAULT 0,
  note TEXT DEFAULT '',                -- なぜこの分け方か
  status TEXT DEFAULT 'draft',         -- draft/approved
  UNIQUE(episode_id, code)
);

-- 9コマの仮Vコン。ドラフトの前に、エージェントが想像しているカットを監督と確かめる。
CREATE TABLE IF NOT EXISTS boards (
  id INTEGER PRIMARY KEY,
  episode_id INTEGER REFERENCES episodes(id),
  code TEXT,                           -- SB01
  seq INTEGER,
  cut_ids_json TEXT NOT NULL,          -- 9コマ分（足りない分は空き）
  UNIQUE(episode_id, code)
);

-- Premiere との橋渡し。エージェントの編集操作をキューに積み、Premiere の中のパネルが取り出して実行する。
-- 監督が Premiere で手直ししたタイムラインは、パネルから state として送り返され、エージェントはそこから続ける。
CREATE TABLE IF NOT EXISTS premiere_queue (
  id INTEGER PRIMARY KEY, ts TEXT, episode TEXT, command TEXT, args_json TEXT,
  status TEXT DEFAULT 'pending',       -- pending/running/done/failed
  result_json TEXT DEFAULT '', done_at TEXT
);
CREATE TABLE IF NOT EXISTS premiere_states (
  id INTEGER PRIMARY KEY, ts TEXT, episode TEXT, actor TEXT, state_json TEXT, diff_json TEXT
);

-- 使用量。生成1回ごとに、サービス・単位・クレジットを記録して、話数ごとの予算と比べる。
CREATE TABLE IF NOT EXISTS usage (
  id INTEGER PRIMARY KEY,
  ts TEXT, episode_id INTEGER REFERENCES episodes(id), take_id INTEGER REFERENCES takes(id),
  provider TEXT, kind TEXT, units REAL DEFAULT 1, credits REAL DEFAULT 0, note TEXT DEFAULT ''
);

-- 誰が何をしたかの記録。エージェントが前回の続きから作業できるようにする。
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY,
  ts TEXT, actor TEXT, action TEXT, payload_json TEXT
);
"""


# 既存の DB に後から足した列。init() で無ければ足す。
MIGRATIONS = {
    "episodes": {"budget_credits": "REAL DEFAULT 0", "deadline": "TEXT DEFAULT ''",
                 "is_test": "INTEGER DEFAULT 0"},   # テストの回：予算を超えても止めずに警告だけ
    "reviews": {"checks_json": "TEXT DEFAULT ''"},   # AI セルフレビューの観点ごとの合否
    # draft（480p）→ upscale（ドラフトをそのまま拡大）→ final（拡大版を入力に 1080p で生成）
    "takes": {"tier": "TEXT DEFAULT ''", "source_take_id": "INTEGER", "shot_id": "INTEGER", "board_id": "INTEGER",
              "submitted_at": "TEXT", "finished_at": "TEXT",
              "role": "TEXT DEFAULT ''"},   # 音声：voice（仮の声）/ actor（声優）/ sfx / music
}


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def connect() -> sqlite3.Connection:
    config.ensure_dirs()
    conn = sqlite3.connect(config.DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def session():
    conn = connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init() -> None:
    with session() as conn:
        conn.executescript(SCHEMA)
        for table, cols in MIGRATIONS.items():
            have = {r["name"] for r in conn.execute(f"PRAGMA table_info({table})")}
            for col, decl in cols.items():
                if col not in have:
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {decl}")


def rows(cur) -> list[dict]:
    return [dict(r) for r in cur.fetchall()]


def one(cur) -> dict | None:
    r = cur.fetchone()
    return dict(r) if r else None


def insert(conn, table: str, data: dict) -> int:
    keys = list(data)
    cur = conn.execute(
        f"INSERT INTO {table} ({','.join(keys)}) VALUES ({','.join('?' * len(keys))})",
        [data[k] for k in keys],
    )
    return cur.lastrowid


def update(conn, table: str, row_id: int, data: dict) -> None:
    if not data:
        return
    sets = ",".join(f"{k}=?" for k in data)
    conn.execute(f"UPDATE {table} SET {sets} WHERE id=?", [*data.values(), row_id])


def log(conn, actor: str, action: str, payload: dict) -> None:
    insert(conn, "events", {"ts": now(), "actor": actor, "action": action,
                            "payload_json": json.dumps(payload, ensure_ascii=False)})


def episode_by_code(conn, code: str) -> dict | None:
    return one(conn.execute("SELECT * FROM episodes WHERE code=?", (code,)))


def get_or_create_episode(conn, code: str, title: str = "") -> dict:
    ep = episode_by_code(conn, code)
    if ep:
        return ep
    insert(conn, "episodes", {"code": code, "title": title})
    return episode_by_code(conn, code)
