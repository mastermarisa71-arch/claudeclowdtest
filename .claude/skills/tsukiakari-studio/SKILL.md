---
name: tsukiakari-studio
description: 月灯りスピークイージーの制作を進める手順。脚本→設計→字コンテ→9コマプロンプト→生成→編集のどの工程でも、ブリーフを読み、作り、月灯スタジオにテイクとして登録し、人のレビューに返答する。「EP09を進めて」「レビューに対応して」「このカットを作り直して」などで使う。
---

# 月灯スタジオでの制作ループ

人は監督としてレビューする。エージェントは作って、**自分で見て**、登録して、返答する。この順を崩さない。
1話（約3分）を2〜3日で作る段取りと関門（G1〜G5）は `studio/docs/制作の段取り_2〜3日で1本.md`。関門の承認を待つ間も、進められる工程は並行で進める。

## 0. 安い順に確かめる

文章（設計・字コンテ）→ Blender の背景 → 9コマシート → 単コマの直し → 動画 → 声・音。
動画は G3（画の確認）で採用されたカットにだけ回す。予算（`usage`）を超えそう、または作り直しの上限で止まったら、迷っている点を書いて監督に回す。

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
| 9コマプロンプト | 字コンテ | シートごとのプロンプトと添付順 | vault と take（kind=text/sheet） |
| 生成 | プロンプト・参照画像 | シート→コマ画像、動画、音声 | `generate` / `take-add` |
| 編集 | 採用テイク | Premiere 用 XML・ffconcat | `export` |

- 9コマのルール、参照画像の添付順、画面の方向（店＝右、外＝左）、キャラの芝居の辞書は vault の制作ルールに従う。
- 前の版を直すときは `--parent` で元テイクを指し、`--note` に「何を変えたか」を一行で書く。人が並べて比べるときの手がかりになる。

## 3. 自分で見る（セルフレビュー）

生成したら、監督に見せる前に必ず見る。そのコマに出るキャラの `月灯_vault/06_設定/キャラ/<名前>.md`（性格・テンション・芝居の辞書）と照らす。
シートは9コマまとめて1回見て、コマごとに結果を残す。

```
python studio/cli.py self-review 31 --checks '{"意図":true,"配置・左右":true,"芝居":"まひるがシェイカーを振っている（振るのは朔奈だけ）","キャラ崩れ":true,"光・色":true,"つなぎ":true}' --comment "芝居だけ不合格。朔奈に持たせて作り直す"
```

不合格は自分で直す。人のレビューなしの作り直しは1コマ2回まで（超えると generate が止まる）。
監督の指摘と自分の見立てがずれた観点は、キャラのノートの「## 追記」に書き足す（監督の承認後）。

## 4. 登録する

```
python studio/cli.py generate EP09 --cut 12 --kind sheet --provider hamster --prompt-file sheet01.txt --refs bg.png,layout.png,akane.png --fixes 5 --note "配置を字コンテどおり中央に"
python studio/cli.py take-add EP09 --cut 12 --kind image --file cut12_v2.png --parent 31 --fixes 5 --note "…"
```

プロバイダーが未接続・API エラーのときも、テイクは failed として残る。エラーは隠さず人に伝える。

## 5. 返答する

```
python studio/cli.py respond 5 "あかねを画面中央へ。表情は『上の空』を目線を外すことで出した" --take 32
```

- 直せないとき、直すと別の決まりと衝突するときは、`--status open` のまま理由を書き、人に判断を求める。
- 同じ種類の指摘が続いたら `propose-rule "<次からのルール>" --scope character:あかね --from 5,8` で提案する。

## 6. 書き出す

```
python studio/cli.py export EP09
```

未採用のコマが残っていれば一覧で返るので、人に伝える。
