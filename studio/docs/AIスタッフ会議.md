# AI スタッフ会議

複数の AI（Claude 2つ・Codex 1つ など）が役を分けて、演出をレビューし合う仕組み。
監督が全部を見る前に、AI どうしで「伝わっているか」「キャラらしいか」「カット割りは合っているか」を詰め、
**合意したものは作り直し、割れたものだけ監督に2択で聞く**。

## 役（`月灯_vault/04_制作ルール/AIスタッフ.json`）

| 役 | 見るところ | ふだんの担当 |
| --- | --- | --- |
| 芝居 | キャラの整合性・芝居（性格・テンション・芝居の辞書・キャラの決まり） | Claude B |
| 演出 | カット割り・カメラ（パン・トラックアップ・FIX・寄り引き）・尺とテンポ | Codex |
| 見る | できたものを初めて見る目で：意図が伝わるか、何がしたいシーンか、飽きる所・ぎこちない所 | Claude B |
| まとめ | 所見を読み、依頼（作り直し）／2択（監督へ）／見送り に分ける。作る係 | Claude A |

担当は `assign` を書き換えれば入れ替えられる。**「見る」は作った本人にしない**（会議を開くときに `--made-by` を書くと、その AI は「見る」の枠を取れない）。

## 流れ

```
開く（S1 / SH03 / #31 / 全体）
  → 1周目：芝居・演出・見る が、ほかの役を見ずに所見（つられないように）
  → 2周目：ほかの役の所見を読んで、賛成・反対・補足
  → まとめ：do＝作り直しの依頼 ／ ask＝監督への2択 ／ drop＝見送り
```

- **だれが開くか**：作る係（まとめ役）が、シーン整理・配置図・字コンテ・9コマ・480p ドラフトを作ったあとに開く。監督は画面「AI スタッフ会議」や、シーン整理の「AI スタッフで検討して」から開ける。
- **止まる仕組み**：同じ対象の会議は、監督が何か返すまで2回まで。作り直しは安い工程だけ（1080p は監督の採用が要る。作り直しの上限と予算の止めもそのまま効く）。
- **監督の決めたことが上**：レビュー・2択で選んだもの・承認済みのルールに反する提案はしない。

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
