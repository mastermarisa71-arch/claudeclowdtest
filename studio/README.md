# 月灯スタジオ

『月灯りスピークイージー』を、**エージェントが作り、人がレビューする**ための制作ツール（骨組み）。

- レビュー画面（ブラウザ）：コマごとにテイクを見る、画面に範囲の印をつけてレビュー、並べて比較、採用、エージェントの返答の確認、ルールの承認。
- エージェント用 CLI：ブリーフを読む、テイクを登録・生成する、レビューに返答する、ルールを提案する、Premiere 用 XML を書き出す。
- 両方とも同じ SQLite（`studio/data/studio.db`）を読み書きする。

## 起動（Windows）

`studio\setup.bat`（最初に1回）→ `studio\start.bat`（毎回）。エージェントへの頼み方（この PC の Claude Code / Claude Desktop / クラウドの Claude）は [使い方](docs/使い方_起動とエージェントへの頼み方.md)。

## 起動（手で）

```bash
pip install -r studio/requirements.txt
# 既存の字コンテを取り込む
python studio/cli.py import-jikonte EP09 e009/EP09_字コンテ_4分版.xlsx --version 4分版
python studio/cli.py import-jikonte EP01 月灯_vault/02_各話/EP01/字コンテ_v6/EP01_v6_字コンテ.xlsx --version v6
# 画面
python -m uvicorn studio.backend.app:app --port 8765   # → http://localhost:8765
```

環境変数：`BLENDER_EXE`（Blender の実行ファイル）、`TSUKI_MAX_RETRIES`（作り直しの上限、既定2）、`TSUKI_DATA`（DB と生成物の置き場所。既定は `studio/data`）、`HAMSTER_API_KEY` `HAMSTER_BASE_URL` `HAMSTER_PROJECT_ID`、`RUNWAYML_API_SECRET`、`ELEVENLABS_API_KEY`。

## 構成

```
studio/
  backend/
    db.py            スキーマ（episodes / documents / cuts / takes / reviews / comparisons / learnings / events）
    core.py          画面と CLI が共通で使う操作
    context.py       エージェント用ブリーフの組み立て
    app.py           FastAPI（レビュー画面の API）
    importers/jikonte.py   字コンテ xlsx → cuts（版ごとの列の違いを吸収）
    exporters/fcpxml.py    採用テイク → Premiere 用 XML（xmeml v5）・ffconcat
    providers/       生成サービスの口（manual / hamster / runway / elevenlabs）
  frontend/          ビルド不要の HTML/JS/CSS
  cli.py             エージェント用 CLI
  docs/ツール設計メモ.md   機能の見通し・実装方針・段階・確認したいこと
```

## 段取り

1話（約3分）を2〜3日で作る流れ、関門、使用量の抑え方は [制作の段取り_2〜3日で1本](docs/制作の段取り_2〜3日で1本.md)。

画面：話数 → **設計**（シーン・尺の配分・動線、予算）／**コマ**／**AIが通したもの**（流し見）／**編集（ライブ）**（通し再生、エージェントの操作がリアルタイムで流れる、尺・台詞の手直し）。

## 今の状態

- 動く（追加）：設定の書き出し（`bible`）、設計（`scene-set`）、セルフレビュー（`self-review`）、予算と作り直しの上限、ライブ編集画面（SSE）、Blender の背景レンダー（`bg-render`、ローカルの Blender が必要）。
- 動く：字コンテ取り込み（EP01 v6 202コマ、EP09 4分版 162コマを確認）、テイク登録、範囲つきレビュー、比較、エージェントの返答と確認、ルールの提案と承認、ブリーフ、XML 書き出し。
- 未接続：HAMSTER（保留）、Runway（実装はあるが未検証）、ElevenLabs（未実装）、9コマシートの切り出し、音声トラックの XML 書き出し、After Effects 連携。
