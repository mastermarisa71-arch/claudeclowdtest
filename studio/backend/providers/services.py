"""各サービスのアダプター。

- manual   : 画面（Seedance・ComfyUI・HAMSTERのWeb画面など）で作ったものを、あとからアップロードして登録する。
- hamster  : 自社 API。仕様が届いたら submit/poll を埋める（下の TODO と、e001/EP01_fix_v5 のエラー記録を参照）。
- runway   : Runway API（画像・動画）。エンドポイントと版は公式ドキュメントで要確認。
- elevenlabs: 音声。EP09 では HAMSTER 経由の elevenlabs_v4 を使っているので、直接呼ぶのは予備。
"""
import json
import urllib.request

from .. import config
from .base import GenerationRequest, JobStatus, NotConfigured, Provider


def _http(method: str, url: str, headers: dict, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read() or b"{}")


class ManualProvider(Provider):
    name = "manual"
    kinds = {"sheet", "image", "video", "audio", "edit", "text"}

    def submit(self, req: GenerationRequest) -> str:
        return ""                      # 生成は外で行う。テイクは awaiting_upload で待つ

    def poll(self, job_id: str) -> JobStatus:
        return JobStatus("awaiting_upload")


class HamsterProvider(Provider):
    """自社 API。既存ログから分かっている流れ：
    1. 参照画像をアップロード → mediaPrepare:image の Work が completed になるのを待つ（inputArtifactId を得る）
    2. imageGenerate を projectId・requestId（冪等キー）つきで送る
    3. Work を待ち、結果URLを取得。失敗時は recover(imageGenerate)
    既知の問題：請求状態が未解決だと HTTP 409 API_REJECTED（Work が作られない）。
    """
    name = "hamster"
    kinds = {"sheet", "image", "video", "audio"}

    def available(self) -> bool:
        return bool(config.HAMSTER_API_KEY and config.HAMSTER_BASE_URL)

    def submit(self, req: GenerationRequest) -> str:
        if not self.available():
            raise NotConfigured("HAMSTER_API_KEY / HAMSTER_BASE_URL が未設定です")
        # TODO: HAMSTER の API 仕様（エンドポイント、認証、mediaPrepare、Work の形）を受け取ってから実装
        raise NotImplementedError("HAMSTER API の仕様待ち")

    def poll(self, job_id: str) -> JobStatus:
        raise NotImplementedError("HAMSTER API の仕様待ち")


class RunwayProvider(Provider):
    name = "runway"
    kinds = {"image", "video"}
    base = "https://api.dev.runwayml.com/v1"

    def available(self) -> bool:
        return bool(config.RUNWAY_API_KEY)

    def _headers(self) -> dict:
        if not self.available():
            raise NotConfigured("RUNWAYML_API_SECRET が未設定です")
        return {"Authorization": f"Bearer {config.RUNWAY_API_KEY}", "X-Runway-Version": "2024-11-06"}

    def submit(self, req: GenerationRequest) -> str:
        # 要確認：モデル名・ratio の書式・参照画像の渡し方は Runway の最新ドキュメントに合わせる
        if req.kind == "video":
            body = {"model": req.model or "gen4_turbo", "promptText": req.prompt,
                    "promptImage": req.refs[0] if req.refs else None,
                    "ratio": req.params.get("ratio", "1280:720"),
                    "duration": req.params.get("duration", 5)}
            res = _http("POST", f"{self.base}/image_to_video", self._headers(), body)
        else:
            body = {"model": req.model or "gen4_image", "promptText": req.prompt,
                    "ratio": req.params.get("ratio", "1920:1080"),
                    "referenceImages": [{"uri": u, "tag": f"image{i + 1}"} for i, u in enumerate(req.refs)]}
            res = _http("POST", f"{self.base}/text_to_image", self._headers(), body)
        return res["id"]

    def poll(self, job_id: str) -> JobStatus:
        res = _http("GET", f"{self.base}/tasks/{job_id}", self._headers())
        state = {"SUCCEEDED": "done", "FAILED": "failed"}.get(res.get("status"), "running")
        return JobStatus(state, res.get("output") or [], res.get("failure", ""))


class ElevenLabsProvider(Provider):
    name = "elevenlabs"
    kinds = {"audio"}

    def available(self) -> bool:
        return bool(config.ELEVENLABS_API_KEY)

    def submit(self, req: GenerationRequest) -> str:
        if not self.available():
            raise NotConfigured("ELEVENLABS_API_KEY が未設定です")
        # TODO: /v1/text-to-speech/{voice_id} は音声のバイト列を同期で返すので、ここで保存してパスを返す形にする
        raise NotImplementedError

    def poll(self, job_id: str) -> JobStatus:
        return JobStatus("done", [job_id])


REGISTRY: dict[str, Provider] = {p.name: p for p in
                                 [ManualProvider(), HamsterProvider(), RunwayProvider(), ElevenLabsProvider()]}
