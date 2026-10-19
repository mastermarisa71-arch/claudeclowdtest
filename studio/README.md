# 月灯スタジオ

『月灯りスピークイージー』を、**エージェントが作り、人がレビューする**ための制作ツール（骨組み）。

- レビュー画面（ブラウザ）：コマごとにテイクを見る、画面に範囲の印をつけてレビュー、並べて比較、採用、エージェントの返答の確認、ルールの承認。
- エージェント用 CLI：ブリーフを読む、テイクを登録・生成する、レビューに返答する、ルールを提案する、Premiere 用 XML を書き出す。
- 両方とも同じ SQLite（`studio/data/studio.db`）を読み書きする。

## 起動

```bash
pip install -r studio/requirements.txt
# 既存の字コンテを取り込む
python studio/cli.py import-jikonte EP09 e009/EP09_字コンテ_4分版.xlsx --version 4分版
python studio/cli.py import-jikonte EP01 月灯_vault/02_各話/EP01/字コンテ_v6/EP01_v6_字コンテ.xlsx --version v6
# 画面
python -m uvicorn studio.backend.app:app --port 8765   # → http://localhost:8765
```

環境変数：`TSUKI_DATA`（DB と生成物の置き場所。既定は `studio/data`）、`HAMSTER_API_KEY` `HAMSTER_BASE_URL` `HAMSTER_PROJECT_ID`、`RUNWAYML_API_SECRET`、`ELEVENLABS_API_KEY`。

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

## 今の状態

- 動く：字コンテ取り込み（EP01 v6 202コマ、EP09 4分版 162コマを確認）、テイク登録、範囲つきレビュー、比較、エージェントの返答と確認、ルールの提案と承認、ブリーフ、XML 書き出し。
- 未接続：HAMSTER（API 仕様待ち）、Runway（実装はあるが未検証）、ElevenLabs（未実装）、9コマシートの切り出し、音声トラックの XML 書き出し、After Effects 連携。
