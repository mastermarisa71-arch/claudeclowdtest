---
title: "EP01 冒頭マルチショット（Seedance 2.5）生成案"
date: 2026-10-10
tags: [EP01, 動画生成, Seedance2.5, プロンプト]
---

1話冒頭（S1-01〜S1-11）を Seedance 2.5 のマルチショットで動画にするための、カット割り・生成方法・プロンプトの骨組み。カットと画は[字コンテ v6](../字コンテ_v6/EP01_v6_指示書.md)と[並べ順リスト](../字コンテ_v6/EP01_v6_並べ順リスト.csv)に従う。ルールは[生成と字コンテのルール](../../../04_制作ルール/生成と字コンテのルール.md)。

## 1. 公式ガイドから押さえること（BytePlus『Dreamina Seedance 2.5 prompt guide』）

- 1本の上限は30秒。参照は画像30・動画10・音声10まで。
- **タイムスタンプが効く**（2.0は効かない）。単位は整数秒。`[0-3s]…[3-6s]…` のように**すき間なく**つなぐ。詰め込みすぎるとカットが飛び、少なすぎるとモデルが勝手に足す。
- **キーフレーム参照**：コマを1枚ずつ独立した画像として順に渡し、プロンプトの1文目に「Use Images X to Y in order as keyframes」と書くと、画が比較的厳密に合う。
- **マルチパネル（3×3シート）参照は「大まかな筋」にしか効かない**。15コマ以下、線画が推奨。AI生成の細かいシートや文字入りは非推奨。→ 9コマシートを直接渡すのはやめ、切り出し済みのコマ（cutouts）をキーフレームとして渡す。
- 参照画像は**番号と役割を本文で一つずつ結びつける**（画像の中に名前を書かない）。キャラは**初めて出る順**にアップロードする。
- 構成の順：一文のまとめ → 素材の割り当て → ショットごとの記述（画・カメラ・芝居・音）→ 全体で守ること。できるだけ肯定形で書く。否定が効くのは字幕と音（「no subtitles」「no BGM」）。
- BGMを止めたいときは、music / BGM / score / melody / instrumental / ambient pad を**列挙**し、**冒頭と末尾の両方**に書く。
- 強い感情語は「目が光る」原因になる。「normal eyes, no glowing eyes」を入れ、感情語は穏やかに。
- 参照画像は出力解像度より大きくしない（指紋のような模様が出る）。1080p出力なら1920×1080以下。
- 2.0と2.5は絵の好みがかなり違う。2.0の動画と混ぜる場合は注意。

## 2. Hamster 側の設定（月灯スピークイージー、10/10時点）

| 項目 | 値 |
|---|---|
| モデル | `dreamina-seedance-2-5-260628`（Seedance 2.5） |
| 尺 | 4〜30秒（-1で自動） |
| 解像度 | 480p / 720p / 1080p。**ドラフト（480p）→ 選んだものだけ本生成（1080p）**ができる（本生成は別課金、ドラフトの有効期限7日） |
| 参照 | 画像30、動画10、音声10。`omniReferenceTaskType: reference`（参照から新規生成）で比率・尺を固定できる |
| framing（始点・終点） | 1〜2枚。比率は画像に合わせて固定。1ショットしか作れないので、今回のマルチショットには使わない |
| seed | 2.5は非対応（毎回ランダム） |
| 出力 | mp4 / mov（あとで延長・編集する可能性があるなら mov） |

## 3. 生成方法

**キーフレーム参照によるマルチショット**を2本に分けて作る。

- 既に v6 の静止画編集で、各コマの切り出し（`e001/EP01_v6_Edit/cutouts/`）と中間コマ（`mid_cutouts/`）がある。これをそのまま**キーフレーム**として順に渡す。字コンテの画と動画がずれにくい。
- 1本に詰めず、**表通り（A）**と**路地〜投函（B）**の2本に分ける。A→Bのつなぎ目は、もともとカットが切り替わるところ（S1-06→S1-07）。
- 尺は整数秒にまとめて生成し、**編集で v6 の尺（0.5秒単位など）に詰め直す**。
- 音：生成では**環境音と足音だけ**にする（BGM・声・鼻歌なし）。暁の鼻歌と、あかねのNAは既存の音声（EP01_v6_mix など）を編集で載せる。2.5に声を作らせると、話ごとに声が変わるため。
- 黒板・手帳の文字は描かせない（ルールどおり、編集で「チョコパン」を合成）。

