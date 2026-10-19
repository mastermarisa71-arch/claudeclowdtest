---
name: tsukiakari-studio
description: 月灯りスピークイージーの制作を進める手順。脚本→設計→字コンテ→プロンプト→生成（480p ドラフト→1080p 本番）→編集のどの工程でも、ブリーフを読み、作り、月灯スタジオにテイクとして登録し、人のレビューに返答する。「EP09を進めて」「レビューに対応して」「このカットを作り直して」などで使う。
---

# 月灯スタジオでの制作ループ

人は監督としてレビューする。エージェントは作って、**自分で見て**、登録して、返答する。この順を崩さない。
1話（約3分）を2〜3日で作る段取りと関門（G1〜G5）は `studio/docs/制作の段取り_2〜3日で1本.md`。関門の承認を待つ間も、進められる工程は並行で進める。

## 0. 安い順に確かめる

文章（設計・字コンテ）→ Blender の背景 → 9コマ仮Vコン → ショット分け → 480p ドラフトを全部 → 通しで採用／不採用 → 1080p 本番 → 声・音。
開始フレームは使わない。参照画像（キャラの設定資料1人1枚＋Blender の背景＋配置図＋小物、最大10枚）とプロンプトで立ち位置と芝居を出す。
1080p 本番は、監督が「良い／採用」をつけたドラフトにだけ回す（`promote` / `promote-all` が止める）。
予算は1話5万円（テストの回は `episode-set --test` で超えてよい）。ショット分けの直後に `budget-plan` で見積もる。予算（`usage`）を超えそう、または作り直しの上限で止まったら、迷っている点を書いて監督に回す。

## 1. 読む

```
python studio/cli.py brief EP09
python studio/cli.py reviews --episode EP09 --status open,working
```

ブリーフに書かれた vault の資料（正本・決定ログ・制作ルール・その話の脚本と設計）を読む。
承認済みルールと「比較で分かった好み」は、プロンプトに必ず反映する。

## 2. 作る（工程ごと）

設計は字コンテより先に `scene-set` で作り、G1 で承認をもらう（狙い・目標尺・感情の流れ・頭の立ち位置と動線・カメラ位置・小物）。
シーンの目標尺の合計は、話数の目標尺（`episode-set --target`）に合わせる。

```
python studio/cli.py scene-set EP09 S1 --place 月灯り店内 --time 夕方 --look B --target 30 --cameras A,C \
  --purpose "いつもの営業前の中で、あかねだけが落ち着かない" --emotion "あかね：上の空→打ち明ける決意" \
  --blocking "朔奈=席2前、まひる=席4前、海凪=ピアノ。あかねはグラスを持って席1→席5を往復し、入口の横で止まる"
python studio/cli.py bg-render EP09 --blend <舞台.blend> --camera CAM_A --cut 1 --note "S1 の引き"
```

| 工程 | 入力 | 出すもの | 置き場所 |
| --- | --- | --- | --- |
| 脚本の直し | 脚本いまの版・正本・レビュー | 直した脚本と変更点 | Claude Docs で作業 → vault 03_脚本/いまの版 |
| 設計案 | 脚本 | 芯・構成と尺・シーンのトーン・提案（複数案） | vault 02_各話/EPxx |
| 字コンテ | 設計案 | xlsx（既存の列構成）→ `import-jikonte` | vault 02_各話/EPxx/字コンテ_vN |
| プロンプト | 字コンテ・設計・設定・参照素材 | カットごとのプロンプトと参照画像の並び（`prompt-build`） | take の prompt・refs |
| 生成 | プロンプト・参照画像 | シート→コマ画像、動画、音声 | `generate` / `take-add` |
| 編集 | 採用テイク | Premiere 用 XML・ffconcat | `export` |

- 参照画像の添付順、画面の方向（店＝右、外＝左）、キャラの芝居の辞書は vault の制作ルールに従う。
- 前の版を直すときは `--parent` で元テイクを指し、`--note` に「何を変えたか」を一行で書く。人が並べて比べるときの手がかりになる。

## 3. 自分で見る（セルフレビュー）

生成したら、監督に見せる前に必ず見る。仮Vコンは「字コンテの意図・配置・芝居が絵になっているか」、ドラフトは加えて「プロンプトに書いた動きと秒数どおりか」を見る。そのコマに出るキャラの `月灯_vault/06_設定/キャラ/<名前>.md`（性格・テンション・芝居の辞書）と照らす。
ドラフトは `python studio/cli.py contact <テイク>` で抜き出したフレームの画像を見る（動画を丸ごと読まない）。ドラフトはカットごとに見る。数カットまとめて見てもよいが、結果はカット（テイク）ごとに残す。

