# Seedance 2.5 プロンプトの書き方（月灯り用）

ショット（1本の動画、最大30秒）のプロンプトは、`shot-brief` が骨組みを作り、エージェントが仕上げる。
Seedance 2.5 は自分で考えて補うより、**書いたとおりに動く**。だから動き・秒数・誰がどの参照かを細かく書く。

出典（公開ガイド。公式の ByteDance / Volcengine の文書は未確認なので、HAMSTER での実際の結果で上書きしていく）：
[Runway: Seedance 2.5 prompt guide](https://runway.com/resources/seedance-2-5-prompt-guide)・
[Kapwing: How to prompt Seedance 2.5](https://www.kapwing.com/resources/how-to-prompt-seedance-2-5-a-guide-for-ai-video-creators/)

## 形（この順）

```
ASSETS        @Image N ごとに役割を1つだけ。何に使わないかも書く
FORMAT        16:9、秒数、480p ドラフト / 1080p、画風
SUMMARY       1文：どこで・誰が・何が起きる・ルック・カメラ
TIMELINE      SHOT n [a-bs] … 整数秒、隙間なし。各区切りに カメラ／配置／動き／表情／台詞／音
CONTINUITY    固定する特徴（髪・服・小物・背の順・画面の方向）を言い直す
AUDIO         Dialogue lip-sync only. No background music. No subtitles.
CONSTRAINTS   No on-screen text, no subtitles …（字幕・音の否定だけ。画は肯定形で書く）
```

## 月灯りの決まり

- **参照は最大10枚**（HAMSTER の Seedance 2.5）：背景（カメラ位置ごと）→ 配置図 → キャラ（1人1枚の設定資料）→ 小物。足りなければ小物 → 配置図 → 2枚目以降の背景の順に外す。
- **キャラの参照**：「@Image 3: あかね's appearance only (face, hairstyle, outfit, colors, head-to-body ratio, height). Do not copy the pose, the turnaround layout, or the plain background of the sheet.」のように、外見だけに使い、ポーズと背景は写さないと書く。区切りごとに「Characters: あかね＝@Image 3」と言い直す。
- **背景の参照**：カメラ位置・画角・家具の配置だけ。家具を足し引きしない。開始フレームではない。
- **区切り**：1区切りは字コンテの1カット（①②③…）。区切りの中で「① 2s: … ② 1s: …」とコマの動きを秒で書く。カットが変わるところは「Hard cut to …」と書く。動きは「始まり→途中→終わり」を1つの動作として書き、1秒ごとに細切れにしない。
- **芝居**：キャラの芝居の辞書（`06_設定/キャラ/<名前>.md`）のしぐさを、その感情の場面で具体的な動作として書く（「不安」ではなく「エプロンの裾を両手で握り、唇を噛む」）。
- **台詞**：`Dialogue (あかね, Japanese): "え？"`。画面にいない話者は「off-screen voice; show the listener's reaction」。仮の声は Runway で別に作るので、ドラフトの口の動きの目安として書く。
- **画面の方向**：店＝右、外＝左。カウンターの内側から撮る区切りは「camera behind the counter, mirrored from position A」と書く。
- **本番（1080p）**：採用したドラフトを入力に作る。冒頭に「Preserve the composition, camera position, timing, performance and lip movement of @Video 1. Only re-render at 1080p …」（`promote` が自動で付ける）。

## 送る前の点検（`shot-shoot` が自動で行う）

- 渡す参照の枚数と @Image の役割の行が一致しているか
- タイムラインが 0 秒から隙間なくつながり、30秒以内か
- 「No subtitles.」があるか
- 台詞に言語（Japanese）の指定があるか

指摘があれば止まる（`--force` で無視できるが、理由を `--note` に書く）。

## 結果から学ぶ

ドラフトの結果で「書いたのに出なかったこと」「書かずに出てしまったこと」は、セルフレビューのコメントに残す。2回続いたら `propose-rule --scope stage:prompt` でルールにし、この文書にも書き足す（監督の承認後）。