流れ：参照画像を準備 → A をドラフト（480p）で2〜3本 → 良いものを選んで本生成（1080p）→ 同じ設定で B → 編集で尺を詰め、音を載せる。

## 4. カット割り

### 生成A｜表通り（S1-01〜S1-06）12秒

| 秒 | ショット | v6の尺 | 画（並べ順リストより） | カメラ | 参照（キーフレーム） |
|---|---|---|---|---|---|
| 0-3s | S1-01 | 3.5 | 石畳を右へ歩く革靴 | 付けパン。靴と同じ速さで右へ。靴の位置は固定、石畳が左へ流れる | v2_sh01_k2 → mid_sh01_k1 → v2_sh01_k3 |
| 3-6s | S1-02 | 3.5 | 右へ歩く暁の背中（左斜め後ろ、顔なし）→肩越しの黒板 | 付けパン→減速して止まる | v6_sh01_k1 → mid_sh01_k2 → v2_sh01_k4 |
| 6-8s | S1-03 | 1.5 | 通りの奥に赤い懐中電灯の光が二つ。近づいて暁の背中に光の端 | 止め。光だけが近づく | v2_sh01_k5 → v2_sh01_k6 |
| 8-9s | S1-04 | 1.0 | 鼻歌の口元→一段寄り、赤い光が頬をなで、口が閉じる | 素早いT.U. | v2_sh01_k7 → v2_sh01_k8 |
| 9-11s | S1-05 | 1.5 | 歩く足がぴたりと止まり、半歩下がって右の角へ向く | 付けパン→足と同時に止まる | v2_sh02_k1 → mid_sh01_k3 → v2_sh02_k2 |
| 11-12s | S1-06 | 1.2 | 角の手前、壁に肩を寄せて右の路地をそっと確かめる。奥に赤い光 | 止め（芝居） | v6_sh01_k2 |

### 生成B｜角〜路地〜投函（S1-07〜S1-11）10秒

| 秒 | ショット | v6の尺 | 画 | カメラ | 参照（キーフレーム） |
|---|---|---|---|---|---|
| 0-1s | S1-07 | 1.0 | 角へ踏み出す暁→右端に消え、路地裏 | 右へ速い振り＋傾き10度→水平 | v2_sh02_k3 → v2_sh02_k4 |
| 1-4s | S1-08 | 3.0 | 路地の入口から暁の後ろ姿、扉の灯りが近づく | ドリーイン（暁との距離は一定） | v2_sh02_k5 → mid_sh01_k4 → v2_sh02_k6 → mid_sh01_k5 → v2_sh02_k7 |
| 4-6s | S1-09 | 2.0 | 暖色の灯りの扉の前で、暁の肩がすとんと下がる | T.B.（カメラだけ引く） | v6_sh01_k3 |
| 6-8s | S1-10 | 2.0 | 手帳にペンで書く手（文字なし） | 止め | EP01_sh01_k7 |
| 8-10s | S1-11 | 1.5 | ページを破り、折りたたみ、投函口へ差し入れる | 止め | EP01_sh01_k8 |

S2-01以降（扉の内側、あかね）は、A・Bの結果を見てから生成C（S2-01〜S2-13、約28秒）として作る。

## 5. プロンプトの骨組み（全ショット共通の型）

英語で書く（カメラ用語・アニメ用語の取りこぼしが少ない）。順番は公式の推奨どおり。

```
[0] KEYFRAMES        Use Images 1 to N in order as keyframes.
[1] SUMMARY          一文：誰が・どこで・何をする・ジャンル/画風・カメラ
[2] AUDIO RULE       音の制約（冒頭）
[3] ASSET BINDINGS   Image番号 → 役割（キーフレーム／キャラ／背景）を1行ずつ
[4] ART STYLE        画風・線幅・線の色・色トレス・影
[5] ANIMATION        コマ打ち（2コマ/3コマ）、止め、カメラは1コマ
[6] SECONDARY MOTION 髪揺れ・布揺れ・紙の動き
[7] COLOR / LIGHT    この生成のルック（N/C/B）、光源、色
[8] CHARACTER        外見・見せない部分・芝居の癖
[9] SCREEN DIRECTION 画面の方向（店=右、外=左）
[10] SHOT LIST       [0-3s] Shot 1 (S1-01): [ショットサイズ, カメラ位置, カメラの動き] 画 / 芝居 / 光 / 音
[11] CONSISTENCY     全体で守ること
[12] NEGATIVES       字幕・文字・目の発光・余計な人物
[13] AUDIO RULE      音の制約（末尾で繰り返す）
```

