# ダウンロードと AI の連携（Claude・Codex）

月灯スタジオは GitHub のリポジトリ `mastermarisa71-arch/claudeclowdtest` にある。いまの作業はブランチ `claude/fervent-dirac-r7lv3x`。

## 1. ダウンロード（最初の1回）

### いるもの（Windows）
- **Git**（または GitHub Desktop）
- **Python 3.11 以上**：インストールのとき「Add python.exe to PATH」に印をつける
- **ffmpeg**：PATH に入れる（動画のコマ送り画像を作るのに使う）
- （Codex を使うなら）**Node.js**（LTS 版）

### おすすめ：GitHub Desktop（画面で操作）
1. GitHub Desktop を入れて、GitHub のアカウントでサインインする。
2. 「File → Clone repository」→ `mastermarisa71-arch/claudeclowdtest` を選び、置き場所を決める（例：`C:\Users\<名前>\Documents\claudeclowdtest`）。
   **パスに日本語やスペースがない場所**が無難。
3. 上の「Current branch」から `claude/fervent-dirac-r7lv3x` を選ぶ。
4. 置いたフォルダの `studio\setup.bat` をダブルクリック（必要なものが `studio\.venv` に入る。数分かかる）。
5. `studio\start.bat` をダブルクリック → ブラウザで月灯スタジオが開く。

### コマンドで（Git を使う場合）
```
cd C:\Users\<名前>\Documents
git clone https://github.com/mastermarisa71-arch/claudeclowdtest.git
cd claudeclowdtest
git checkout claude/fervent-dirac-r7lv3x
studio\setup.bat
studio\start.bat
```

### 9話の仮制作を載せる（動作確認）
```
studio\.venv\Scripts\activate
python studio\seeds\EP09_仮制作.py
python studio\seeds\EP09_仮制作.py --staff-sample
```

## 2. 新しい版にする（2回目から）
1. 黒いウィンドウ（月灯スタジオ）を閉じる。
2. GitHub Desktop で「Fetch origin」→「Pull origin」（コマンドなら `git pull`）。
3. 9話にあとから足した見本を入れるときは `python studio\seeds\EP09_仮制作.py --sheet`（レビューは消えない）。
4. `studio\start.bat`。

生成物と DB は `studio\data` にある（git には入らない）。別の場所に置くなら環境変数 `TSUKI_DATA`。

## 3. AI の連携

どの AI も、**リポジトリのフォルダを開いて使う**。手順書（Claude は `CLAUDE.md`、Codex は `AGENTS.md`）を自分で読み、月灯スタジオの道具（`studio\cli.py`、または MCP）で作業する。
**月灯スタジオ（start.bat）を先に起動しておく**と、AI の作業が画面にすぐ出る。

| AI | 役（AI 会議） | 名前（--agent） |
| --- | --- | --- |
| Claude A | 制作・まとめ | `claude-a` |
| Claude B | 芝居・見る | `claude-b` |
| Codex（GPT） | 演出・カット割り | `codex` |

担当は `月灯_vault\04_制作ルール\AIスタッフ.json` で入れ替えられる。

### Claude（Claude Code）
1. Claude のデスクトップアプリを開き、Claude Code（コード）でリポジトリのフォルダを開く。ターミナル版 `claude` なら、リポジトリのフォルダで `claude` と打つ。
2. 最初に「tsukiakari-studio（MCP サーバー）を使うか」と聞かれたら許可する（`.mcp.json` に書いてある）。
3. 確かめる：「`python studio/cli.py brief EP09` を見て、いまの状態を教えて」と頼む。9話の状態が返ればつながっている。
4. 2つ目の Claude（Claude B）は、別のウィンドウ（または別のアカウント）で同じフォルダを開く。頼むときに「あなたは claude-b」と伝える。

### Codex（GPT）
1. Codex を入れる（Codex のアプリ、または コマンドで `npm install -g @openai/codex`）。ChatGPT のアカウントでサインインする。
2. リポジトリのフォルダで Codex を開く（コマンドなら、そのフォルダで `codex`）。Codex は `AGENTS.md` を自分で読む。
3. 道具はコマンドで使える（`studio\.venv\Scripts\python.exe studio\cli.py …`）。追加の設定はいらない。
4. MCP でもつなぐとき（任意）は、`%USERPROFILE%\.codex\config.toml` に足す（パスは自分の置き場所に直す）：
   ```toml
   [mcp_servers.tsukiakari-studio]
   command = "C:\\Users\\<名前>\\Documents\\claudeclowdtest\\studio\\.venv\\Scripts\\python.exe"
   args = ["C:\\Users\\<名前>\\Documents\\claudeclowdtest\\studio\\mcp_server.py"]
   ```
5. 確かめる：「`studio\.venv\Scripts\python.exe studio\cli.py brief EP09` を見て、いまの状態を教えて」。

Codex のインストール方法や設定の書き方は版で変わることがある。動かないときは、出たエラーをそのままエージェントに貼る。

### AI 会議を回す（最初は手で）
1. 月灯スタジオで、シーン整理の「AI 会議にかける」（または「AI 会議」タブ）で会議を開く。
2. それぞれの AI に頼む：
   - Claude B に「`staff-claim --agent claude-b` して、ブリーフに沿って書いて」
   - Codex に「`staff-claim --agent codex` して、ブリーフに沿って書いて」
   - 1周目が済むと2周目の枠ができる。同じように頼む。
   - 全員が書いたら、Claude A に「`staff-claim --agent claude-a` して、まとめて。直しは案（version）にして」
3. 「AI 会議」タブで流れを、「④ 決める」で案を見る。

慣れたら、見張り番で自動にできる（AI ごとに黒いウィンドウを1つ）：
```
studio\staff_watch.bat codex
studio\staff_watch.bat claude-b
studio\staff_watch.bat claude-a
```
起こすときのコマンドは `AIスタッフ.json` の `agents`。CLI の版で書き方が変わるので、動かなければ黒いウィンドウの表示をエージェントに見せる。

### ふだんの頼み方
- 画面の「AI に頼む」に依頼を積んでおき、どの AI にも「依頼を1つ取って進めて」（`request-claim --agent <名前>`）と頼む。二重に進まない。
- 「AI（演出）に下書きを頼む」「案を出して」なども依頼として積まれる。
