"""パスと環境変数。Windows のローカルPCでもクラウドでも同じコードで動くように、場所は環境変数で差し替える。"""
import os
from pathlib import Path

STUDIO_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = STUDIO_DIR.parent

# 作品の知識（正本・決定ログ・制作ルール・脚本・レビュー）。エージェントはここを読んでから作業する。
VAULT_DIR = Path(os.environ.get("TSUKI_VAULT", REPO_ROOT / "月灯_vault"))

# DB と生成物（画像・動画・音声）。生成物は git に入れない（.gitignore 済み）。
DATA_DIR = Path(os.environ.get("TSUKI_DATA", STUDIO_DIR / "data"))
DB_PATH = DATA_DIR / "studio.db"
MEDIA_DIR = DATA_DIR / "media"

# 外部サービスの鍵。未設定のプロバイダーは「未接続」として扱う。
HAMSTER_API_KEY = os.environ.get("HAMSTER_API_KEY", "")
HAMSTER_BASE_URL = os.environ.get("HAMSTER_BASE_URL", "")
HAMSTER_PROJECT_ID = os.environ.get("HAMSTER_PROJECT_ID", "")
RUNWAY_API_KEY = os.environ.get("RUNWAYML_API_SECRET", "")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
BLENDER_EXE = os.environ.get("BLENDER_EXE", "blender")   # 例：C:/Program Files/Blender Foundation/Blender 4.2/blender.exe

# 予算は円。1話の基準は 5万円（テストの回は超えてよい：episode-set --test）。
DEFAULT_BUDGET_YEN = 50000
# 1回あたりの目安（円）。動画は「1秒あたり」で、段階ごとの単価は TIERS の yen_per_sec を使う。
# 画像・音声は【仮の値】。実際の単価が分かったら直す。
COST_TABLE = {
    ("hamster", "sheet"): 40, ("hamster", "image"): 20, ("hamster", "video"): 17, ("hamster", "audio"): 5,
    ("runway", "image"): 20, ("runway", "video"): 20, ("runway", "audio"): 10,
    ("elevenlabs", "audio"): 5, ("blender", "bg"): 0, ("manual", "*"): 0,
}
PER_SECOND_KINDS = {"video"}
# 動画の段階と、HAMSTER（Seedance 2.5）の実際の単価（2026-10 監督より。15秒の生成で
# 480p 250円・720p 550円・1080p 1,400円 → 1秒あたりに換算）。15秒以外は未確認で、長い方が割安の見込み。
TIERS = {
    "draft": {"resolution": "854x480", "yen_per_sec": 250 / 15},     # 480p ドラフト。全部出し切って通しで判断
    "mid": {"resolution": "1280x720", "yen_per_sec": 550 / 15},      # 720p（必要なときだけ）
    "upscale": {"resolution": "1920x1080", "yen_per_sec": 1400 / 15},
    "final": {"resolution": "1920x1080", "yen_per_sec": 1400 / 15},  # 採用したドラフトを入力に 1080p
}
# Seedance 2.5（HAMSTER 経由）の制限。1本の長さと、1回に渡す参照画像の数。
SHOT_MAX_SECONDS = 30
SHOT_TARGET_SECONDS = 15        # 自動の分け方の目安。1ビート 6〜8秒を2〜3つ
REF_LIMIT = 10

# 人のレビューをはさまずにエージェントが同じコマを作り直してよい回数。超えたら人の判断を待つ。
MAX_AGENT_RETRIES = int(os.environ.get("TSUKI_MAX_RETRIES", "2"))

FPS = 24
FRAME_W, FRAME_H = 1920, 1080


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