## 6. 生成A のプロンプト（そのまま使える形）

**画像の割り当て**（この順でアップロード）

| Image | ファイル（`e001/EP01_v6_Edit/`） | 役割 |
|---|---|---|
| 1 | cutouts/EP01_v2_sh01_k2.png | S1-01 始点 |
| 2 | mid_cutouts/EP01_v6_mid_sh01_k1.png | S1-01 中間 |
| 3 | cutouts/EP01_v2_sh01_k3.png | S1-01 終点 |
| 4 | cutouts/EP01_v6_sh01_k1.png | S1-02 始点 |
| 5 | mid_cutouts/EP01_v6_mid_sh01_k2.png | S1-02 中間 |
| 6 | cutouts/EP01_v2_sh01_k4.png | S1-02 終点（黒板） |
| 7 | cutouts/EP01_v2_sh01_k5.png | S1-03 始点 |
| 8 | cutouts/EP01_v2_sh01_k6.png | S1-03 終点 |
| 9 | cutouts/EP01_v2_sh01_k7.png | S1-04 始点 |
| 10 | cutouts/EP01_v2_sh01_k8.png | S1-04 終点 |
| 11 | cutouts/EP01_v2_sh02_k1.png | S1-05 始点 |
| 12 | mid_cutouts/EP01_v6_mid_sh01_k3.png | S1-05 中間 |
| 13 | cutouts/EP01_v2_sh02_k2.png | S1-05 終点 |
| 14 | cutouts/EP01_v6_sh01_k2.png | S1-06 |
| 15 | リファレンス/akira_moto_260909.png | 暁の外見 |
| 16 | リファレンス/パン屋の通り.png | 表通りの背景（1920×1080に縮小して渡す） |

**パラメータ**：model `dreamina-seedance-2-5-260628` / imageMode `reference` / omniReferenceTaskType `reference` / ratio `16:9` / durationSec `12` / draft `true`（480p）/ generateAudio `true` / outputFormat `mov`

