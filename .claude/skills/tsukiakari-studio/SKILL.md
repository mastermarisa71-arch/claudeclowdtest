---
name: tsukiakari-studio
description: 月灯りスピークイージーの制作を進める手順。脚本→設計→字コンテ→9コマプロンプト→生成→編集のどの工程でも、ブリーフを読み、作り、月灯スタジオにテイクとして登録し、人のレビューに返答する。「EP09を進めて」「レビューに対応して」「このカットを作り直して」などで使う。
---

# 月灯スタジオでの制作ループ

人は監督としてレビューする。エージェントは作って、登録して、返答する。この順を崩さない。

## 1. 読む

```
python studio/cli.py brief EP09
python studio/cli.py reviews --episode EP09 --status open,working
```

ブリーフに書かれた vault の資料（正本・決定ログ・制作ルール・その話の脚本と設計）を読む。
承認済みルールと「比較で分かった好み」は、プロンプトに必ず反映する。

## 2. 作る（工程ごと）

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

## 3. 登録する

```
python studio/cli.py generate EP09 --cut 12 --kind sheet --provider hamster --prompt-file sheet01.txt --refs bg.png,layout.png,akane.png --fixes 5 --note "配置を字コンテどおり中央に"
python studio/cli.py take-add EP09 --cut 12 --kind image --file cut12_v2.png --parent 31 --fixes 5 --note "…"
```

プロバイダーが未接続・API エラーのときも、テイクは failed として残る。エラーは隠さず人に伝える。

## 4. 返答する

```
python studio/cli.py respond 5 "あかねを画面中央へ。表情は『上の空』を目線を外すことで出した" --take 32
```

- 直せないとき、直すと別の決まりと衝突するときは、`--status open` のまま理由を書き、人に判断を求める。
- 同じ種類の指摘が続いたら `propose-rule "<次からのルール>" --scope character:あかね --from 5,8` で提案する。

## 5. 書き出す

```
python studio/cli.py export EP09
```

未採用のコマが残っていれば一覧で返るので、人に伝える。
