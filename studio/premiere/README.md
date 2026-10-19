# Premiere の中で、エージェントと一緒に編集する

XML を書き出して読み込み直す往復をやめ、**Premiere の中に月灯スタジオのパネルを置いて**、同じタイムラインをエージェントと監督が交互に触る。

## しくみ

```
エージェント（Windows の PC 上の Claude Code）
   │ pr-build / pr-replace / pr-marker / pr-read（命令をキューに積む）
   ▼
月灯スタジオ（localhost:8765）── キュー ──▶ Premiere のパネル（3秒ごとに取り出して ExtendScript で実行）
   ▲                                          │ 監督が溜め・詰めを手直し
   │ pr-state（差分を読んで続きを作る）         │ 「AIに渡す」＋ひとこと（音声入力可）
   └────────────── タイムラインの今の状態 ◀────┘
```

- エージェントの操作は Premiere の画面で起きるので、監督はそのまま見ていられる。パネルの下半分には月灯スタジオの編集画面が出る。
- 監督が手で直したら「AIに渡す」。コマの名前のクリップは尺がそのまま字コンテに反映され、ショットのクリップは長さの変化が記録される。ひとことは監督のレビューとして残り、エージェントの次のブリーフに入る。
- XML の書き出し（`export`）は予備として残す。

## 画面操作（computer use）との使い分け

| やること | 方法 | 理由 |
| --- | --- | --- |
| シーケンスを組む、テイクの差し替え、尺、マーカー | パネル（ExtendScript） | 速くて確実。何をしたかが記録に残る |
| エフェクト、色、After Effects の作業、パネルでできない操作 | 画面操作（Claude の computer use） | 画面を見ながら操作できる。遅いので要所だけ |
| 微調整（溜め・詰め・つなぎの感覚） | 監督が手で | 人の手を入れる部分。終わったら「AIに渡す」 |

画面操作をするには、エージェントを**クラウドではなく Windows の PC で**動かす（Claude Code のデスクトップアプリ＋ computer use）。

## 入れ方（Windows）

1. `studio/premiere/cep` フォルダを `C:\Users\<ユーザー>\AppData\Roaming\Adobe\CEP\extensions\com.tsukiakari.studio` にコピーする。
2. 署名なしの拡張を読み込めるよう、レジストリ `HKEY_CURRENT_USER\Software\Adobe\CSXS.11` に文字列値 `PlayerDebugMode` = `1` を足す（CSXS の番号は Premiere の版に合わせる）。
3. 月灯スタジオを起動（`python -m uvicorn studio.backend.app:app --port 8765`）。
4. Premiere の「ウィンドウ → エクステンション → 月灯スタジオ」。

注意：CEP は Adobe が UXP へ移行中の仕組み。今の Premiere で動くことを最初に確認し、使えなくなったら同じ命令（build / read / replace / marker）を UXP のプラグインに移す。ExtendScript の部分（`host/tsuki.jsx`）は**まだ実機で試していない**。初回は小さいシーケンスで確かめる。

## エージェントの使い方

```
python studio/cli.py pr-build EP09            # ドラフトの段階から組める（--selected で採用分だけ）
python studio/cli.py pr-read EP09             # 今のタイムラインを読み取らせる
python studio/cli.py pr-state EP09            # 監督が直した差分
python studio/cli.py pr-replace EP09 SH03 --take 52
python studio/cli.py pr-marker EP09 --at 12.5 --comment "ここの溜めはどうしますか"
```

監督の手直しは「正」として扱う。手直しされたコマを、エージェントが勝手に元の尺へ戻さない。
