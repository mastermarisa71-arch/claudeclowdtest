"""生成サービスの共通の口。どのサービスも submit → poll → fetch の3つで扱う。

新しいサービス（Seedance、ComfyUI、Kling など）は Provider を継承して registry に足すだけで、
エージェントからもレビュー画面からも同じ手順で使える。
"""
from dataclasses import dataclass, field


class NotConfigured(RuntimeError):
    """API キーや接続先が未設定。"""


@dataclass
class GenerationRequest:
    kind: str                      # sheet/image/video/audio
    prompt: str
    model: str = ""
    refs: list[str] = field(default_factory=list)   # 参照ファイル（MEDIA_DIR 相対 or URL）。添付順を保つ
    params: dict = field(default_factory=dict)      # ratio, duration, voice_id, seed など


@dataclass
class JobStatus:
    state: str                     # queued/running/done/failed/awaiting_upload
    result_urls: list[str] = field(default_factory=list)
    error: str = ""


class Provider:
    name = "base"
    kinds: set[str] = set()

    def available(self) -> bool:
        return True

    def submit(self, req: GenerationRequest) -> str:
        """ジョブを投げて外部のジョブIDを返す。"""
        raise NotImplementedError

    def poll(self, job_id: str) -> JobStatus:
        raise NotImplementedError
