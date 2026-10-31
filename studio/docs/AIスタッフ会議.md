# AI スタッフ会議

複数の AI（Claude 2つ・Codex 1つ など）が役を分けて、演出をレビューし合う仕組み。
監督が全部を見る前に、AI どうしで「伝わっているか」「キャラらしいか」「カット割りは合っているか」を詰め、
**合意したものは作り直し、割れたものだけ監督に2択で聞く**。

## 工程ごとに毎回まわす（自動進行）

AI 会議は「必要なときに開く」のではなく、**工程ごとに毎回まわる**。監督がやるのは、シーン整理の承認と、映像を見ての判断だけ。

```
② シーン整理（AI が下書き → 監督が直して「このシーンでいく」）
② 字コンテ会議：芝居（設定）と演出が話し合う → まとめ役が字コンテにし、そのまま 480p ドラフト（30秒程度）まで作る
③ 映像会議：見る（Codex）・演出・芝居 の3つの AI が映像を見る → まとめ役が監督に結論を出す（作り直さない）
④ 監督：映像と結論を見て「OK」か「こうしたい（一言）」（画面「⑤ 決める」）
   こうしたい → まとめ役が作り直す → ③ 映像会議 → ④ 監督（2周目、3周目 …）
```

- 承認（シーン整理の「このシーンでいく」）で②が自動で始まる。②のまとめで、まとめ役に「字コンテ → 480p」の依頼が自動で積まれ、それが終わる（`request-done`）と③が自動で開く。③のまとめで、シーンは「監督の判断待ち」になる。
- 進み具合は「いま」の「シーンの工程」に出る（字コンテ会議／ドラフト作り／映像会議／監督の判断待ち／OK）。
- 止める・手で回すときは `AIスタッフ.json` の `rules.auto` を `false` にする（監督が開く「検討」の会議は、これまでどおり使える）。
- CLI：`flows EP09`（進み具合）、`flow-start EP09 S1`（手で始める）、`flow-direct EP09 S1 ok|redo --note "…"`。

## 役（`月灯_vault/04_制作ルール/AIスタッフ.json`）

| 役 | 字コンテ会議 | 映像会議 | ふだんの担当 |
| --- | --- | --- | --- |
| 演出 | カット割り・カメラ位置とカメラワーク・秒の案 | 自分が意図したことが映像に出ているか。意図そのものを直すべきか | Claude A |
| 芝居（設定） | 各カットのキャラの芝居（視線・手・間）、辞書と決まりに合わせる | キャラが設定どおりか、表情・しぐさと台詞 | Claude B |
| 見る | ― | 企画と脚本を読んだうえで、初めて見る目で：何がしたいか伝わるか。**そもそもこの演出の仕方で良いか** | Codex |
| まとめ（制作） | まとめて字コンテにし、480p まで作る | 監督に結論を出す（作り直さない）。監督の指示で作り直す | Claude A |

担当は `assign` を書き換えれば入れ替えられる。**「見る」は作った本人にしない**。会議の種類ごとの見方は `kinds`。

## AI の手順（どの AI も同じ）

```
python studio/cli.py staff-claim --agent codex          # 自分の役の空いた枠を1つ取る → その役のブリーフが出る
#   ブリーフ＝役の見方、監督の意図、シーン整理・配置図・字コンテ・脚本、できたもの（見る役は画像を必ず見る）
python studio/cli.py contact 31 --frames 12             # 動画はコマ送りの画像にして見る
python studio/cli.py staff-post 12 --agent codex --file post.json
python studio/cli.py staff-summarize 15 --agent claude-a --file summary.json   # まとめ役
python studio/cli.py staff-rounds EP09
```

MCP が使える AI は `staff_next` / `staff_post` / `staff_summarize` / `staff_open` / `staff_rounds`。

書き方（post.json）：

```json
{"summary": "S1 は打ち明けるまでが長く、山場の前の溜めがない",
 "items": [{"severity": "必須", "at": "S1 区切り2", "what": "打ち明けの10秒がずっと同じ引き",
            "fix": "『その時の顔が』でトラックアップ（3秒）、言い終わりで止める"}]}
```

## つなぎ方

### Claude Code（2つ）
リポジトリのフォルダで開けば `CLAUDE.md` と MCP（`.mcp.json`）がそのまま効く。2つ目の Claude は名前だけ変える（`--agent claude-b`）。

### Codex
Codex はリポジトリの `AGENTS.md` を読む。月灯スタジオの道具は CLI（`python studio/cli.py …`）で使える。
MCP でもつなぐときは `%USERPROFILE%\.codex\config.toml` に（パスは自分の clone に直す）：

```toml
[mcp_servers.tsukiakari-studio]
command = "C:\\path\\to\\claudeclowdtest\\studio\\.venv\\Scripts\\python.exe"
args = ["C:\\path\\to\\claudeclowdtest\\studio\\mcp_server.py"]
env = { TSUKI_DATA = "C:\\path\\to\\claudeclowdtest\\studio\\data" }
```

### 自動で回す（見張り番）
`start.bat` で月灯スタジオを起動したまま、AI ごとに黒いウィンドウを1つずつ：

```
studio\staff_watch.bat codex
studio\staff_watch.bat claude-b
studio\staff_watch.bat claude-a
```

自分の役の枠が空くと、その AI の CLI（`claude -p …` / `codex exec …`）を起こす。起こすコマンドは `AIスタッフ.json` の `agents`。
**最初は見張り番を使わず、手で1回まわして確かめる**（`staff-claim` を各 AI に頼む）。コマンドの書き方（許可の出し方）は、使っている CLI の版で変わるので、動かなかったら黒いウィンドウの表示をエージェントに見せる。

## 使用量の目安

1回の会議 ＝ 1周目3役 ＋ 2周目3役 ＋ まとめ ＝ AI の呼び出し7回。シーン1つの文章段なら軽いが、全シーン×毎工程で回すと重い。
おすすめ：**シーン整理（G1 の前）と、480p ドラフトの通し（G3 の前）の2回**。迷うシーンだけ追加で開く。
2周目を省くときは `passes` を 1 にする（AIスタッフ.json の rules）。

## できないこと（いまの限界）

- AI は動画を「コマ送りの画像」で見る。動きのなめらかさ・間の体感は、画像から分かる範囲でしか言えない（ぎこちなさの候補を挙げ、最後は監督が見る）。
- 音（声・間合い）は、台詞の文字と秒でしか判断できない。