```
Use Images 1 to 14 in order as keyframes.

A 2D Japanese TV-anime opening sequence: on a cold blue night in a town where fun is forbidden, Akira, a young woman reporter, walks along a closed-shop street, slows at a bakery chalkboard, notices two distant red patrol flashlights, stops, and checks the dark alley around the corner. Hand-drawn cel animation, six shots, camera stays close to her.

Audio: natural sound only — footsteps on stone, faint distant city hum, light wind. No music of any kind: no BGM, no score, no melody, no instrumental, no ambient pad, no synth. No dialogue, no narration, no humming, no voice.

Asset bindings:
- Images 1-14: keyframes for Shots 1-6, in order. Match their composition, framing, character position and lighting.
- Image 15: Akira's three-view character sheet. Use only for hair color, hairstyle and outfit. Her face is never shown in this video.
- Image 16: the bakery street at night. Use for the environment and background art style.

Art style:
2D hand-drawn TV anime, digital ink and paint, cel-shaded characters over painted backgrounds. Not 3D, not CG, not photoreal, not a painterly illustration.
Line art: thin, clean, even-weight lines. Character outer contour about 2.5 px at 1080p, inner detail lines about 1.5 px, no brush taper, no sketchy double lines. Lines are never pure black: character lines are a deep plum-brown (#3B2A33); in these cold night shots the lines lean toward deep navy (#1E2340).
Color trace (iro-tore): inner lines of hair, highlight edges, shadow boundaries on skin and cloth are drawn in a darker tint of the neighboring fill color instead of the line color — orange hair uses burnt-sienna lines, skin uses rose-brown lines.
Shading: two-tone cel shading (base + one hard-edged shadow), one hard highlight shape on hair, no soft gradients on characters except a thin rim light. Shadows shift toward blue-violet. Backgrounds are painted with no outlines.

Animation timing:
24 fps output. Character animation is drawn on twos (12 drawings per second); small acting such as a shoulder drop is on threes. Holds are true holds: the drawing stays still and only hair and coat secondary motion moves. Camera moves (tracking pan, push-in, stop) are smooth on ones, as if the background layer slides under the cel. No morphing between poses, no frame-blend ghosting, no AI interpolation smoothness.

Secondary motion (hair and cloth):
Akira's orange hair is tied in a loose low bun with stray strands. The strand tips swing 1–2 frames after each footstep and the bun bounces slightly on each step. When she stops, the hair settles in two small diminishing swings and then rests. No floating hair, no constant wind waving. The coat hem sways in rhythm with her steps and settles when she stops.

Color and light (Look N, cold night):
Coldest palette of the episode: blue and blue-grey, cold white streetlights, deep navy shadows. The bakery window and wall lamp give a small, contained warm glow only on the right edge. The only strong color accent is the red of two patrol flashlights far down the street. From Shot 5 the frame is one step darker and shadows shift further to blue (Look C, tension).

Character: Akira, a young woman newspaper reporter heading home from work. Long dark navy coat, shoulder-bag strap over her right shoulder, dark ankle boots with a block heel. Relaxed, slightly loose posture at night. Face never visible: only feet, back, the edge of her mouth and jaw, hands, and silhouette.

Screen direction: the bar is to screen right and the town is to screen left. Akira always faces right and walks left to right.

Shots:
[0-3s] Shot 1 (S1-01): [low close shot at ankle height, side view, tracking pan right] Keyframes Images 1→2→3. A leather ankle boot walks right on wet cobblestones in front of closed shutters. The camera tracks right at exactly the same speed, so the boot stays in the same place in frame while the cobblestone seams and shutters slide left. Walk cycle on twos, heel-to-toe weight shift.
[3-6s] Shot 2 (S1-02): [medium shot from behind her left shoulder, tracking pan right that slows and stops] Keyframes Images 4→5→6. Akira walks right along the closed-shop street, one hand in her coat pocket. A sandwich-board chalkboard with only a chalk bread drawing slides in from the right. She slows down; the camera slows with her and stops in an over-the-shoulder framing on the chalkboard. Far down the street a tiny red light.
[6-8s] Shot 3 (S1-03): [locked-off wide shot down the street] Keyframes Images 7→8. The camera does not move. Two red handheld flashlight beams far down the street come closer and grow larger; the edge of the red light reaches Akira's back. Footsteps of the patrol grow slightly louder.
[8-9s] Shot 4 (S1-04): [extreme close-up of mouth and jaw, quick push-in] Keyframes Images 9→10. A quick push-in of about 0.3 seconds to her lips. Red light brushes across her cheek and her relaxed mouth closes.
[9-11s] Shot 5 (S1-05): [low shot at foot height, tracking right then stopping] Keyframes Images 11→12→13. His walking feet slide right with the camera, then stop dead; the camera stops at the same instant. She takes half a step back and her toes turn toward the corner on the right. The edge of the red light skims the cobblestones.
[11-12s] Shot 6 (S1-06): [medium shot behind her back at the street corner, locked-off] Keyframe Image 14. Akira presses her shoulder against the wall, her face in shadow, and carefully looks around the corner into the dark alley on the right. Red light far down the street behind her on the left.

Overall: keep Akira's hair color, bun, coat and bag identical in every shot. Cuts are hard cuts on the timestamps; no dissolves. The street, shutters, chalkboard and lamp stay in the same places as in the keyframes. Stable lines, no line boiling, no flicker.

No subtitles. No text, letters or numbers anywhere; the chalkboard shows only the chalk bread drawing. Normal eyes, no glowing eyes. No other people except the distant red flashlight carriers as tiny dark silhouettes.

Audio again: footsteps, light wind and faint city hum only. No music, BGM, score, melody, instrumental or ambient pad. No voice, no humming.
```

## 7. 生成B のプロンプト（差分だけ）

