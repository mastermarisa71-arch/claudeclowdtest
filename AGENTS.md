# 月灯りスピークイージー 制作リポジトリ（Codex など、Claude 以外のエージェント向け）

作品のルールと手順は Claude と同じ。**まず `CLAUDE.md` を読む**（役割分担・正本の優先順位・予算・プロンプトの決まり）。
手順の詳細は `.claude/skills/tsukiakari-studio/SKILL.md`。道具は `python studio/cli.py …`（MCP `tsukiakari-studio` でも同じことができる）。

## AI スタッフ会議に入るとき

役（芝居・演出・見る・まとめ）と担当は `月灯_vault/04_制作ルール/AIスタッフ.json`。手順は `studio/docs/AIスタッフ会議.md`。

```
python studio/cli.py staff-claim --agent codex      # 自分の役の枠を取る → ブリーフ（見方・監督の意図・材料・書き方）が出る
python studio/cli.py staff-post <枠> --agent codex --file post.json
```

- ブリーフに書かれた資料（シーン整理・配置図・字コンテ・脚本・キャラのノート）を読んでから書く。
- 自分の役の観点だけ。指摘は5つまで、重い順。監督が決めたこと（レビュー・2択・承認済みのルール）に反する提案はしない。
- ファイル（vault・コード）は書き換えない。会議では所見を出すだけ。作るのはまとめ役の依頼を取ったエージェント。
- 文章は日本語。プロンプトの英語化は作る係がやる。