```
python studio/cli.py self-review 31 --checks '{"意図":true,"配置・左右":true,"芝居":"まひるがシェイカーを振っている（振るのは朔奈だけ）","キャラ崩れ":true,"光・色":true,"つなぎ":true}' --comment "芝居だけ不合格。朔奈に持たせて作り直す"
```

不合格は自分で直す。人のレビューなしの作り直しは1コマ（1ショット）2回まで（超えると止まる）。
「書いたのに出なかった」「書かずに出た」は、Seedance の書き方の学びとしてコメントに残す。
監督の指摘と自分の見立てがずれた観点は、キャラのノートの「## 追記」に書き足す（監督の承認後）。

## 4. 生成して登録する

### 9コマ仮Vコン（ドラフトの前の確認段、G2）
エージェントが想像しているカットを監督と確かめる。プロンプトは既存の 9コマの形（日本語）で仕上げる。

```
python studio/cli.py board-plan EP09                       # 9コマずつのシート分け（同じカットは同じシート）
python studio/cli.py board-prompt EP09 SB01 --out sb01.txt # 骨組み → 仕上げる
python studio/cli.py board-shoot EP09 SB01 --provider hamster --prompt-file sb01.txt
python studio/cli.py board-split 45                        # シートを9コマに切ってコマのテイクにする → 編集画面で通しで見られる
```

### ショット分け
`shot-plan` はたたき台（同じシーンで目安15秒まで詰めるだけ）。字コンテと仮Vコンを並べて見て、カットが変わっても1本で出した方がつながるもの（物を落として拾う、視線のやりとり）をまとめ直す。1本30秒まで。

```
python studio/cli.py shot-plan EP09
python studio/cli.py shot-set EP09 SH03 S1-06 S1-07 --note "グラスを落として拾うまでを1本で"
python studio/cli.py budget-plan EP09
```

### 480p ドラフト（Seedance 2.5）
`shot-brief` の骨組みを、`studio/docs/Seedance2.5_プロンプトの書き方.md` に沿って仕上げる。Seedance は書いたとおりに動くので、各区切りの動作を秒で、キャラごとに参照番号つきで細かく書く。`shot-shoot` は送る前に点検し、指摘があれば止まる。

```
python studio/cli.py shot-brief EP09 SH03 --out sh03.txt   # 骨組み → 仕上げる
python studio/cli.py shot-shoot EP09 SH03 --prompt-file sh03.txt --note "初回"
python studio/cli.py shot-shoot EP09 SH03 --prompt-file sh03_v2.txt --parent 31 --fixes 5 --note "配置の直し"
```

ドラフトは全部出し切って、編集画面の通しで監督が採用／不採用を決める。採用されたものから 1080p へ：

```
python studio/cli.py promote-all EP09        # 採用済みでまだ本番がないドラフトを順に
python studio/cli.py promote 31              # 1本だけ
```

参照素材（`asset-add` / `bg-render --asset-name 店内:A`）が足りないときは、勝手に代用せず監督に伝える。
音声や手作業の結果は `generate` / `take-add` / `attach`。プロバイダーが未接続・API エラーのときも、テイクは failed として残る。エラーは隠さず人に伝える。

## 5. 返答する

```
python studio/cli.py respond 5 "あかねを画面中央へ。表情は『上の空』を目線を外すことで出した" --take 32
```

- 直せないとき、直すと別の決まりと衝突するときは、`--status open` のまま理由を書き、人に判断を求める。
- 同じ種類の指摘が続いたら `propose-rule "<次からのルール>" --scope character:あかね --from 5,8` で提案する。

## 6. 音と編集（Premiere で一緒に）

Seedance の音は使わない。並べるときは Runway の仮の声・効果音・劇伴、声優の声が届いたらそれに差し替える。

```
python studio/cli.py audio-add EP09 --cut 12 --file v012.mp3 --role voice --speaker あかね   # 仮の声
python studio/cli.py audio-add EP09 --cut 12 --file actor012.wav --role actor --speaker あかね  # 声優
python studio/cli.py promote 31     # 声優の声があるショットは、その声に口を合わせて 1080p を作る
```

編集は Premiere の中のパネル経由（`studio/premiere/README.md`）。監督の手直しは正として扱い、勝手に戻さない。

```
python studio/cli.py pr-build EP09               # シーケンスを組む（ドラフトの段階から）
python studio/cli.py pr-state EP09               # 監督が直した差分を読んでから続ける
python studio/cli.py pr-replace EP09 SH03 --take 52
python studio/cli.py pr-marker EP09 --at 12.5 --comment "ここの溜めはどうしますか"
```

使った額と待ち時間は `stats EP09` で確かめ、予算の残りが2割を切ったら監督に伝える。

## 7. 書き出す（予備）


```
python studio/cli.py export EP09
```

未採用のコマが残っていれば一覧で返るので、人に伝える。
