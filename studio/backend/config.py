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

FPS = 24
FRAME_W, FRAME_H = 1920, 1080


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