画像の割り当て：Image 1-2＝S1-07（v2_sh02_k3, k4）／3-7＝S1-08（v2_sh02_k5, mid_sh01_k4, v2_sh02_k6, mid_sh01_k5, v2_sh02_k7）／8＝S1-09（v6_sh01_k3）／9＝S1-10（EP01_sh01_k7）／10＝S1-11（EP01_sh01_k8）／11＝暁（akira_moto）／12＝背景（月明かりの路地.png を縮小）。durationSec `10`。

アート・コマ打ち・髪揺れ・音・禁止は生成Aと同じ文をそのまま使い、ルックとショットだけ差し替える。

```
Color and light: Shot 1 is Look C (tension, one step darker, blue-shifted shadows, red light behind her). From Shot 2 the alley is Look N (cold blue), and the red light never enters the alley. In Shot 3 the first warm color of the episode appears: a small honey-colored lamp above a wooden door at the far end of the alley.

Secondary motion addition: in Shots 4-5 the notebook page and the folded paper move with real paper weight — the page bends as it is torn, the folded note is stiff, a slight flutter only when it leaves her fingers. No floating paper.

[0-1s] Shot 1 (S1-07): [medium shot at the street corner, fast whip pan right with rotation] Keyframes Images 1→2. Akira steps around the corner. The camera whips right fast while the frame tilt rotates from 10 degrees back to level. Only the background streaks horizontally; Akira disappears off the right edge into the dark alley.
[1-4s] Shot 2 (S1-08): [wide shot from the alley entrance, steady dolly-in behind her] Keyframes Images 3→4→5→6→7. The camera follows Akira's back at a constant distance deeper into the narrow alley. The lamp above the door grows closer. At the near edge of frame the red light crosses the main street but does not enter the alley.
[4-6s] Shot 3 (S1-09): [wide shot, slow pull-back] Keyframe Image 8. Akira stops in front of the small warm-lit door; her shoulders drop as she exhales. Only the camera slowly pulls back, showing the narrow dark alley and the small warm door.
[6-8s] Shot 4 (S1-10): [insert close-up of hands, locked-off] Keyframe Image 9. In front of the old door, her hand writes in a small notebook with a pen. The page has pen strokes only, no readable letters.
[8-10s] Shot 5 (S1-11): [insert close-up of hands, locked-off] Keyframe Image 10. She tears out the page, folds it small, and slides it into the narrow mail slot in the door. Paper sound.
```

## 8. 生成前に確認すること

1. **左右反転**：並べ順リストで「左右反転」の S1-01（v2_sh01_k2, k3）、S1-05（v2_sh02_k1, k2）、S1-07（v2_sh02_k3, k4）。cutouts の v2_sh01_k2 は靴先が右向き（＝正しい向き）だった。残りも、暁が右へ進む向きになっているか確かめ、逆なら反転した画像を渡す。
2. **背景画像の縮小**：`リファレンス/パン屋の通り.png` などは約6MBで、出力解像度より大きい可能性がある。1920×1080以下にして渡す。
3. **mid コマの扱い**：中間コマは、始点・終点と人物が違うものがあった（M02-1〜4は不採用）。S1の中間（mid_sh01_k1〜k5）は採用済みだが、気になるなら外して始点・終点だけにする。
4. **既存のSeedance 2.5テスト**：`e001/EP01_Seedance25_Test01〜03` などがある。そのとき何がうまくいかなかったかが分かれば、プロンプトに反映する。

## 9. 確認するポイント（ドラフトを見るとき）

- ショットの順番とタイムスタンプが合っているか（カットが飛んでいないか、勝手なカットが増えていないか）
- 暁の顔が出ていないか、髪色・まとめ髪・コートが変わらないか
- 線が黒くないか、色トレスが出ているか、3DCG風になっていないか
- 動きがヌルヌル（補間）になっていないか、止めが止まっているか
- 髪が歩みに遅れて揺れ、止まると収まるか
- 黒板に文字が出ていないか、字幕が出ていないか、BGMが入っていないか

Related: [EP01 v6 指示書](../字コンテ_v6/EP01_v6_指示書.md) · [EP01 演出設計](../EP01_演出設計.md) · [生成と字コンテのルール](../../../04_制作ルール/生成と字コンテのルール.md)

出典：BytePlus ModelArk『Dreamina Seedance 2.5 prompt guide』 https://docs.byteplus.com/en/docs/modelark/seedance-2-5-prompt-guide （2026-10-10 参照）
