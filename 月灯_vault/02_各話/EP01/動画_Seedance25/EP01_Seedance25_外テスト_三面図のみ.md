---
title: "EP01 外カット テスト（Seedance 2.5、三面図＋背景のみ）"
date: 2026-10-10
tags: [EP01, 動画生成, Seedance2.5, テスト]
---

切り出しコマ・中間コマは使わず、**三面図と背景だけ**を参照して、キャラの動作の書き方を試すテスト。カットは[字コンテ v6](../字コンテ_v6/EP01_v6_並べ順リスト.csv)の外のカットから抜き出した。後で3Dのレイアウトから生成する方式に移る前の、動作記述の確認用。

共通設定：model `dreamina-seedance-2-5-260628` / imageMode `reference` / omniReferenceTaskType `reference` / 16:9 / 15秒 / draft（480p）/ mov。参照画像は長辺1920pxに縮小して渡す。

## テスト1｜暁の帰り道（S1-02, S1-03, S1-06, S1-08〜09）

動きの確認：歩き→減速→停止、振り返らずに気配に気づく、壁に肩を寄せて覗く、路地を進んで扉の前で肩が落ちる。髪（お団子とカール）とジャケットの揺れ。顔は字コンテどおり見せない。音は環境音と足音のみ。

| Image | ファイル | 役割 |
|---|---|---|
| 1 | リファレンス/akira_moto_260909.png | 暁の三面図 |
| 2 | リファレンス/パン屋の通り.png | 表通り（昼の絵→夜・閉店後に変換） |
| 3 | リファレンス/月明かりの路地.png | 路地 |

```
A 2D Japanese TV-anime sequence: on a cold blue night in a town where fun is forbidden, Akira, a young woman reporter, walks home along a closed-shop street, senses two distant red patrol flashlights, checks the dark alley around the corner, then slips down the alley to a small warm-lit door. Four shots, hand-drawn cel animation, the camera stays close to her and never shows her face.

Audio: natural sound only — her footsteps on stone, faint distant city hum, light wind, distant patrol footsteps. No music of any kind: no BGM, no score, no melody, no instrumental, no ambient pad, no synth. No dialogue, no narration, no humming, no voice.

Asset bindings:
- Image 1: Akira's three-view character sheet (front, side, back). Use it for her hair, glasses, outfit and body proportions. It is one person; ignore the white background and the sheet layout.
- Image 2: the bakery street. Use only for the architecture, cobblestones, bollards, lamps and painted-background style. Convert it to late night after closing: shop lights off, shutters and blinds down, empty street with no pedestrians, only the street lamps lit.
- Image 3: the narrow brick back alley at night. Use for the alley in Shot 4. Wall notices are blank, illegible paper.

Art style:
2D hand-drawn TV anime, digital ink and paint, cel-shaded characters over painted backgrounds. Match the clean flat look of Image 1. Not 3D, not CG, not photoreal, not a painterly illustration.
Line art: thin, clean, even-weight lines. Character outer contour about 2.5 px at 1080p, inner detail lines about 1.5 px, no brush taper, no sketchy double lines. Lines are never pure black: character lines are a deep plum-brown (#3B2A33); in these cold night shots they lean toward deep navy (#1E2340).
Color trace (iro-tore): inner lines of hair, highlight edges and shadow boundaries on skin and cloth are drawn in a darker tint of the neighboring fill color instead of the line color — orange hair uses burnt-sienna lines, skin uses rose-brown lines.
Shading: two-tone cel shading (base + one hard-edged shadow), one hard highlight shape on hair, no soft gradients on characters except a thin cool rim light. Shadows shift toward blue-violet. Backgrounds are painted with no outlines.

Animation timing:
24 fps output. Character animation is drawn on twos (12 drawings per second); small acting such as the shoulder drop is on threes. Holds are true holds: the drawing stays still and only hair and jacket secondary motion moves. Camera moves are smooth on ones, as if the background layer slides under the cel. No morphing between poses, no frame-blend ghosting, no AI interpolation smoothness. Walking has clear weight: heel strike, body drops slightly on contact, rises on passing.

Secondary motion (hair and cloth):
Akira's orange hair has two small buns at the back with loose curled ends. The curls bounce 1–2 frames after each footstep; the buns stay firm. When she stops, the curls settle in two small diminishing swings and rest. No floating hair, no constant wind waving. The wide sleeves of her jacket and the grey hanging straps swing with her arms and settle after she stops. The camera on its lanyard swings slightly against her chest.

Color and light (Look N, cold night):
Coldest palette: blue and blue-grey, cold white street lamps, deep navy shadows. No warm light anywhere except the small door lamp in the last shot. The only strong accent is the red of two patrol flashlights far down the street. Shots 2–3 are one step darker with shadows shifted further to blue (tension).

Character: Akira (Image 1), a young woman newspaper reporter heading home from work. Orange hair with two small curled buns, red-framed glasses, light-blue shirt, oversized navy cropped jacket with wide sleeves and grey hanging straps, small camera on a lanyard, navy shorts, grey knee-high boots. Relaxed, slightly loose posture at night, one hand in her jacket pocket. Her face is never shown: only her back, the back of her head, her shoulder, hands, feet and silhouette.

Screen direction: the bar is to screen right and the town is to screen left. Akira always faces right and moves left to right.

Shots:
[0-4s] Shot 1: [medium shot from behind her left shoulder, waist up, tracking right] Akira walks right along the dark closed-shop street, one hand in her pocket, head slightly lowered. The camera tracks with her at the same speed so she stays in the left third of the frame while the shutters and lamps slide left. A sandwich-board chalkboard outside the closed bakery slides in from the right; she slows down, and the camera slows with her and stops in an over-the-shoulder framing on the chalkboard. Far down the street, a tiny red light.
[4-7s] Shot 2: [locked-off wide shot down the street, Akira small in the left foreground, back to camera] The camera does not move. Akira stands still. Two red handheld flashlight beams far down the street come closer and grow larger, carried by two tiny dark silhouettes. The edge of the red light reaches her back. Her shoulders tense slightly and her hand comes out of her pocket. Patrol footsteps get a little louder.
[7-10s] Shot 3: [medium shot behind her back at the street corner, locked-off] Akira presses her shoulder against the brick wall at the corner, her face hidden in shadow, and carefully leans to look around the corner into the dark alley on the right. She holds still for a beat, then pushes off the wall. Red light glows far down the street behind her on the left.
[10-15s] Shot 4: [wide shot from the alley entrance, steady dolly-in behind her, then a slow pull-back] Akira walks deeper into the narrow brick alley (Image 3); the camera follows her back at a constant distance. A small honey-colored lamp above a wooden door at the far end is the first warm color of the night. She stops in front of the door; her shoulders drop as she exhales. The camera stops, then only the camera slowly pulls back, showing the narrow dark alley and the small warm door with her small figure in front of it.

Overall: keep Akira's hair, buns, glasses, jacket, straps, camera and boots identical in every shot and consistent with Image 1. Hard cuts on the timestamps, no dissolves. Stable lines, no line boiling, no flicker.

No subtitles. No text, letters or numbers anywhere; the chalkboard is blank dark slate. Normal eyes, no glowing eyes. No other people except the two distant flashlight carriers as tiny dark silhouettes.

Audio again: footsteps, light wind and faint city hum only. No music, BGM, score, melody, instrumental or ambient pad. No voice, no humming.
```

## テスト2｜捜査官の二人（S8-02, S8-03, S8-05, S8-09）

動きの確認：二人の歩き（体格差）、立ち止まり、ピン送り、手をポケットから出す、指さし、舌打ちして歩き出す。先輩のツインテールの揺れ、後輩の片目を隠す前髪。顔と台詞の口の動き（三面図にどこまで似るか）。台詞は生成させる（声はテスト用）。

| Image | ファイル | 役割 |
|---|---|---|
| 1 | リファレンス/senpai_moto_260914.png | 先輩の三面図 |
| 2 | リファレンス/kohai_moto_260914.png | 後輩の三面図 |
| 3 | リファレンス/パン屋外観.png | パン屋の店先（昼→夜・閉店後） |
| 4 | リファレンス/パン屋の通り.png | 表通り（昼→夜） |

```
A 2D Japanese TV-anime sequence: late at night on an empty street outside a closed bakery, two patrol inspectors — a tiny, dignified senior officer and her tall, lazy junior — come out of a back alley with a red flashlight, stop, exchange a few words, and leave. Four shots, hand-drawn cel animation, dialogue in Japanese.

Audio: only the two characters' voices, their footsteps on stone, light wind and faint city hum. No music of any kind: no BGM, no score, no melody, no instrumental, no ambient pad, no synth.

Asset bindings:
- Image 1: the Senior Inspector's three-view character sheet (front, back, side, and her cap). Use it for her face, hair, cap, outfit and small body proportions. One person; ignore the sheet layout and white background.
- Image 2: the Junior Inspector's three-view character sheet (front, side, back). Use it for her face, hair, outfit and tall proportions. One person; ignore the sheet layout and white background.
- Image 3: the bakery shopfront. Use for the building, window, wall lamp and painted-background style. Convert it to late night after closing: the shop is dark inside, no people, the chalkboard is blank dark slate, the bicycle stays.
- Image 4: the bakery street. Use for the cobblestone street, bollards and street lamps. Convert to late night, empty, no pedestrians.

Art style:
2D hand-drawn TV anime, digital ink and paint, cel-shaded characters over painted backgrounds. Match the clean flat look of Images 1 and 2. Not 3D, not CG, not photoreal, not a painterly illustration.
Line art: thin, clean, even-weight lines. Character outer contour about 2.5 px at 1080p, inner detail lines about 1.5 px, no brush taper, no sketchy double lines. Lines are never pure black: character lines are a deep plum-brown (#3B2A33), leaning toward deep navy (#1E2340) in the night light.
Color trace (iro-tore): inner lines of hair, highlight edges and shadow boundaries on skin and cloth are drawn in a darker tint of the neighboring fill color — mint-white hair uses teal-grey lines, lavender hair uses deep violet lines, skin uses rose-brown lines.
Shading: two-tone cel shading (base + one hard-edged shadow), one hard highlight shape on hair, no soft gradients on characters except a thin cool rim light and the red flashlight spill. Shadows shift toward blue-violet. Backgrounds are painted with no outlines.

Animation timing:
24 fps output. Character animation is drawn on twos (12 drawings per second); small acting such as eye movement and the hands leaving the pockets is on threes. Holds are true holds: the drawing stays still and only hair and coat secondary motion moves. Mouths move only while that character speaks; a closed mouth stays closed. Camera moves are smooth on ones. No morphing between poses, no frame-blend ghosting, no AI interpolation smoothness.

Secondary motion (hair and cloth):
The Senior Inspector's very long twin tails (white fading to mint) swing with clear follow-through: they trail 2–3 frames behind her body, swing out when she turns, and settle in two or three diminishing swings when she stops. The tips never float upward. Her oversized coat hem and the hanging belt straps sway with her small steps.
The Junior Inspector's short lavender hair moves only a little; her long bangs keep covering one eye at all times. Her off-shoulder coat slips and sways with her slouching walk.

Color and light (Look N, cold night):
Blue and blue-grey palette, cold white street lamps, deep navy shadows. The Senior Inspector holds a handheld flashlight with a red beam; the red light pools on the cobblestones and spills on their legs and coats. No warm light except a faint, dark bakery window.

Characters:
- Senior Inspector (Image 1): very small and young-looking but dignified. Very long white-to-mint twin tails, blunt bangs, green eyes, dark grey peaked officer cap with a diamond emblem, oversized dark grey double-breasted coat with taupe lapels and rolled cuffs, emblem patch on her LEFT upper arm, red tie, black shorts, thigh belt, white socks, black loafers. She walks with her hands clasped behind her back, chin up; she never crouches. Calm, slightly old-fashioned speech.
- Junior Inspector (Image 2): tall, slouching, bored. Short wavy lavender hair with long bangs covering one eye, black choker, white shirt with a loose red tie and suspenders, dark grey coat worn off the shoulders, black tights torn at one knee, black boots. Hands in her coat pockets. Lazy drawling voice.
She is about twice the Senior Inspector's height; the Senior Inspector's head reaches only her chest.

Screen direction: the inspectors walk from screen right to screen left (from the bar's alley toward the town).

Shots:
[0-4s] Shot 1: [medium-wide shot on the street, tracking left] From the dark alley corner on the right, the red flashlight beam appears, then the small Senior Inspector and the tall Junior Inspector step out onto the street and walk left. The camera tracks left with them, keeping them in the center. The Junior Inspector, hands in pockets, looks down at her: Junior Inspector's line (bored): 「この辺の路地、全部見る必要あります？」 The Senior Inspector, not looking up, keeps walking: Senior Inspector's line (firm): 「担当エリアじゃ。見とらん場所があってたまるか」
[4-8s] Shot 2: [medium shot in front of the dark bakery, rack focus and slight pan right] The Senior Inspector, sharp in the left foreground, suddenly stops; her twin tails swing forward and settle. Senior Inspector's line (quiet): 「……ん？」 The focus shifts to the Junior Inspector behind her on the right, who looks down at her lazily with her hands still in her pockets. Junior Inspector's line (teasing): 「また何か見つけちゃいましたー？」
[8-11s] Shot 3: [medium close-up of the Junior Inspector, locked-off] Off-screen, Senior Inspector's line (low): 「さっき、猫の声がした」 The Junior Inspector slowly takes both hands out of her pockets; her bored face turns serious and her visible eye turns toward the dark alley. Junior Inspector's line (serious, quiet): 「……この辺で？」
[11-15s] Shot 4: [medium shot on the street, whip pan left with rack focus] The Junior Inspector on the right points far down the street to the left. Junior Inspector's line (flat): 「あー、酔っ払い発見」 The camera whips left and the focus lands on the Senior Inspector, who clicks her tongue and starts walking left, the red flashlight swinging. Senior Inspector's line (annoyed): 「……チッ、行くぞ！」 Her twin tails whip around as she turns.

Overall: keep both characters' faces, hair, caps and outfits identical in every shot and consistent with Images 1 and 2. Keep their height difference constant. Hard cuts on the timestamps, no dissolves. Stable lines, no line boiling, no flicker.

No subtitles. No text, letters or numbers anywhere; the chalkboard and shop signs are blank. Normal eyes, no glowing eyes. No other people.

Audio again: only the two voices, footsteps, light wind and faint city hum. No music, BGM, score, melody, instrumental or ambient pad.
```

## テスト1 v2（10/10のレビューを反映）

| Image | ファイル | 役割 |
|---|---|---|
| 1 | リファレンス/akira_moto_260909.png | 暁の三面図 |
| 2 | リファレンス/パン屋の通り.png | 表通り（最初から夜） |
| 3 | リファレンス/月明かりの路地.png | 月灯りの左の路地（反転しない。右の壁の扉＝月灯り） |

位置関係（正面の通り＝パン屋の通り.png）：真ん中がパン屋と月灯り、右がおばあの家（突き当たりとつながっていて路地はない）、左が新しく建った建物。**新しい建物とパン屋のあいだに路地**がある。路地に入ると、右の壁が月灯り（扉あり）、左の壁は新しい建物（扉なし）。

```
A 2D Japanese TV-anime sequence set entirely at deep night: in a town under heavy patrol, Akira, a young woman reporter, walks home along a closed-shop street past patrolling inspectors, stops as a patrol car with a red rotating light approaches, peeks around a corner, vanishes as the car sweeps past, and slips into a narrow side alley to a plain unlit door on the right wall. Four shots, hand-drawn cel animation. Her face is never shown.

Audio: natural sound and sirens only — her footsteps on stone, a patrol siren wailing in the distance from the very first second and growing louder as the patrol car approaches, the car engine and tires passing close by in Shot 3, distant patrol footsteps, light wind. No music of any kind: no BGM, no score, no melody, no instrumental, no ambient pad, no synth. No dialogue, no narration, no humming, no voice.

Asset bindings:
- Image 1: Akira's three-view character sheet (front, side, back). Use it for her hair, glasses, outfit and body proportions. It is one person; ignore the white background and the sheet layout.
- Image 2: the bakery street, seen from the front. Keep this exact row of buildings: in the center the brick bakery (the hidden bar is inside this building); to its right the old woman's brick house with the green garage shutter, joined directly to the bakery with no gap; to its left the newer light-grey concrete apartment building. The only alley is the narrow gap between the grey building and the bakery. Use Image 2 for the architecture, cobblestones, bollards, street lamps and painted-background style. It is deep night from the first frame to the last — never daytime, no day-to-night transition. Shops closed and dark, shutters down, no civilians, only street lamps lit.
- Image 3: the inside of that alley, seen from the street entrance, used for Shot 4. Do not mirror it. The right wall is the bakery/bar building, and the teal wooden door partway down the right wall is the bar's door. The left wall is the side of the newer grey building: plain wall, pipes and utility boxes, no doors. There is no lamp over the bar's door and nothing glowing at the end; beyond the door the alley simply continues, narrow and dark, into the distance. Wall notices are blank, illegible paper.

Patrol inspectors (background extras): the town's inspectors wear long dark grey uniform coats and dark grey peaked caps, and carry handheld flashlights with red beams. Their faces are never clearly visible; they appear as silhouettes, backs, shoulders and caps.

Art style:
2D hand-drawn TV anime, digital ink and paint, cel-shaded characters over painted backgrounds. Match the clean flat look of Image 1. Not 3D, not CG, not photoreal, not a painterly illustration.
Line art: thin, clean, even-weight lines. Character outer contour about 2.5 px at 1080p, inner detail lines about 1.5 px, no brush taper, no sketchy double lines. Lines are never pure black: character lines are a deep plum-brown (#3B2A33), leaning toward deep navy (#1E2340) in this night light.
Color trace (iro-tore): inner lines of hair, highlight edges and shadow boundaries on skin and cloth are drawn in a darker tint of the neighboring fill color instead of the line color — orange hair uses burnt-sienna lines, skin uses rose-brown lines.
Shading: two-tone cel shading (base + one hard-edged shadow), one hard highlight shape on hair, no soft gradients on characters except a thin cool rim light and the moving red light. Shadows shift toward blue-violet. Backgrounds are painted with no outlines.

Animation timing:
24 fps output. Character animation is drawn on twos (12 drawings per second); small acting such as the shoulder drop is on threes. Holds are true holds: the drawing stays still and only hair and jacket secondary motion moves. Camera moves are smooth on ones, as if the background layer slides under the cel. No morphing between poses, no frame-blend ghosting, no AI interpolation smoothness. Walking has clear weight: heel strike, body drops slightly on contact, rises on passing.

Secondary motion (hair and cloth):
Akira's orange hair has two small buns at the back with loose curled ends. The curls bounce 1–2 frames after each footstep; the buns stay firm. When she stops, the curls settle in two small diminishing swings and rest. No floating hair, no constant wind waving. The wide sleeves of her jacket and the grey hanging straps swing with her arms and settle after she stops.

Color and light (one consistent night look for all four shots):
Deep night, dark blue and blue-grey, cold white street lamps, deep navy shadows, the same dark low-key lighting in every shot. No warm light anywhere. The only strong accent is red: the inspectors' red flashlights and the patrol car's rotating red light. The red light is never static: the rotating light sweeps across walls, cobblestones and Akira's back, and as the car comes closer the red patches grow larger, brighter and slide across the frame.

Character: Akira (Image 1), a young woman newspaper reporter heading home from work. Orange hair with two small curled buns, red-framed glasses, light-blue shirt, oversized navy cropped jacket with wide sleeves and grey hanging straps, small camera on a lanyard, navy shorts, grey knee-high boots. One hand in her jacket pocket. Her face is never shown: only her back, the back of her head, her shoulder, hands, feet and silhouette.

Screen direction: the bar is to screen right and the town is to screen left. On the street Akira faces right and moves left to right.

Shots:
[0-4s] Shot 1: [medium shot, foreground over-the-shoulder framing on an inspector, locked-off] Deep night from the first frame. In the left foreground, very large and out of focus, the dark back, shoulder and peaked cap of a standing patrol inspector fill about a third of the frame, a red flashlight beam hanging from his hand toward the ground. In the gap behind him, in sharp focus in the middle distance, Akira walks left to right along the closed shops, small in frame, one hand in her pocket, head slightly lowered, not looking at him. Further down the street two more inspectors stand with red flashlights. A siren wails far away.
[4-7s] Shot 2: [locked-off wide shot down the street, Akira small in the left foreground, back to camera] Akira slows down and stops; her curls settle. At the far end of the street a patrol car with a rotating red light turns into the street and drives toward the camera; one or two inspectors stand at the far intersection. The rotating red light sweeps across the shopfronts and reaches her back. Her shoulders tense slightly and her hand comes out of her pocket. The siren gets louder.
[7-11s] Shot 3: [medium shot from across the street facing the buildings, locked-off] The corner where the grey concrete building ends and the narrow alley opens between it and the bakery. Akira presses her back and shoulder against the grey building's corner wall and carefully leans to peek into the dark alley gap, her face hidden in shadow. The red light grows brighter and slides across the walls as the car approaches. At 9s the patrol car passes along the street through the foreground from left to right, between the camera and her, close to the camera, its dark body and rotating red light wiping across the whole frame with horizontal motion blur. At 10s the car has passed: the corner is empty — Akira has slipped into the alley and is gone. Only the red light sliding away across the empty walls, and the siren fading.
[11-15s] Shot 4: [medium-wide shot inside the alley from Image 3, from the street entrance, camera behind her, short follow then stop] Akira walks away from the camera into the narrow dark alley, quickly and quietly, keeping close to the right wall. Partway down she stops at the teal wooden door on the right wall (the bar's door) and turns toward it; her shoulders drop as she exhales. The left wall (the grey building) has no doors. Beyond her the alley continues, narrow and dark, into the distance. The camera follows a few steps, then stops and holds. Faint red light flickers once at the alley entrance behind the camera and is gone.

Overall: keep Akira's hair, buns, glasses, jacket, straps, camera and boots identical in every shot and consistent with Image 1. Hard cuts on the timestamps, no dissolves. Stable lines, no line boiling, no flicker.

No subtitles. No text, letters or numbers anywhere; signs, notices and the chalkboard are blank. Normal eyes, no glowing eyes. No civilians; the only other people are the patrol inspectors as dark silhouettes.

Audio again: footsteps, sirens, car engine, light wind and faint city hum only. No music, BGM, score, melody, instrumental or ambient pad. No voice, no humming.
```

## テスト1 v3（10/11のレビューを反映）

参照画像はv2と同じ（暁の三面図／パン屋の通り／月明かりの路地）。

```
A 2D Japanese TV-anime sequence set entirely at deep night: in a town crowded with patrolling inspectors, Akira, a young woman reporter, walks home along a closed-shop street, weaving past inspectors coming the other way, slips into the narrow side alley next to the bakery, checks the main street from inside the alley as a patrol car passes, then walks deeper into the safe, dark alley to a plain door on the right wall. Four shots, hand-drawn cel animation. Her face is never shown.

Audio: natural sound and sirens only — her footsteps on stone, many inspectors' footsteps passing, a patrol siren wailing in the distance from the very first second and growing louder as the patrol car approaches, the car engine and tires passing the alley mouth in Shot 3, light wind. Inside the alley in Shot 4 the street noise and siren are muffled and distant. No music of any kind: no BGM, no score, no melody, no instrumental, no ambient pad, no synth. No dialogue, no narration, no humming, no voice.

Asset bindings:
- Image 1: Akira's three-view character sheet (front, side, back). Use it for her hair, glasses, outfit and body proportions. It is one person; ignore the white background and the sheet layout.
- Image 2: the bakery street, seen from the front. Keep this exact row of buildings: in the center the brick bakery (the hidden bar is inside this building); to its right the old woman's brick house with the green garage shutter, joined directly to the bakery with no gap; to its left the newer light-grey concrete apartment building. The only alley is the narrow gap between the grey building and the bakery. Use Image 2 for the architecture, cobblestones, bollards, street lamps and painted-background style. It is deep night from the first frame to the last — never daytime, no day-to-night transition. Every shop is closed with its lights off: the bakery window is dark inside, no warm light behind any window. Only the street lamps are lit.
- Image 3: the inside of that alley, seen from the street entrance, used for Shots 3 and 4. Do not mirror it. The right wall is the bakery/bar building, and the teal wooden door partway down the right wall is the bar's door. The left wall is the side of the newer grey building: plain light-grey concrete wall with pipes and utility boxes, no doors, no posters. There is no lamp over the bar's door. Beyond the door the alley simply continues, narrow and dark, fading into a soft dark night haze in the distance.

Patrol inspectors (background extras): the town's inspectors wear long dark grey uniform coats and dark grey peaked caps, and carry handheld flashlights with red beams. Their faces are never clearly visible; they appear as silhouettes, backs, shoulders and caps.

Art style:
2D hand-drawn TV anime, digital ink and paint, cel-shaded characters over painted backgrounds. Match the clean flat look of Image 1. Not 3D, not CG, not photoreal, not a painterly illustration.
Line art: thin, clean, even-weight lines. Character outer contour about 2.5 px at 1080p, inner detail lines about 1.5 px, no brush taper, no sketchy double lines. Lines are never pure black: character lines are a deep plum-brown (#3B2A33), leaning toward deep navy (#1E2340) in this night light.
Color trace (iro-tore): inner lines of hair, highlight edges and shadow boundaries on skin and cloth are drawn in a darker tint of the neighboring fill color instead of the line color — orange hair uses burnt-sienna lines, skin uses rose-brown lines.
Shading: two-tone cel shading (base + one hard-edged shadow), one hard highlight shape on hair, no soft gradients on characters except a thin cool rim light and the moving red light. Shadows shift toward blue-violet. Backgrounds are painted with no outlines.

Animation timing:
24 fps output. Character animation is drawn on twos (12 drawings per second); small acting such as the shoulder drop is on threes. Holds are true holds: the drawing stays still and only hair and jacket secondary motion moves. Camera moves are smooth on ones, as if the background layer slides under the cel. No morphing between poses, no frame-blend ghosting, no AI interpolation smoothness. Walking has clear weight: heel strike, body drops slightly on contact, rises on passing.

Secondary motion (hair and cloth):
Akira's orange hair has two small buns at the back with loose curled ends. The curls bounce 1–2 frames after each footstep; the buns stay firm. When she stops, the curls settle in two small diminishing swings and rest. No floating hair, no constant wind waving. The wide sleeves of her jacket and the grey hanging straps swing with her arms and settle after she stops.

Color and light (one consistent night look for all four shots):
Deep night, dark blue and blue-grey, cold white street lamps, deep navy shadows, the same dark low-key lighting in every shot. No warm light anywhere. On the main street the only strong accent is red: the inspectors' red flashlights and the patrol car's rotating red light, always moving, sweeping across walls, cobblestones and Akira. The alley is the safe place: inside the alley there is no red light at all except the brief sweep across the alley mouth in Shot 3; the depth of the alley is only dark blue night haze.

Character: Akira (Image 1), a young woman newspaper reporter heading home from work. Orange hair with two small curled buns, red-framed glasses, light-blue shirt, oversized navy cropped jacket with wide sleeves and grey hanging straps, small camera on a lanyard, navy shorts, grey knee-high boots. One hand in her jacket pocket. Her face is never shown in any shot: she is always seen from behind or from the side with her face turned away or hidden in shadow — only her back, the back of her head, her shoulder, hands, feet and silhouette.

Screen direction: on the street the bar is to screen right and the town is to screen left. Akira faces right and moves left to right; the inspectors walking past her come the other way, right to left.

Shots:
[0-4s] Shot 1: [close tracking shot at waist height from the street side, tracking right] Deep night from the first frame. Akira, framed close from the side and slightly behind (chest to knees, face out of frame), walks right past the dark closed shutters; the camera tracks right with her at her speed so she stays in the same place in frame while the shutters slide left. Several inspectors walk past in the foreground in the opposite direction, right to left, very close to the camera: their dark grey coats, arms and red flashlights cross the frame out of focus, partly hiding Akira for a moment each time, then she is visible again, still walking. She does not look at them.
[4-8s] Shot 2: [locked-off wide shot down the street, Akira small in the left foreground, back to camera] Akira keeps walking down the street toward the grey building's corner. Inspectors are everywhere on the street: some walk toward her and pass her shoulder to shoulder going the other way, some cross the street, some stand under the lamps with red flashlights. At the far end a patrol car with a rotating red light turns into the street and drives slowly toward the camera, its red light sweeping across the shopfronts. As she reaches the narrow gap between the grey building and the bakery, she turns and slips into it without stopping.
[8-12s] Shot 3: [medium shot from inside the alley, behind her, looking out toward the main street, locked-off] Just inside the alley mouth, Akira stands with her back to the camera, pressed against the bakery's brick side wall in the shadow (looking out from inside the alley, the bakery wall is on the left of the frame and the grey building on the right), and carefully leans to look out at the main street. Through the bright opening the street lamps and the inspectors' silhouettes are visible. The patrol car drives past the alley mouth from left to right; its rotating red light sweeps into the alley entrance and across her back for a moment, then slides away. She stays perfectly still until it has passed, then slowly pulls back from the opening; her shoulders relax slightly.
[12-15s] Shot 4: [medium-wide shot inside the alley from Image 3, camera behind her, short follow then stop] Akira turns away from the street and walks deeper into the quiet, dark alley, close to the right wall. She stops at the teal wooden door on the right wall (the bar's door) and turns toward it; her shoulders drop as she exhales. Beyond her the alley continues, narrow and dark, fading into soft blue night haze — no red light, nothing glowing. The camera follows a few steps, then stops and holds.

Overall: keep Akira's hair, buns, glasses, jacket, straps, camera and boots identical in every shot and consistent with Image 1. Hard cuts on the timestamps, no dissolves. Stable lines, no line boiling, no flicker.

No subtitles. No text, letters or numbers anywhere; signs, notices and the chalkboard are blank. Normal eyes, no glowing eyes. Never show Akira's face. No civilians; the only other people are the patrol inspectors as dark silhouettes.

Audio again: footsteps, sirens, car engine, light wind and faint city hum only. No music, BGM, score, melody, instrumental or ambient pad. No voice, no humming.
```

## テスト1 v4（10/11のレビューを反映、5ショット・20秒）

参照画像はv2・v3と同じ（暁の三面図／パン屋の通り／月明かりの路地）。durationSec 20。

```
A 2D Japanese TV-anime sequence set entirely at deep night: in a town crowded with patrolling inspectors, Akira, a young woman reporter, walks home along a closed-shop street, weaving past inspectors coming the other way, slips into the narrow side alley next to the bakery, checks the main street from inside the alley as a patrol car passes, then walks a long way down the safe, dark alley to a plain door set deep inside it on the right wall. Five shots, hand-drawn cel animation. Her face is never shown.

Audio: natural sound and sirens only — her footsteps on stone, many inspectors' footsteps passing, a patrol siren wailing in the distance from the very first second and growing louder as the patrol car approaches, the car engine and tires passing the alley mouth in Shot 3, light wind. Inside the alley in Shots 4 and 5 the street noise and siren grow more and more muffled and distant. No music of any kind: no BGM, no score, no melody, no instrumental, no ambient pad, no synth. No dialogue, no narration, no humming, no voice.

Asset bindings:
- Image 1: Akira's three-view character sheet (front, side, back). Use it for her hair, glasses, outfit and body proportions. It is one person; ignore the white background and the sheet layout.
- Image 2: the bakery street, seen from the front. Use it only for the architecture and painted-background style: in the center the brick bakery (the hidden bar is inside this building); to its right the old woman's brick house with the green garage shutter, joined directly to the bakery with no gap; to its left the newer light-grey concrete apartment building; the only alley is the narrow gap between the grey building and the bakery. Do not copy its daylight, its lit shop window or its pedestrians. In this video it is deep night from the first frame to the last: every shop is closed, the bakery window is completely dark inside with no warm light, shutters are down, and only the street lamps are lit. There are no civilians at all.
- Image 3: the inside of that alley, seen from the street entrance, used for Shots 4 and 5. Do not mirror it. The right wall is the bakery/bar building; the teal wooden door on the right wall is the bar's door, and it is set deep inside the alley, far from the street. The left wall is the side of the newer grey building: plain light-grey concrete wall with pipes and utility boxes, no doors, no posters. There is no lamp over the bar's door. Beyond the door the alley continues, narrow and dark, fading into a soft dark night haze.

Patrol inspectors: every person on the street other than Akira is a patrol inspector in the same uniform — long dark grey uniform coat, dark grey peaked cap, plain red armband with no writing, handheld flashlight with a red beam. They walk naturally, alone or in pairs, at different speeds and in different directions. Their faces are never clearly visible; they appear as silhouettes, backs, shoulders and caps.

Patrol car: a plain dark navy sedan with a single rotating red light on the roof. Completely unmarked: no lettering, no words, no logos, no emblems, no numbers, no stripes anywhere on the car.

Art style:
2D hand-drawn TV anime, digital ink and paint, cel-shaded characters over painted backgrounds. Match the clean flat look of Image 1. Not 3D, not CG, not photoreal, not a painterly illustration.
Line art: thin, clean, even-weight lines. Character outer contour about 2.5 px at 1080p, inner detail lines about 1.5 px, no brush taper, no sketchy double lines. Lines are never pure black: character lines are a deep plum-brown (#3B2A33), leaning toward deep navy (#1E2340) in this night light.
Color trace (iro-tore): inner lines of hair, highlight edges and shadow boundaries on skin and cloth are drawn in a darker tint of the neighboring fill color instead of the line color — orange hair uses burnt-sienna lines, skin uses rose-brown lines.
Shading: two-tone cel shading (base + one hard-edged shadow), one hard highlight shape on hair, no soft gradients on characters except a thin cool rim light and the moving red light. Shadows shift toward blue-violet. Backgrounds are painted with no outlines.

Animation timing:
24 fps output. Character animation is drawn on twos (12 drawings per second); small acting such as the shoulder drop is on threes. Holds are true holds: the drawing stays still and only hair and jacket secondary motion moves. Camera moves are smooth on ones, as if the background layer slides under the cel. No morphing between poses, no frame-blend ghosting, no AI interpolation smoothness. Walking has clear weight: heel strike, body drops slightly on contact, rises on passing.

Secondary motion (hair and cloth):
Akira's orange hair has two small buns at the back with loose curled ends. The curls bounce 1–2 frames after each footstep; the buns stay firm. When she stops, the curls settle in two small diminishing swings and rest. No floating hair, no constant wind waving. The wide sleeves of her jacket and the grey hanging straps swing with her arms and settle after she stops.

Color and light (one consistent night look for all five shots):
Deep night, dark blue and blue-grey, cold white street lamps, deep navy shadows, the same dark low-key lighting in every shot. No warm light anywhere. On the main street the only strong accent is red: the inspectors' red flashlights and the patrol car's rotating red light, always moving, sweeping across walls, cobblestones and Akira. The alley is the safe place: inside the alley there is no red light at all except the brief sweep across the alley mouth in Shot 3; the depth of the alley is only dark blue night haze.

Character: Akira (Image 1), a young woman newspaper reporter heading home from work. Orange hair with two small curled buns, red-framed glasses, light-blue shirt, oversized navy cropped jacket with wide sleeves and grey hanging straps, small camera on a lanyard, navy shorts, grey knee-high boots. One hand in her jacket pocket. Her face is never shown in any shot: she is always seen from behind or from the side with her face turned away or hidden in shadow. She never turns her head back toward the camera.

Screen direction: on the street the bar is to screen right and the town is to screen left. Akira faces right and moves left to right; the inspectors walking past her come the other way, right to left.

Shots:
[0-4s] Shot 1: [close tracking shot at waist height from the street side, tracking right] Deep night from the first frame. Akira, framed close from the side and slightly behind (chest to knees, face out of frame), walks right past the dark closed shutters; the camera tracks right with her at her speed so she stays in the same place in frame while the shutters slide left. Several inspectors walk past in the foreground in the opposite direction, right to left, very close to the camera: their dark grey coats, plain red armbands and red flashlights cross the frame out of focus, partly hiding Akira for a moment each time, then she is visible again, still walking. She does not look at them.
[4-8s] Shot 2: [locked-off wide shot of the dark street in front of the closed bakery, slightly high angle] The bakery and every shop are dark and closed. The street is busy with uniformed inspectors walking naturally in both directions, alone and in pairs, some crossing, some standing under the lamps with red flashlights. Among them, Akira, small in frame, walks right along the sidewalk; two inspectors pass her shoulder to shoulder going the other way. At the far end the unmarked dark patrol car with its rotating red light turns into the street and drives slowly closer, the red light sweeping across the dark shopfronts. As she reaches the narrow gap between the grey building and the bakery, she turns and slips into it without stopping.
[8-12s] Shot 3: [medium shot from inside the alley, behind her, looking out toward the main street, locked-off] Just inside the alley mouth, Akira stands with her back to the camera, pressed against the bakery's brick side wall in the shadow (looking out from inside the alley, the bakery wall is on the left of the frame and the grey building on the right), and carefully leans to look out at the main street. Through the bright opening the street lamps and the inspectors' silhouettes are visible. The unmarked patrol car drives past the alley mouth; its rotating red light sweeps into the alley entrance and across her back for a moment, then slides away. She stays perfectly still until it has passed, then slowly pulls back from the opening.
[12-16s] Shot 4: [wide shot deep inside the alley looking back toward the street entrance, locked-off] A long, narrow, dark alley. Far away at the end of the frame the bright street entrance is a small rectangle of lamplight with tiny inspector silhouettes passing across it. Akira walks toward the camera from the entrance end, but small and in deep shadow so her face is an unreadable dark silhouette; she keeps her head lowered and walks quickly and quietly along the right side, growing larger as she comes down the alley, then passes out of frame on the left of the camera. The street noise fades behind her.
[16-20s] Shot 5: [medium-wide shot inside the alley from Image 3, camera behind her] Deep inside the alley, far from the street. Akira, seen from behind, walks the last few steps and stops in front of the teal wooden door on the right wall (the bar's door), turning her body toward the door without looking back; her shoulders drop as she exhales. Beyond her the alley continues, narrow and dark, fading into soft blue night haze — no red light, nothing glowing. The camera holds still.

Overall: keep Akira's hair, buns, glasses, jacket, straps, camera and boots identical in every shot and consistent with Image 1. Hard cuts on the timestamps, no dissolves. Stable lines, no line boiling, no flicker.

No subtitles. No text, letters, words, logos or numbers anywhere: the patrol car, the armbands, signs, notices and the chalkboard are all completely blank. Normal eyes, no glowing eyes. Never show Akira's face. No civilians; the only other people are the patrol inspectors.

Audio again: footsteps, sirens, car engine, light wind and faint city hum only. No music, BGM, score, melody, instrumental or ambient pad. No voice, no humming.
```

## テスト3｜扉と投函、入口の内側（S1-10, S1-11, S2-01〜02, S2-04〜05）15秒

テスト1の続き。暁が扉の前で合言葉を書いて投函→内側で紙が落ちて鈴が鳴る→奥からあかねが小走りで来てフードをかぶる。あかねの顔はまだ見せない（字コンテどおり）。ピアノは編集で載せるので、生成では音楽なし。

| Image | ファイル | 役割 |
|---|---|---|
| 1 | リファレンス/akira_moto_260909.png | 暁の三面図 |
| 2 | リファレンス/akane_moto_260909.png | あかねの三面図 |
| 3 | リファレンス/月明かりの路地.png | 路地と月灯りの扉（外） |
| 4 | リファレンス/月明かり店内.png | 店内（入口の内側から見える奥の暖色の光の参考） |

```
A 2D Japanese TV-anime sequence at deep night: at the plain door deep inside a dark alley, Akira writes a password in a small notebook, tears out the page and slips it through the door's mail slot; inside, in the dark entrance of a hidden bar, the folded note drops into a box and a tiny bell rings; then Akane hurries in from the warm bar to the door and pulls up her hood. Four shots, hand-drawn cel animation. Neither girl's face is shown.

Audio: natural sound only — a pen scratching on paper, a page torn out, paper sliding through a slot, a tiny brass bell ringing once and fading, light quick footsteps on a wooden floor, the rustle of fabric. Outside, a faint distant siren and wind; inside, a soft muffled murmur from the bar behind the wall with no intelligible words. No music of any kind: no BGM, no score, no melody, no piano, no instrumental, no ambient pad, no synth. No dialogue, no narration, no humming, no voice.

Asset bindings:
- Image 1: Akira's three-view character sheet. Use it for her hands, sleeves, jacket and hair. One person; ignore the white background and sheet layout.
- Image 2: Akane's three-view character sheet. Use it for her pink hair, hair clips, uniform, legs and boots. One person; ignore the white background and sheet layout.
- Image 3: the dark brick alley; the teal wooden door on the right wall is the bar's door. Use it for Shots 1 and 2. The door has a narrow brass mail slot at chest height. No lamp over the door. Wall notices are blank.
- Image 4: the bar interior. Use it only as the reference for the warm honey-colored light, wood and brick of the bar that glows beyond the dark entrance in Shots 3 and 4.

The bar's entrance (Shots 3 and 4): a small, dark vestibule just inside the alley door. The door is on the left of the frame; the bar is off to the right, and its warm honey-colored light spills a little across the wooden floor from the right. On the inside of the door: the narrow mail slot, a tiny brass bell hanging just above it, and a small wooden box below it that catches the notes. A thin line of cold blue street light comes through the slot.

Art style:
2D hand-drawn TV anime, digital ink and paint, cel-shaded characters over painted backgrounds. Match the clean flat look of Images 1 and 2. Not 3D, not CG, not photoreal, not a painterly illustration.
Line art: thin, clean, even-weight lines. Character outer contour about 2.5 px at 1080p, inner detail lines about 1.5 px, no brush taper, no sketchy double lines. Lines are never pure black: character lines are a deep plum-brown (#3B2A33), leaning toward deep navy (#1E2340) in the cold night light and toward warm brown in the bar's light.
Color trace (iro-tore): inner lines of hair, highlight edges and shadow boundaries on skin and cloth are drawn in a darker tint of the neighboring fill color instead of the line color — orange hair uses burnt-sienna lines, pink hair uses rose lines, skin uses rose-brown lines.
Shading: two-tone cel shading (base + one hard-edged shadow), one hard highlight shape on hair, no soft gradients on characters except a thin rim light. Shadows shift toward blue-violet outside and warm violet-brown inside. Backgrounds are painted with no outlines.

Animation timing:
24 fps output. Character animation is drawn on twos (12 drawings per second); small hand acting is on threes. Holds are true holds: the drawing stays still and only hair, cloth, paper and the bell move. Camera moves are smooth on ones. No morphing between poses, no frame-blend ghosting, no AI interpolation smoothness.

Secondary motion:
Paper has real weight: the page bends as it is torn, the folded note is stiff, it tips and drops straight into the box with a small bounce. The tiny bell swings on its hook with three diminishing swings and stops. Akane's long pink hair trails one or two frames behind her quick steps and settles when she stops; the hood fabric folds naturally as she pulls it up. No floating hair, no wind inside.

Color and light:
Shots 1 and 2 (alley): cold night — dark blue and blue-grey, deep navy shadows, no warm light, no red light. Shots 3 and 4 (entrance): mostly dark, with the first warm color of the night — soft honey-colored light from the bar on the right, against the cold blue line of light from the slot. Never bright.

Characters:
- Akira (Image 1): a young woman reporter. Only her hands, sleeves and the front of her navy jacket are seen; no face.
- Akane (Image 2): a young woman, the bar's gatekeeper. Long light-pink hair with hair clips, white and pale-grey uniform with an orange tie, pleated white skirt, dark tights, black ankle boots. Over her uniform she wears a dark navy hooded outer jacket for door duty. Her face is not shown in this video: only her boots, legs, back, hands and the back of her head.

Screen direction: inside the bar, the alley door is on screen left and the bar is on screen right; Akane moves right to left toward the door.

Shots:
[0-3s] Shot 1: [insert close-up of hands in front of the door, locked-off] In the dark alley in front of the teal door, Akira's hands hold a small notebook and write a few quick strokes with a pen. The page shows only abstract pen strokes, no readable letters.
[3-6s] Shot 2: [insert close-up of hands at the door, locked-off] She tears the page out, folds it small twice, and slides it into the narrow brass mail slot of the door until it disappears.
[6-10s] Shot 3: [close shot inside the dark entrance, the same mail slot seen from the inside, locked-off] Match cut to the inside of the door: the folded note pushes through the slot and drops into the small wooden box below. The tiny brass bell above the slot rings once and swings, then slowly settles. The vestibule is empty and dark; warm honey light from the bar spills across the floor from the right. Hold until the bell is still.
[10-15s] Shot 4: [low shot at floor level in the entrance, locked-off, then the same angle tilting up slightly] From the warm light on the right, Akane's black ankle boots and dark-tighted legs hurry in with quick light steps toward the door on the left; her white pleated skirt hem bounces. She stops by the door, and seen from behind she pulls the hood of her dark navy jacket up over her pink hair with both hands, her face never visible.

Overall: keep each character's hair, clothes and colors identical in every shot and consistent with Images 1 and 2. Hard cuts on the timestamps, no dissolves. Stable lines, no line boiling, no flicker.

No subtitles. No text, letters, words, logos or numbers anywhere; the notebook page, the door and the walls are blank. Normal eyes, no glowing eyes. No other people.

Audio again: pen, paper, bell, footsteps, fabric, faint siren and wind outside, muffled wordless murmur inside. No music, BGM, score, melody, piano, instrumental or ambient pad. No voice, no humming.
```

## テスト3 v2（10/11のレビューを反映、5ショット・17秒）

参照画像はテスト3と同じ。変更：暁が潜んでいる体のカットを足す／入口の内側は暗く、店の明るさはまだ見せない／扉はあかねの背丈に合った普通の大きさ／フードはかぶる。

```
A 2D Japanese TV-anime sequence at deep night: deep inside a dark alley, Akira reaches the bar's plain door, crouches low against the wall like someone hiding, secretly writes a password in a small notebook, tears out the page and slips it through the door's mail slot; inside, in the pitch-dark entrance of a hidden bar, the folded note drops into a box and a tiny bell rings; then Akane hurries to the door in the dark and pulls her hood up. Five shots, hand-drawn cel animation. Neither girl's face is shown.

Audio: natural sound only — her careful footsteps, the rustle of her jacket as she crouches, a pen scratching quickly on paper, a page torn out quietly, paper sliding through a slot, a tiny brass bell ringing once and fading, light quick footsteps on a wooden floor, the rustle of fabric. Outside, a faint distant siren and wind; inside, a soft muffled murmur from behind a wall with no intelligible words. No music of any kind: no BGM, no score, no melody, no piano, no instrumental, no ambient pad, no synth. No dialogue, no narration, no humming, no voice.

Asset bindings:
- Image 1: Akira's three-view character sheet. Use it for her hair, glasses, jacket, straps, camera, shorts, boots and body proportions. One person; ignore the white background and sheet layout.
- Image 2: Akane's three-view character sheet. Use it for her pink hair, hair clips, uniform, legs and boots. One person; ignore the white background and sheet layout.
- Image 3: the dark brick alley; the teal wooden door on the right wall is the bar's door. Use it for Shots 1 to 3. The door is an ordinary single door, only a little taller than a person, with a narrow brass mail slot at chest height. No lamp over the door. Wall notices are blank.
- Image 4: the bar interior. Use it only for the wood paneling and the color of the warm light; in this video the bar itself is never shown and its light is only a faint glow.

The bar's entrance (Shots 4 and 5): a small, very dark vestibule just inside the alley door, lit almost only by the thin line of cold blue street light coming through the mail slot. The door is on the left of the frame; the bar is off to the right and is never seen — only a faint, dim warm glow touches the edge of the floor on the far right. On the inside of the door: the narrow mail slot, a tiny brass bell hanging just above it, and a small wooden box below it. The door is an ordinary single door, in normal proportion to Akane: its top is only about a head above her hood.

Art style:
2D hand-drawn TV anime, digital ink and paint, cel-shaded characters over painted backgrounds. Match the clean flat look of Images 1 and 2. Not 3D, not CG, not photoreal, not a painterly illustration.
Line art: thin, clean, even-weight lines. Character outer contour about 2.5 px at 1080p, inner detail lines about 1.5 px, no brush taper, no sketchy double lines. Lines are never pure black: character lines are a deep plum-brown (#3B2A33), leaning toward deep navy (#1E2340) in this dark light.
Color trace (iro-tore): inner lines of hair, highlight edges and shadow boundaries on skin and cloth are drawn in a darker tint of the neighboring fill color instead of the line color — orange hair uses burnt-sienna lines, pink hair uses rose lines, skin uses rose-brown lines.
Shading: two-tone cel shading (base + one hard-edged shadow), one hard highlight shape on hair, no soft gradients on characters except a thin rim light. Shadows shift toward blue-violet. Backgrounds are painted with no outlines.

Animation timing:
24 fps output. Character animation is drawn on twos (12 drawings per second); small hand acting is on threes. Holds are true holds: the drawing stays still and only hair, cloth, paper and the bell move. Camera moves are smooth on ones. No morphing between poses, no frame-blend ghosting, no AI interpolation smoothness.

Secondary motion:
Akira's curled hair ends sway slightly as she crouches and settle. Paper has real weight: the page bends as it is torn, the folded note is stiff, it tips and drops straight into the box with a small bounce. The tiny bell swings on its hook with three diminishing swings and stops. Akane's long pink hair trails one or two frames behind her quick steps and settles; the hood fabric folds naturally as she pulls it up over her head. No floating hair, no wind inside.

Color and light:
The whole video is dark, low-key night. Shots 1 to 3 (alley): dark blue and blue-grey, deep navy shadows, no warm light, no red light. Shots 4 and 5 (entrance): almost black, with the cold blue line from the slot as the main light and only a faint, dim warm glow at the far right edge. The bar's brightness is not revealed yet.

Characters:
- Akira (Image 1): a young woman reporter. Orange hair with two small curled buns, red-framed glasses, light-blue shirt, oversized navy cropped jacket with wide sleeves and grey hanging straps, small camera on a lanyard, navy shorts, grey knee-high boots. She behaves like someone hiding: low, compact, quiet, quick. Her face is never shown: she is seen from behind or from the side with her face turned away toward the alley entrance and hidden in shadow.
- Akane (Image 2): a young woman, the bar's gatekeeper. Long light-pink hair with hair clips, white and pale-grey uniform with an orange tie, pleated white skirt, plain dark tights with no pattern, black ankle boots. Over her uniform she wears a dark navy hooded outer jacket for door duty. Her face is not shown in this video.

Shots:
[0-4s] Shot 1: [medium-wide shot in the alley from further down the alley, behind Akira, locked-off] Akira walks quickly to the teal door on the right wall, then drops into a low crouch beside it, pressing her shoulder and back against the brick wall next to the door. She turns her head away from the camera to glance back toward the alley entrance, holds still for a beat, then slips a small notebook and a pen out of her jacket pocket.
[4-7s] Shot 2: [medium close-up over her shoulder, crouched at the door, locked-off] Still crouched low and hunched, Akira presses the small notebook against the door below the mail slot and writes a few quick strokes, her other hand and her body shielding the page; her head stays turned slightly toward the alley entrance, listening. The page shows only a few loose pen scribbles, no letters and no words.
[7-10s] Shot 3: [insert close-up of hands at the door, locked-off] She tears the page out quietly, folds it small twice, slides it into the narrow brass mail slot, and quickly pulls her hand back out of frame.
[10-13s] Shot 4: [close shot inside the pitch-dark entrance, the same mail slot seen from the inside, locked-off] Match cut to the inside of the door: the folded note pushes through the slot and drops into the small wooden box below. The tiny brass bell above the slot rings once and swings, then slowly settles. Almost black; only the thin blue line from the slot lights the note and the bell.
[13-17s] Shot 5: [medium shot in the dark entrance at hip height, locked-off] From the dim right side, Akane hurries in with quick light steps to the ordinary-sized door on the left and stops, seen from behind, her pink hair catching a little of the blue slot light. She lifts the hood of her dark navy jacket with both hands and pulls it up over her head until her pink hair is mostly hidden. Her face is never visible.

Overall: keep each character's hair, clothes and colors identical in every shot and consistent with Images 1 and 2. Keep the door the same ordinary size inside and outside. Hard cuts on the timestamps, no dissolves. Stable lines, no line boiling, no flicker.

No subtitles. No text, letters, words, logos or numbers anywhere; the notebook page, the door and the walls show no writing. Normal eyes, no glowing eyes. No other people.

Audio again: footsteps, fabric, pen, paper, bell, faint siren and wind outside, muffled wordless murmur inside. No music, BGM, score, melody, piano, instrumental or ambient pad. No voice, no humming.
```

## テスト4｜あかねの初登場（S2-06〜S2-09）15秒・Runway

Runway（Seedance 2.5、Unlimited）で生成。あかねの顔が初めて出るカット。台詞は声つきで生成（口の動きの確認用）。

| Image | ファイル | 役割 |
|---|---|---|
| 1 | リファレンス/akane_moto_260909.png | あかねの三面図 |
| 2 | リファレンス/akira_moto_260909.png | 暁の三面図 |
| 3 | リファレンス/月明かりの路地.png | 路地と月灯りの扉（外） |

```
A 2D Japanese TV-anime sequence at deep night: in the pitch-dark entrance of a hidden bar, Akane, the gatekeeper, checks a password note, then opens the door just a crack; through the narrow gap her face appears for the first time, and she glares at Akira waiting outside in the dark alley. Four shots, hand-drawn cel animation, dialogue in Japanese.

Audio: Akane's voice, the rustle of paper, the click of a door handle, a small creak of the door, light wind in the alley, a faint distant siren. No music of any kind: no BGM, no score, no melody, no piano, no instrumental, no ambient pad, no synth.

Asset bindings:
- Image 1: Akane's three-view character sheet (front, side, back). Use it for her face, eyes, long light-pink hair, hair clips, uniform and proportions. One person; ignore the white background and sheet layout.
- Image 2: Akira's three-view character sheet. Use it for her back, orange hair with two small buns, navy jacket and straps. One person; ignore the white background and sheet layout.
- Image 3: the dark brick alley; the teal wooden door on the right wall is the bar's door, an ordinary single door with a narrow brass mail slot. Use it for Shots 3 and 4. No lamp over the door. Wall notices are blank.

Akane's look in this video: over her uniform she wears a dark navy hooded outer jacket with the hood up; her long pink hair spills out from under the hood at the front. Her face (Image 1): large blue-violet eyes, small nose and mouth, pink hair with a side part and hair clips.

Inside the entrance (Shots 1 and 2): a small, very dark vestibule, lit almost only by the thin cold blue line of street light from the mail slot, with a faint dim warm glow from the right. The door is on the left of the frame.

Art style:
2D hand-drawn TV anime, digital ink and paint, cel-shaded characters over painted backgrounds. Match the clean flat look of Images 1 and 2. Not 3D, not CG, not photoreal, not a painterly illustration.
Line art: thin, clean, even-weight lines. Character outer contour about 2.5 px at 1080p, inner detail lines about 1.5 px, no brush taper, no sketchy double lines. Lines are never pure black: character lines are a deep plum-brown (#3B2A33), leaning toward deep navy (#1E2340) in the cold light.
Color trace (iro-tore): inner lines of hair, highlight edges and shadow boundaries on skin and cloth are drawn in a darker tint of the neighboring fill color instead of the line color — pink hair uses rose lines, orange hair uses burnt-sienna lines, skin uses rose-brown lines.
Shading: two-tone cel shading (base + one hard-edged shadow), one hard highlight shape on hair, no soft gradients on characters except a thin rim light. Shadows shift toward blue-violet. Backgrounds are painted with no outlines.

Animation timing:
24 fps output. Character animation is drawn on twos (12 drawings per second); eye and mouth acting on threes. Holds are true holds: the drawing stays still and only hair, cloth and paper move. Mouths move only while speaking; a closed mouth stays closed. Camera moves are smooth on ones. No morphing between poses, no frame-blend ghosting, no AI interpolation smoothness.

Secondary motion:
The strands of pink hair that spill from Akane's hood sway a little when she moves her head and settle. Paper unfolds with real weight. Akira's curled hair ends move only slightly in the alley wind. No floating hair.

Color and light:
Dark, low-key night throughout. Inside: almost black with the cold blue slot line and a faint warm glow from the right. Outside: dark blue and blue-grey alley. When the door opens, only one thin vertical strip of dim warm light falls through the gap and across Akane's face. Never bright.

Screen direction: in the alley the door is on screen right; Akane in the gap looks to screen left; Akira stands on screen left facing right. Akira's face is never shown.

Shots:
[0-3s] Shot 1: [insert close-up of hands in the dark entrance, locked-off] Akane's fingers unfold the small folded note in the thin blue light from the slot. The page is held at an angle so its content cannot be seen. Akane's line (quiet, to herself, off-screen): 「……正解」
[3-6s] Shot 2: [medium close shot inside, from behind her shoulder, locked-off] Hood up, Akane leans close against the edge of the door in the dark, her face hidden by the hood's shadow, and closes her hand on the door handle. A small click.
[6-10s] Shot 3: [close shot from the alley side, framed through the door gap, very slow push-in] The teal door opens just a few centimeters. A thin vertical strip of dim warm light appears, and in it, for the first time, Akane's face: one large blue-violet eye and part of her face under the hood, looking left at someone outside. She blinks once, calm and wary.
[10-15s] Shot 4: [medium shot from the alley, over Akira's shoulder, locked-off] In the left foreground, Akira's back and the back of her orange head with two small buns, dark and out of focus, facing right. On the right, the door is still open only a narrow crack, its width unchanged; in the gap, Akane looks up at Akira with half-closed, unimpressed eyes. Akane's line (flat, scolding): 「鼻歌。また外で歌ってきたでしょ」 Akira does not turn around.

Overall: keep Akane's face, hair, hood and colors identical in every shot and consistent with Image 1; keep Akira consistent with Image 2. The door stays an ordinary size and only opens a crack. Hard cuts on the timestamps, no dissolves. Stable lines, no line boiling, no flicker.

No subtitles. No text, letters, words, logos or numbers anywhere; the note, the door and the walls show no writing. Normal eyes, no glowing eyes. No other people.

Audio again: only Akane's voice, paper, door handle, door creak, light wind and a faint distant siren. No music, BGM, score, melody, piano, instrumental or ambient pad.
```


## テスト4 v2（照明の修正）15秒・Hamster

テスト4（Runway）から照明だけ変更：入口の内側にあかねの背後から店の暖色、扉の隙間から店の光がはっきり漏れて、あかねの輪郭と暁の肩に落ちる。構図・芝居・台詞はそのまま。

```
A 2D Japanese TV-anime sequence at deep night: in the dim, warm-lit entrance of a hidden bar, Akane, the gatekeeper, checks a password note, then opens the door just a crack; through the narrow gap her face appears for the first time, and she glares at Akira waiting outside in the dark alley. Four shots, hand-drawn cel animation, dialogue in Japanese.

Audio: Akane's voice, the rustle of paper, the click of a door handle, a small creak of the door, light wind in the alley, a faint distant siren. No music of any kind: no BGM, no score, no melody, no piano, no instrumental, no ambient pad, no synth.

Asset bindings:
- Image 1: Akane's three-view character sheet (front, side, back). Use it for her face, eyes, long light-pink hair, hair clips, uniform and proportions. One person; ignore the white background and sheet layout.
- Image 2: Akira's three-view character sheet. Use it for her back, orange hair with two small buns, navy jacket and straps. One person; ignore the white background and sheet layout.
- Image 3: the dark brick alley; the teal wooden door on the right wall is the bar's door, an ordinary single door with a narrow brass mail slot. Use it for Shots 3 and 4. No lamp over the door. Wall notices are blank.

Akane's look in this video: over her uniform she wears a dark navy hooded outer jacket with the hood up; her long pink hair spills out from under the hood at the front. Her face (Image 1): large blue-violet eyes, small nose and mouth, pink hair with a side part and hair clips.

Inside the entrance (Shots 1 and 2): a small vestibule between the alley door and the bar. Warm honey-colored light from the bar behind Akane fills it softly from the right and from behind her: it lights her hands, the paper, the rim of her hood and her pink hair, and the inside of the door. The thin cold blue line from the mail slot stays as a contrast. Moody and low-key, but clearly visible, not black. The door is on the left of the frame.

Art style:
2D hand-drawn TV anime, digital ink and paint, cel-shaded characters over painted backgrounds. Match the clean flat look of Images 1 and 2. Not 3D, not CG, not photoreal, not a painterly illustration.
Line art: thin, clean, even-weight lines. Character outer contour about 2.5 px at 1080p, inner detail lines about 1.5 px, no brush taper, no sketchy double lines. Lines are never pure black: character lines are a deep plum-brown (#3B2A33), leaning toward deep navy (#1E2340) in the cold light.
Color trace (iro-tore): inner lines of hair, highlight edges and shadow boundaries on skin and cloth are drawn in a darker tint of the neighboring fill color instead of the line color — pink hair uses rose lines, orange hair uses burnt-sienna lines, skin uses rose-brown lines.
Shading: two-tone cel shading (base + one hard-edged shadow), one hard highlight shape on hair, no soft gradients on characters except a thin rim light. Shadows shift toward blue-violet. Backgrounds are painted with no outlines.

Animation timing:
24 fps output. Character animation is drawn on twos (12 drawings per second); eye and mouth acting on threes. Holds are true holds: the drawing stays still and only hair, cloth and paper move. Mouths move only while speaking; a closed mouth stays closed. Camera moves are smooth on ones. No morphing between poses, no frame-blend ghosting, no AI interpolation smoothness.

Secondary motion:
The strands of pink hair that spill from Akane's hood sway a little when she moves her head and settle. Paper unfolds with real weight. Akira's curled hair ends move only slightly in the alley wind. No floating hair.

Color and light:
Inside: warm honey-colored bar light from behind Akane, soft and moody, against the cold blue line from the slot. Outside: dark blue and blue-grey alley. When the door opens a crack, the bar's warm light clearly spills out through the gap: a bright warm vertical strip that rims Akane's hood and hair from behind, lights her face with a warm glow, and falls as a warm line across the alley's stones and onto Akira's shoulder and hair in the foreground, in strong contrast with the cold blue night.

Screen direction: in the alley the door is on screen right; Akane in the gap looks to screen left; Akira stands on screen left facing right. Akira's face is never shown.

Shots:
[0-3s] Shot 1: [insert close-up of hands in the entrance, locked-off] Akane's fingers unfold the small folded note in the warm bar light, with the thin blue line from the slot behind it. The page is held at an angle so its content cannot be seen. Akane's line (quiet, to herself, off-screen): 「……正解」
[3-6s] Shot 2: [medium close shot inside, from behind her shoulder, locked-off] Hood up, Akane leans close against the edge of the door, the warm bar light behind her rimming her hood, her face hidden by the hood's shadow, and closes her hand on the door handle. A small click.
[6-10s] Shot 3: [close shot from the alley side, framed through the door gap, very slow push-in] The teal door opens just a few centimeters. A bright vertical strip of warm bar light spills out, and in it, for the first time, Akane's face: one large blue-violet eye and part of her face under the hood, looking left at someone outside. She blinks once, calm and wary.
[10-15s] Shot 4: [medium shot from the alley, over Akira's shoulder, locked-off] In the left foreground, Akira's back and the back of her orange head with two small buns, dark and out of focus, facing right. On the right, the door is still open only a narrow crack, its width unchanged; in the gap, backlit and rimmed by the bright warm light from the bar, Akane looks up at Akira with half-closed, unimpressed eyes; the warm light from the gap falls across Akira's shoulder and the back of her hair. Akane's line (flat, scolding): 「鼻歌。また外で歌ってきたでしょ」 Akira does not turn around.

Overall: keep Akane's face, hair, hood and colors identical in every shot and consistent with Image 1; keep Akira consistent with Image 2. The door stays an ordinary size and only opens a crack. Hard cuts on the timestamps, no dissolves. Stable lines, no line boiling, no flicker.

No subtitles. No text, letters, words, logos or numbers anywhere; the note, the door and the walls show no writing. Normal eyes, no glowing eyes. No other people.

Audio again: only Akane's voice, paper, door handle, door creak, light wind and a faint distant siren. No music, BGM, score, melody, piano, instrumental or ambient pad.
```

## テスト5｜扉ごしのやりとり〜どうぞ（S2-09②〜S2-11）15秒・Runway

テスト4の続き。暁「あれくらい平気だろ」〜SDの掛け合い〜「……どうぞ、お入りください」で暁が店に入る。台詞は声つき。参照：Image 1 あかね／2 暁／3 路地／4 店内。

```
A 2D Japanese TV-anime sequence at deep night, outside and just inside the door of a hidden bar: Akane, the gatekeeper, scolds Akira through a narrow crack in the door, they bicker in a quick super-deformed gag, then Akane opens the door and lets Akira in. Five shots, hand-drawn cel animation, dialogue in Japanese.

Audio: the two girls' voices, light wind in the alley, the creak of the door opening wider, Akira's footsteps on wood, a soft muffled murmur from the bar with no intelligible words. Small comic sound effects only in the super-deformed shots (a light pop). No music of any kind: no BGM, no score, no melody, no piano, no instrumental, no ambient pad, no synth.

Asset bindings:
- Image 1: Akane's three-view character sheet (front, side, back). Use it for her face, eyes, long light-pink hair, hair clips, uniform and proportions. One person; ignore the white background and sheet layout.
- Image 2: Akira's three-view character sheet. Use it for her orange hair with two small curled buns, red-framed glasses, navy jacket with straps, camera and proportions. One person; ignore the white background and sheet layout.
- Image 3: the dark brick alley; the teal wooden door on the right wall is the bar's door, an ordinary single door with a narrow brass mail slot. Use it for Shot 1. No lamp over the door. Wall notices are blank.
- Image 4: the bar interior. Use it for the warm honey-colored light and the wood of the bar seen behind Akane in Shots 4 and 5.

Characters:
- Akane (Image 1): the bar's gatekeeper, a young woman. Long light-pink hair with hair clips, large blue-violet eyes. Over her uniform she wears a dark navy hooded outer jacket with the hood up; her pink hair spills out at the front. Serious and strict at the door.
- Akira (Image 2): a young woman newspaper reporter, a regular. Relaxed and cheeky, one hand in her pocket. Her face stays hidden in the normal-proportion shots (seen from behind or in shadow); only in the super-deformed shot is her face shown.

Inside the entrance: a small vestibule between the alley door and the bar, softly filled with warm honey-colored light from the bar on the right. The door is on the left of the frame.

Art style:
2D hand-drawn TV anime, digital ink and paint, cel-shaded characters over painted backgrounds. Match the clean flat look of Images 1 and 2. Not 3D, not CG, not photoreal, not a painterly illustration.
Line art: thin, clean, even-weight lines. Character outer contour about 2.5 px at 1080p, inner detail lines about 1.5 px, no brush taper, no sketchy double lines. Lines are never pure black: character lines are a deep plum-brown (#3B2A33), leaning toward deep navy (#1E2340) in the cold light and warm brown in the bar light.
Color trace (iro-tore): inner lines of hair, highlight edges and shadow boundaries on skin and cloth are drawn in a darker tint of the neighboring fill color instead of the line color — pink hair uses rose lines, orange hair uses burnt-sienna lines, skin uses rose-brown lines.
Shading: two-tone cel shading (base + one hard-edged shadow), one hard highlight shape on hair, no soft gradients on characters except a thin rim light. Shadows shift toward blue-violet. Backgrounds are painted with no outlines.

Animation timing:
24 fps output. Character animation is drawn on twos (12 drawings per second); eye and mouth acting on threes. Holds are true holds: the drawing stays still and only hair and cloth move. Mouths move only while that character speaks; a closed mouth stays closed. Camera moves are smooth on ones. No morphing between poses, no frame-blend ghosting, no AI interpolation smoothness. The super-deformed shots are snappy: quick pose changes on twos with a held final pose.

Secondary motion:
Akane's pink hair strands at the front of the hood sway a little when she turns her head and settle. Akira's curled hair ends bounce slightly when she shrugs and when she walks. The hood fabric folds naturally. No floating hair.

Color and light:
Outside: dark blue and blue-grey alley, with the bar's warm light spilling through the door gap onto Akane's face, the stones and Akira's shoulder. Inside: warm honey-colored bar light behind Akane, moody but clearly visible. The super-deformed shots use a plain pale pastel color background instead of the scene.

Screen direction: outside, the door is on screen right and Akane in the gap looks left; Akira stands on screen left facing right. Inside, the door is on screen left and the bar is on screen right; Akira enters from the left and passes to the right.

Shots:
[0-4s] Shot 1: [medium shot from the alley, over Akira's shoulder, locked-off] In the left foreground, Akira's back and the back of her orange head with two small buns, facing right; on the right, the door open only a narrow crack, Akane in the gap lit by the warm light from inside, looking at Akira with half-closed, unimpressed eyes. Akira shrugs her shoulders loosely. Akira's line (casual, carefree): 「あれくらい平気だろ」 Akane's line (flat, cold): 「捕まっても知りませんからね」
[4-6s] Shot 2: [super-deformed gag shot, plain pale pastel background] Super-deformed two-head-tall Akira (orange hair, red glasses) grins lazily and waves one hand. Akira's line (lazy, teasing): 「そんときゃ差し入れ頼むわ」
[6-8s] Shot 3: [super-deformed gag shot, plain pale pastel background] Super-deformed two-head-tall Akane in her hood puffs her cheeks and turns her face sharply away with a small pop. Akane's line (short, sulky): 「嫌です」
[8-12s] Shot 4: [medium shot inside the entrance, from behind Akane's right shoulder, locked-off] Normal proportions again. In the right foreground, Akane's hooded back and the edge of her profile, warm bar light on her. On the left she pulls the door open just wide enough for one person; outside in the dark alley stands Akira as a dark silhouette. Akane's line (formal, a little reluctant): 「……どうぞ、お入りください」
[12-15s] Shot 5: [same angle, locked-off; the camera stays on Akane] Akira, her face in shadow, steps in through the door and walks past in front of Akane from left to right and out of frame on the right, toward the bar. Akane stays holding the door, still looking out into the alley.

Overall: keep both characters' faces, hair, clothes and colors consistent with Images 1 and 2 in every normal-proportion shot. The door is an ordinary single door. Hard cuts on the timestamps, no dissolves. Stable lines, no line boiling, no flicker.

No subtitles. No text, letters, words, logos or numbers anywhere; no speech bubbles or onomatopoeia text in the super-deformed shots. Normal eyes, no glowing eyes. No other people.

Audio again: only the two girls' voices, wind, door creak, footsteps, a light comic pop, a muffled wordless murmur. No music, BGM, score, melody, piano, instrumental or ambient pad.
```


## テスト4 v3（v2の照明＋Runway版のカメラ位置）15秒・Hamster

ショット3は扉の隙間の超寄り（隙間が画面中央、右端にレンガ）、ショット4は暁の頭と肩を左半分に大きく、扉をすぐ前に置く。貼り紙が画面に入らないよう指定。

```
A 2D Japanese TV-anime sequence at deep night: in the dim, warm-lit entrance of a hidden bar, Akane, the gatekeeper, checks a password note, then opens the door just a crack; through the narrow gap her face appears for the first time, and she glares at Akira waiting outside in the dark alley. Four shots, hand-drawn cel animation, dialogue in Japanese.

Audio: Akane's voice, the rustle of paper, the click of a door handle, a small creak of the door, light wind in the alley, a faint distant siren. No music of any kind: no BGM, no score, no melody, no piano, no instrumental, no ambient pad, no synth.

Asset bindings:
- Image 1: Akane's three-view character sheet (front, side, back). Use it for her face, eyes, long light-pink hair, hair clips, uniform and proportions. One person; ignore the white background and sheet layout.
- Image 2: Akira's three-view character sheet. Use it for her back, orange hair with two small buns, navy jacket and straps. One person; ignore the white background and sheet layout.
- Image 3: the dark brick alley; the teal wooden door on the right wall is the bar's door, an ordinary single door with a narrow brass mail slot. Use it for Shots 3 and 4. No lamp over the door. Wall notices are blank.

Akane's look in this video: over her uniform she wears a dark navy hooded outer jacket with the hood up in every shot; her long pink hair spills out from under the hood at the front. Her face (Image 1): large blue-violet eyes, small nose and mouth, pink hair with a side part and hair clips.

Inside the entrance (Shots 1 and 2): a small vestibule between the alley door and the bar. Warm honey-colored light from the bar behind Akane fills it softly from the right and from behind her: it lights her hands, the paper, the rim of her hood and her pink hair, and the inside of the door. The thin cold blue line from the mail slot stays as a contrast. Moody and low-key, but clearly visible, not black. The door is on the left of the frame.

Art style:
2D hand-drawn TV anime, digital ink and paint, cel-shaded characters over painted backgrounds. Match the clean flat look of Images 1 and 2. Not 3D, not CG, not photoreal, not a painterly illustration.
Line art: thin, clean, even-weight lines. Character outer contour about 2.5 px at 1080p, inner detail lines about 1.5 px, no brush taper, no sketchy double lines. Lines are never pure black: character lines are a deep plum-brown (#3B2A33), leaning toward deep navy (#1E2340) in the cold light.
Color trace (iro-tore): inner lines of hair, highlight edges and shadow boundaries on skin and cloth are drawn in a darker tint of the neighboring fill color instead of the line color — pink hair uses rose lines, orange hair uses burnt-sienna lines, skin uses rose-brown lines.
Shading: two-tone cel shading (base + one hard-edged shadow), one hard highlight shape on hair, no soft gradients on characters except a thin rim light. Shadows shift toward blue-violet. Backgrounds are painted with no outlines.

Animation timing:
24 fps output. Character animation is drawn on twos (12 drawings per second); eye and mouth acting on threes. Holds are true holds: the drawing stays still and only hair, cloth and paper move. Mouths move only while speaking; a closed mouth stays closed. Camera moves are smooth on ones. No morphing between poses, no frame-blend ghosting, no AI interpolation smoothness.

Secondary motion:
The strands of pink hair that spill from Akane's hood sway a little when she moves her head and settle. Paper unfolds with real weight. Akira's curled hair ends move only slightly in the alley wind. No floating hair.

Color and light:
Inside: warm honey-colored bar light from behind Akane, soft and moody, against the cold blue line from the slot. Outside: dark blue and blue-grey alley. When the door opens a crack, the bar's warm light clearly spills out through the gap: a bright warm vertical strip that rims Akane's hood and hair from behind, lights her face with a warm glow, and falls as a warm line across the alley's stones and onto Akira's shoulder and hair in the foreground, in strong contrast with the cold blue night.

Screen direction: in the alley the door is on screen right; Akane in the gap looks to screen left; Akira stands on screen left facing right. Akira's face is never shown.

Shots:
[0-3s] Shot 1: [insert close-up of hands in the entrance, locked-off] Akane's fingers unfold the small folded note in the warm bar light, with the thin blue line from the slot behind it. The page is held at an angle so its content cannot be seen. Akane's line (quiet, to herself, off-screen): 「……正解」
[3-6s] Shot 2: [medium close shot inside, from behind her shoulder, locked-off] Hood up, Akane leans close against the edge of the door, the warm bar light behind her rimming her hood, her face hidden by the hood's shadow, and closes her hand on the door handle. A small click.
[6-10s] Shot 3: [extreme close-up from the alley, the camera right at the door, locked-off with a very slow push-in] The narrow vertical gap of the teal door fills the center of the frame; the edge of the brick wall is at the far right of the frame and nothing else of the alley is visible. The door opens just a few centimeters, a bright vertical strip of warm bar light spills out, and in it, for the first time, Akane's face fills the gap: one large blue-violet eye, her hair clips and the edge of her hood, very close to the camera. She looks left at someone outside and blinks once, calm and wary.
[10-15s] Shot 4: [close medium shot from the alley, over Akira's shoulder at very close range, locked-off] Akira's head and shoulder fill the left half of the frame, large and soft-focused, seen from behind: orange hair with two small buns, navy jacket collar, facing right. The door is right in front of her, close to the camera, filling the right half of the frame; the narrow gap is at the right, with a strip of brick wall at the far right edge. In the gap, backlit and rimmed by the bright warm light from the bar, Akane's face is clearly visible at medium close size, hood up, looking up at Akira with half-closed, unimpressed eyes; the warm light from the gap falls across Akira's shoulder and the back of her hair. Akane's line (flat, scolding): 「鼻歌。また外で歌ってきたでしょ」 Akira does not turn around.

Overall: keep Akane's face, hair, hood and colors identical in every shot and consistent with Image 1; keep Akira consistent with Image 2. The door stays an ordinary size and only opens a crack. Hard cuts on the timestamps, no dissolves. Stable lines, no line boiling, no flicker.

No subtitles. No text, letters, words, logos or numbers anywhere; the note, the door and the walls show no writing; no posters or signs with writing are in frame in Shots 3 and 4. Normal eyes, no glowing eyes. No other people.

Audio again: only Akane's voice, paper, door handle, door creak, light wind and a faint distant siren. No music, BGM, score, melody, piano, instrumental or ambient pad.
```

## テスト5 v2（フード常時・暁の動きをなめらかに・SDをやめて緊迫感）15秒

参照：Image 1 あかね／2 暁／3 路地／4 店内。

```
A 2D Japanese TV-anime sequence at deep night, outside and just inside the door of a hidden bar: Akane, the gatekeeper, scolds Akira through a narrow crack in the door; Akira brushes it off, Akane refuses coldly while watching the alley, then she opens the door and lets Akira in. A quiet, tense exchange in whispers, never comedic. Five shots, hand-drawn cel animation, dialogue in Japanese.

Audio: the two girls' low voices, almost whispering, light wind in the alley, a faint distant siren, the creak of the door opening wider, Akira's footsteps on wood, a soft muffled murmur from the bar with no intelligible words. No music of any kind: no BGM, no score, no melody, no piano, no instrumental, no ambient pad, no synth. No comic sound effects.

Asset bindings:
- Image 1: Akane's three-view character sheet (front, side, back). Use it for her face, eyes, long light-pink hair, hair clips, uniform and proportions. One person; ignore the white background and sheet layout.
- Image 2: Akira's three-view character sheet. Use it for her orange hair with two small curled buns, red-framed glasses, navy jacket with straps, camera and proportions. One person; ignore the white background and sheet layout.
- Image 3: the dark brick alley; the teal wooden door on the right wall is the bar's door, an ordinary single door with a narrow brass mail slot. Use it for Shots 1 to 3. No lamp over the door. Wall notices are blank.
- Image 4: the bar interior. Use it for the warm honey-colored light and the wood of the bar seen behind Akane in Shots 4 and 5.

Characters:
- Akane (Image 1): the bar's gatekeeper, a young woman. Long light-pink hair with hair clips, large blue-violet eyes. Over her uniform she wears a dark navy hooded outer jacket, and the hood is ALWAYS up, covering the top of her head, in every shot from the first frame to the last; only the front strands of her pink hair show under the hood. She never lowers the hood. Serious, strict and alert at the door.
- Akira (Image 2): a young woman newspaper reporter, a regular. Relaxed and cheeky, one hand in her pocket. Her face is never shown: she is seen from behind or as a silhouette in shadow.

Inside the entrance: a small vestibule between the alley door and the bar, softly filled with warm honey-colored light from the bar on the right. The door is on the left of the frame.

Art style:
2D hand-drawn TV anime, digital ink and paint, cel-shaded characters over painted backgrounds. Match the clean flat look of Images 1 and 2. Not 3D, not CG, not photoreal, not a painterly illustration.
Line art: thin, clean, even-weight lines. Character outer contour about 2.5 px at 1080p, inner detail lines about 1.5 px, no brush taper, no sketchy double lines. Lines are never pure black: character lines are a deep plum-brown (#3B2A33), leaning toward deep navy (#1E2340) in the cold light and warm brown in the bar light.
Color trace (iro-tore): inner lines of hair, highlight edges and shadow boundaries on skin and cloth are drawn in a darker tint of the neighboring fill color instead of the line color — pink hair uses rose lines, orange hair uses burnt-sienna lines, skin uses rose-brown lines.
Shading: two-tone cel shading (base + one hard-edged shadow), one hard highlight shape on hair, no soft gradients on characters except a thin rim light. Shadows shift toward blue-violet. Backgrounds are painted with no outlines.

Animation timing:
24 fps output. Body movement is smooth, natural and continuous, with real weight and easing in and out; no jerky, stuttering or choppy motion. Small acting such as blinks, glances and mouth movement stays subtle. Holds are calm and still, with only hair and cloth moving slightly. Mouths move only while that character speaks; a closed mouth stays closed. Camera moves are smooth. No morphing between poses, no frame-blend ghosting.

Secondary motion:
The strands of pink hair under Akane's hood sway a little when she turns her head and settle. Akira's curled hair ends move slightly with her shrug and her steps. The hood fabric folds naturally and stays on Akane's head. No floating hair.

Color and light:
Outside: dark blue and blue-grey alley, with the bar's warm light spilling through the door gap onto Akane's face, the stones and Akira's shoulder. Inside: warm honey-colored bar light behind Akane, moody but clearly visible. One consistent tense night mood in every shot; no pastel or plain backgrounds.

Screen direction: outside, the door is on screen right and Akane in the gap looks left; Akira stands on screen left facing right. Inside, the door is on screen left and the bar is on screen right; Akira enters from the left and passes to the right.

Shots:
[0-4s] Shot 1: [medium shot from the alley, over Akira's shoulder, locked-off] In the left foreground, Akira's back and the back of her orange head with two small buns, facing right; on the right, the door open only a narrow crack, Akane in the gap with her hood up, lit by the warm light from inside, looking at Akira with half-closed, unimpressed eyes. Akira gives one slow, small, relaxed shrug of her shoulders and lets them settle, smooth and unhurried. Akira's line (low, casual): 「あれくらい平気だろ」 Akane's line (flat, cold, quiet): 「捕まっても知りませんからね」
[4-7s] Shot 2: [close shot of Akira from behind her right shoulder, locked-off] Akira, seen from behind, lifts one hand lazily to shoulder height and gives a small, slow wave toward the door, her face never shown. Akira's line (low, lazy, teasing): 「そんときゃ差し入れ頼むわ」
[7-9s] Shot 3: [close-up of Akane in the door gap, hood up, locked-off] In the narrow gap, lit by the warm strip of light, Akane does not smile; her eyes flick once toward the dark alley entrance on the left, checking for patrols, then back. Akane's line (short, cold, very quiet): 「嫌です」
[9-12s] Shot 4: [medium shot inside the entrance, from behind Akane's right shoulder, locked-off] In the right foreground, Akane's back with the hood up and the edge of her profile, warm bar light on her. On the left she pulls the door open just wide enough for one person; outside in the dark alley stands Akira as a dark silhouette. Akane's line (formal, quiet): 「……どうぞ、お入りください」
[12-15s] Shot 5: [same angle, locked-off; the camera stays on Akane] Akira, her face in shadow, steps in through the door and walks past in front of Akane from left to right and out of frame on the right, toward the bar, with smooth natural steps. Akane, hood still up, keeps holding the door and looks out into the alley once more.

Overall: keep both characters' faces, hair, clothes and colors consistent with Images 1 and 2 in every shot; Akane's hood stays up in every shot. All characters keep normal proportions in every shot; no super-deformed or chibi style. The door is an ordinary single door. Hard cuts on the timestamps, no dissolves. Stable lines, no line boiling, no flicker.

No subtitles. No text, letters, words, logos or numbers anywhere; no posters or signs with writing in frame. Normal eyes, no glowing eyes. No other people.

Audio again: only the two girls' low voices, wind, a faint distant siren, door creak, footsteps, a muffled wordless murmur. No music, BGM, score, melody, piano, instrumental or ambient pad.
```

## テスト6｜店内BGテスト・カウンターの5人（アニメ調変換BG）15秒・Hamster

3DCGの店内をアニメ調に変換し撮影処理を入れた仮BG（参照_縮小/bg_bar_counter_test_animestyle.webp）での背景テスト。同じプロンプトで、3DCGそのまま版・色補正なし版などに背景だけ差し替えて比べる想定。
参照：Image 1 朔奈／2 まひる／3 海凪／4 暁／5 あかね／6 店内BG。

```
A 2D Japanese TV-anime sequence inside a small hidden bar at night, warm and cozy: five young women at the wooden counter. Behind the counter Sakuna quietly works and Mahiru proudly presents a dessert she just made; on the customer side Kairi sits on a stool, Akira sits at the far right stool, and Akane stands beside her. Four shots, hand-drawn cel animation, dialogue in Japanese. This is a background test: the set must match Image 6 exactly.

Audio: the girls' voices, the soft clink of glass and spoon, a low cozy room tone. No music of any kind: no BGM, no score, no melody, no piano, no instrumental, no ambient pad, no synth.

Asset bindings:
- Image 1: Sakuna's three-view character sheet. Use it for her face, long pale-blue hair tied low with bangs over one eye, black cropped jacket with striped cuffs, white shirt, orange tie, long grey slit skirt.
- Image 2: Mahiru's three-view character sheet. Use it for her face, wavy short blonde-to-orange hair with a blue ribbon, yellow eyes, grey pinafore dress with frilled hem, white off-shoulder puff sleeves, orange tie.
- Image 3: Kairi's three-view character sheet. Use it for her face, very long straight navy hair with small side tails and a white rabbit-ear ribbon, red eyes, grey waistcoat over a white blouse with sheer sleeves, black gloves, white thigh-high socks.
- Image 4: Akira's three-view character sheet. Use it for her orange hair with two small curled buns, red-framed glasses, light-blue shirt, navy cropped jacket with grey straps, camera on a lanyard, navy shorts.
- Image 5: Akane's three-view character sheet. Use it for her long light-pink hair with hair clips, blue-violet eyes, white and pale-grey uniform with an orange tie, white pleated skirt. Inside the bar she wears no hood.
- Image 6: the bar counter set. This is the exact background for every shot. Keep it exactly as in Image 6: the long dark-wood counter, the teal-cushioned bar stools, the bottle shelves on the right, the small shelves with teacups and jars, the purple range hood on the left, the cake dome, the white candles in gold holders, the black coasters and the small cards with an emblem. Keep its painted anime look, its warm cream and honey colors, its lighting and its photographic post effects (soft glow and bloom around the candles and lights, gentle warm haze, slight diffusion). Do not repaint, simplify, add or remove props.

Each character is one person; ignore the white backgrounds and sheet layouts of Images 1 to 5. Every face, hairstyle and outfit must match its sheet.

Placement (camera looking at the counter from the customer side, as in Image 6): behind the counter, Sakuna stands at the sink area left of center and Mahiru stands right of center in front of the bottle shelves. On the customer side, Kairi sits on the second stool from the left; Akira sits on the stool at the far right; Akane stands on the floor just behind and to the left of Akira. Nobody stands on the counter side who belongs on the customer side.

Art style:
2D hand-drawn TV anime, digital ink and paint, cel-shaded characters composited into the painted background of Image 6. Match the clean flat look of Images 1 to 5. Not 3D, not CG, not photoreal.
Line art: thin, clean, even-weight lines. Character outer contour about 2.5 px at 1080p, inner detail lines about 1.5 px, no brush taper, no sketchy double lines. Lines are never pure black: character lines are a warm deep plum-brown (#3B2A33) in this warm light.
Color trace (iro-tore): inner lines of hair, highlight edges and shadow boundaries on skin and cloth are drawn in a darker tint of the neighboring fill color — pale-blue hair uses grey-blue lines, blonde hair uses amber lines, navy hair uses deep indigo lines, orange hair uses burnt-sienna lines, pink hair uses rose lines, skin uses rose-brown lines.
Shading: two-tone cel shading (base + one hard-edged shadow) with one hard highlight shape on hair. Characters are lit to match Image 6: warm honey key light from above, soft warm bounce from the counter, and the same soft glow and slight diffusion as the background so they sit in the same photographed image.

Animation timing:
24 fps output. Body movement is smooth, natural and continuous, with real weight and easing; no jerky or stuttering motion. Mouths move only while that character speaks; a closed mouth stays closed. Holds are calm, with hair and cloth moving slightly. Camera moves are smooth. No morphing between poses, no frame-blend ghosting.

Secondary motion:
Mahiru's wavy hair and ribbon bounce when she lifts the dessert and settle. Kairi's long straight hair moves only a little. Sakuna's long hair sways slightly as she turns her head. No floating hair.

Shots:
[0-4s] Shot 1: [wide establishing shot, the exact camera angle and framing of Image 6, locked-off] All five are in the frame in their places. Sakuna quietly dries a glass at the sink. Mahiru sets a small glass of affogato on the counter and throws her arms up happily. Kairi, seated, turns her head slightly toward the dessert. Akira leans back on her stool, relaxed. Akane, standing, looks at Mahiru. Mahiru's line (bright, proud): 「できた！ まひる特製アフォガート！」
[4-7s] Shot 2: [medium shot of Mahiru behind the counter, the bottle shelves of Image 6 behind her, locked-off] Mahiru holds the affogato glass up with both hands, beaming, her hair bouncing and settling.
[7-11s] Shot 3: [medium two-shot from the counter edge, Kairi in the foreground on her stool, Sakuna softly out of focus behind the counter, locked-off] Kairi does not turn toward Mahiru; she glances sideways with a cool face and speaks quietly. Kairi's line (cool, quiet): 「……それ、あとで私の分もあるのよね？」 Behind her, Sakuna smiles gently.
[11-15s] Shot 4: [medium shot at the right end of the counter, locked-off] Akira sits on the far-right stool and settles back with a satisfied sigh; Akane, standing behind her, reaches out and straightens the collar of Akira's jacket. Akira's line (relaxed, content): 「やっぱ、ここだな」

Overall: keep all five characters' faces, hair, clothes and colors identical in every shot and consistent with Images 1 to 5. Keep the background identical to Image 6 in every shot. Hard cuts on the timestamps, no dissolves. Stable lines, no line boiling, no flicker.

No subtitles. No text, letters, words, logos or numbers anywhere; the small cards keep only their simple emblem. Normal eyes, no glowing eyes. No other people.

Audio again: only the girls' voices, glass and spoon sounds and a low room tone. No music, BGM, score, melody, piano, instrumental or ambient pad.
```

## テスト6 v2｜店内BG v2（レンガ壁）でカウンターの5人 15秒・Hamster

テスト6と同じプロンプトで、BGだけv2（参照_縮小/bg_bar_counter_v2.webp）に差し替え。BGの説明文のみv2に合わせて変更。

```
A 2D Japanese TV-anime sequence inside a small hidden bar at night, warm and cozy: five young women at the wooden counter. Behind the counter Sakuna quietly works and Mahiru proudly presents a dessert she just made; on the customer side Kairi sits on a stool, Akira sits at the far right stool, and Akane stands beside her. Four shots, hand-drawn cel animation, dialogue in Japanese. This is a background test: the set must match Image 6 exactly.

Audio: the girls' voices, the soft clink of glass and spoon, a low cozy room tone. No music of any kind: no BGM, no score, no melody, no piano, no instrumental, no ambient pad, no synth.

Asset bindings:
- Image 1: Sakuna's three-view character sheet. Use it for her face, long pale-blue hair tied low with bangs over one eye, black cropped jacket with striped cuffs, white shirt, orange tie, long grey slit skirt.
- Image 2: Mahiru's three-view character sheet. Use it for her face, wavy short blonde-to-orange hair with a blue ribbon, yellow eyes, grey pinafore dress with frilled hem, white off-shoulder puff sleeves, orange tie.
- Image 3: Kairi's three-view character sheet. Use it for her face, very long straight navy hair with small side tails and a white rabbit-ear ribbon, red eyes, grey waistcoat over a white blouse with sheer sleeves, black gloves, white thigh-high socks.
- Image 4: Akira's three-view character sheet. Use it for her orange hair with two small curled buns, red-framed glasses, light-blue shirt, navy cropped jacket with grey straps, camera on a lanyard, navy shorts.
- Image 5: Akane's three-view character sheet. Use it for her long light-pink hair with hair clips, blue-violet eyes, white and pale-grey uniform with an orange tie, white pleated skirt. Inside the bar she wears no hood.
- Image 6: the bar counter set. This is the exact background for every shot. Keep it exactly as in Image 6: the red-brick back wall, the long dark-wood counter, the teal-cushioned bar stools, the bottle shelves on the right, the small shelves with teacups and jars, the dark-blue range hood on the left, the cake dome, the lit white candles in gold holders, the black coasters and the small cards with an emblem. Keep its painted anime look, its warm brick-red and honey colors, its moody low-key candle and lamp lighting with soft pools of light and deep shadows under the counter, and its photographic post effects (soft glow around the candle flames and lamps, gentle warm haze, slight diffusion). Do not repaint, simplify, add or remove props.

Each character is one person; ignore the white backgrounds and sheet layouts of Images 1 to 5. Every face, hairstyle and outfit must match its sheet.

Placement (camera looking at the counter from the customer side, as in Image 6): behind the counter, Sakuna stands at the sink area left of center and Mahiru stands right of center in front of the bottle shelves. On the customer side, Kairi sits on the second stool from the left; Akira sits on the stool at the far right; Akane stands on the floor just behind and to the left of Akira. Nobody stands on the counter side who belongs on the customer side.

Art style:
2D hand-drawn TV anime, digital ink and paint, cel-shaded characters composited into the painted background of Image 6. Match the clean flat look of Images 1 to 5. Not 3D, not CG, not photoreal.
Line art: thin, clean, even-weight lines. Character outer contour about 2.5 px at 1080p, inner detail lines about 1.5 px, no brush taper, no sketchy double lines. Lines are never pure black: character lines are a warm deep plum-brown (#3B2A33) in this warm light.
Color trace (iro-tore): inner lines of hair, highlight edges and shadow boundaries on skin and cloth are drawn in a darker tint of the neighboring fill color — pale-blue hair uses grey-blue lines, blonde hair uses amber lines, navy hair uses deep indigo lines, orange hair uses burnt-sienna lines, pink hair uses rose lines, skin uses rose-brown lines.
Shading: two-tone cel shading (base + one hard-edged shadow) with one hard highlight shape on hair. Characters are lit to match Image 6: warm candle and lamp light from above and from the counter, soft warm bounce, deeper shadows, and the same soft glow and slight diffusion as the background so they sit in the same photographed image.

Animation timing:
24 fps output. Body movement is smooth, natural and continuous, with real weight and easing; no jerky or stuttering motion. Mouths move only while that character speaks; a closed mouth stays closed. Holds are calm, with hair and cloth moving slightly. Camera moves are smooth. No morphing between poses, no frame-blend ghosting.

Secondary motion:
Mahiru's wavy hair and ribbon bounce when she lifts the dessert and settle. Kairi's long straight hair moves only a little. Sakuna's long hair sways slightly as she turns her head. No floating hair.

Shots:
[0-4s] Shot 1: [wide establishing shot, the exact camera angle and framing of Image 6, locked-off] All five are in the frame in their places. Sakuna quietly dries a glass at the sink. Mahiru sets a small glass of affogato on the counter and throws her arms up happily. Kairi, seated, turns her head slightly toward the dessert. Akira leans back on her stool, relaxed. Akane, standing, looks at Mahiru. Mahiru's line (bright, proud): 「できた！ まひる特製アフォガート！」
[4-7s] Shot 2: [medium shot of Mahiru behind the counter, the bottle shelves of Image 6 behind her, locked-off] Mahiru holds the affogato glass up with both hands, beaming, her hair bouncing and settling.
[7-11s] Shot 3: [medium two-shot from the counter edge, Kairi in the foreground on her stool, Sakuna softly out of focus behind the counter, locked-off] Kairi does not turn toward Mahiru; she glances sideways with a cool face and speaks quietly. Kairi's line (cool, quiet): 「……それ、あとで私の分もあるのよね？」 Behind her, Sakuna smiles gently.
[11-15s] Shot 4: [medium shot at the right end of the counter, locked-off] Akira sits on the far-right stool and settles back with a satisfied sigh; Akane, standing behind her, reaches out and straightens the collar of Akira's jacket. Akira's line (relaxed, content): 「やっぱ、ここだな」

Overall: keep all five characters' faces, hair, clothes and colors identical in every shot and consistent with Images 1 to 5. Keep the background identical to Image 6 in every shot. Hard cuts on the timestamps, no dissolves. Stable lines, no line boiling, no flicker.

No subtitles. No text, letters, words, logos or numbers anywhere; the small cards keep only their simple emblem. Normal eyes, no glowing eyes. No other people.

Audio again: only the girls' voices, glass and spoon sounds and a low room tone. No music, BGM, score, melody, piano, instrumental or ambient pad.
```

## テスト6 v3｜BG v3・カット割り修正 15秒・Hamster

BG v3（参照_縮小/bg_bar_counter_v3.webp）。変更：注ぐインサート→まひるの「できた！」の喜び、あかねは手下ではなく呆れた姉のように襟を直してそっぽ、海凪の目（中心にハイライト、黒い瞳孔なし）。

```
A 2D Japanese TV-anime sequence inside a small hidden bar at night, warm and cozy: five young women at the wooden counter. Mahiru finishes her special affogato behind the counter and bursts with pride; Kairi teases her coolly; Akira, just back from outside, settles in at her usual seat while Akane fusses over her like an exasperated older sister. Five shots, hand-drawn cel animation, dialogue in Japanese. The set must match Image 6.

Audio: the girls' voices, espresso pouring, the soft clink of glass and spoon, a low cozy room tone. No music of any kind: no BGM, no score, no melody, no piano, no instrumental, no ambient pad, no synth.

Asset bindings:
- Image 1: Sakuna's three-view character sheet. Use it for her face, long pale-blue hair tied low with bangs over one eye, black cropped jacket with striped cuffs, white shirt, orange tie, long grey slit skirt.
- Image 2: Mahiru's three-view character sheet. Use it for her face, wavy short blonde-to-orange hair with a blue ribbon, yellow eyes, grey pinafore dress with frilled hem, white off-shoulder puff sleeves, orange tie.
- Image 3: Kairi's three-view character sheet. Use it for her face, very long straight navy hair with small side tails and a white rabbit-ear ribbon, grey waistcoat over a white blouse with sheer sleeves, black gloves, white thigh-high socks. Kairi's eyes exactly as in Image 3: rose-red irises with a pale vertical highlight in the very center of each eye and a small warm orange glow just below it; there is no black pupil — the center of her eye is light, not dark. Dark upper lashes.
- Image 4: Akira's three-view character sheet. Use it for her orange hair with two small curled buns at the back, red-framed glasses, light-blue shirt, navy cropped jacket with grey straps, camera on a lanyard, navy shorts.
- Image 5: Akane's three-view character sheet. Use it for her long light-pink hair with hair clips, blue-violet eyes, white and pale-grey uniform with an orange tie, white pleated skirt. Inside the bar she wears no hood.
- Image 6: the bar counter set. This is the background for every shot. Keep it as in Image 6: the red-brick back wall, the long dark-wood counter, the teal-cushioned bar stools, the bottle shelves on the right, the small shelves with teacups and jars, the brushed grey-metal range hood on the left, the cake dome, the lit white candles in gold holders, the black coasters and the small cards with an emblem. Keep its painted anime look, its warm brick-red and honey colors, its soft warm lamp and candle lighting with gentle shadows, and its photographic post effects (soft glow around the candle flames and lamps, gentle warm haze, slight diffusion). Closer shots show parts of this same set with the same props in the same places; do not invent a different room.

Each character is one person; ignore the white backgrounds and sheet layouts of Images 1 to 5. Every face, eye design, hairstyle and outfit must match its sheet.

Placement (camera looking at the counter from the customer side, as in Image 6): behind the counter, Sakuna stands at the sink area left of center and Mahiru stands right of center in front of the bottle shelves. On the customer side, Kairi sits on the second stool from the left; Akira sits on the stool at the far right; Akane stands on the floor just behind and to the left of Akira.

Art style:
2D hand-drawn TV anime, digital ink and paint, cel-shaded characters composited into the painted background of Image 6. Match the clean flat look of Images 1 to 5. Not 3D, not CG, not photoreal.
Line art: thin, clean, even-weight lines. Character outer contour about 2.5 px at 1080p, inner detail lines about 1.5 px, no brush taper, no sketchy double lines. Lines are never pure black: character lines are a warm deep plum-brown (#3B2A33) in this warm light.
Color trace (iro-tore): inner lines of hair, highlight edges and shadow boundaries on skin and cloth are drawn in a darker tint of the neighboring fill color — pale-blue hair uses grey-blue lines, blonde hair uses amber lines, navy hair uses deep indigo lines, orange hair uses burnt-sienna lines, pink hair uses rose lines, skin uses rose-brown lines.
Shading: two-tone cel shading (base + one hard-edged shadow) with one hard highlight shape on hair. Characters are lit to match Image 6: warm lamp and candle light from above and from the counter, soft warm bounce, and the same soft glow and slight diffusion as the background.

Animation timing:
24 fps output. Body movement is smooth, natural and continuous, with real weight and easing, and with clear, readable acting; no jerky or stuttering motion. Mouths move only while that character speaks; a closed mouth stays closed. Holds are calm, with hair and cloth moving slightly. No morphing between poses, no frame-blend ghosting.

Secondary motion:
Mahiru's wavy hair and ribbon spring up when she throws her arms up and settle in two small bounces. Kairi's long straight hair moves only a little. Sakuna's long hair sways slightly as she turns her head. Akane's long hair swings once when she turns away. No floating hair.

Shots:
[0-3s] Shot 1: [wide establishing shot, the camera angle and framing of Image 6, locked-off] All five in their places. Behind the counter, Mahiru leans over a small glass in total concentration, tongue slightly out; Sakuna quietly dries a glass beside the sink; Kairi, seated, watches Mahiru from the corner of her eye; Akira has just sat down on the far-right stool, and Akane stands behind her.
[3-5s] Shot 2: [insert close-up on the counter, locked-off] Mahiru's hand slowly pours a thin stream of dark espresso from a small metal pitcher over a round scoop of vanilla ice cream in a glass; the coffee runs down the scoop and the ice cream starts to melt, a wisp of steam rising in the warm candle light.
[5-8s] Shot 3: [medium close-up of Mahiru behind the counter, the bottle shelves behind her, slow push-in] She lifts her head, her eyes go wide and sparkle, a huge proud grin spreads across her face, and she throws both arms straight up in triumph, her hair and ribbon springing. Mahiru's line (bursting with joy and pride): 「できた！ まひる特製アフォガート！」
[8-11s] Shot 4: [medium two-shot from the counter edge, Kairi in the foreground on her stool, Sakuna softly out of focus behind the counter, locked-off] Kairi does not turn toward Mahiru; she props her chin on her gloved hand, glances sideways with a cool, slightly amused face and speaks quietly. Kairi's line (cool, teasing): 「……それ、あとで私の分もあるのよね？」 Behind her, Sakuna covers a small smile with her hand.
[11-15s] Shot 5: [medium shot at the right end of the counter, locked-off] Akira slumps back on the far-right stool with a satisfied sigh, her jacket collar crooked. Akira's line (relaxed, content): 「やっぱ、ここだな」 Akane, still a little cross with her from the door, puts one hand on her hip, lets out a short exasperated sigh, and with a quick brisk tug straightens Akira's collar like a fussy older sister — not like a servant — then folds her arms and turns her face away with slightly puffed cheeks. Akira grins at her.

Overall: keep all five characters' faces, eye designs, hair, clothes and colors identical in every shot and consistent with Images 1 to 5. Keep the background consistent with Image 6 in every shot. Hard cuts on the timestamps, no dissolves. Stable lines, no line boiling, no flicker.

No subtitles. No text, letters, words, logos or numbers anywhere; the small cards keep only their simple emblem. Normal eyes, no glowing eyes. No other people.

Audio again: only the girls' voices, espresso pouring, glass and spoon sounds and a low room tone. No music, BGM, score, melody, piano, instrumental or ambient pad.
```

## テスト6 v4｜BG v4・新三面図（あかね・暁）・海凪の目の参照 15秒・Hamster 1080p

参照：Image 1 朔奈／2 まひる／3 海凪／4 暁（akira_v2）／5 あかね（akane_v2）／6 BG v4（ろうそく・ケーキドームなし）／7 海凪の目のアップ。

```
A 2D Japanese TV-anime sequence inside a small hidden bar at night, warm and cozy: five young women at the wooden counter. Mahiru finishes her special affogato behind the counter and bursts with pride; Kairi teases her coolly; Akira, just back from outside, settles in at her usual seat while Akane fusses over her like an exasperated older sister. Five shots, hand-drawn cel animation, dialogue in Japanese. The set must match Image 6.

Audio: the girls' voices, espresso pouring, the soft clink of glass and spoon, a low cozy room tone. No music of any kind: no BGM, no score, no melody, no piano, no instrumental, no ambient pad, no synth.

Asset bindings:
- Image 1: Sakuna's three-view character sheet. Use it for her face, long pale-blue hair tied low with bangs over one eye, black cropped jacket with striped cuffs, white shirt, orange tie, long grey slit skirt.
- Image 2: Mahiru's three-view character sheet. Use it for her face, wavy short blonde-to-orange hair with a blue ribbon, yellow eyes, grey pinafore dress with frilled hem, white off-shoulder puff sleeves, orange tie.
- Image 3: Kairi's three-view character sheet. Use it for her face, very long straight navy hair with small side tails and a white rabbit-ear ribbon, grey waistcoat over a white blouse with sheer sleeves, black gloves, white thigh-high socks.
- Image 7: a close-up of Kairi's eyes. Copy her eye design exactly from Image 7 in every shot: dark rose-red irises; in the very center of each iris a bright white vertical oval highlight, with a small warm orange glow directly under it; there is no black or dark pupil anywhere — the center of each eye is white and bright. Dark brown upper lash line.
- Image 4: Akira's three-view character sheet. Use it for her face, light-blue eyes, shoulder-length orange hair with a small curled bun on each side at the back, red half-rim glasses, light-blue shirt, oversized navy cropped jacket with wide sleeves, grey hanging straps and a black wristband, small camera on a lanyard, navy shorts with cargo pockets, grey knee-high boots.
- Image 5: Akane's three-view character sheet. Use it for her face, blue-violet eyes, long wavy light-pink hair with a small side bun tied with a white fluffy ornament and two black hair clips, pale-grey double-breasted vest with a sailor collar and an orange tie, detached white sleeves with blue trim, white pleated skirt, dark tights, black ankle boots. Inside the bar she wears no hood.
- Image 6: the bar counter set. This is the background for every shot. Keep it as in Image 6: the red-brick back wall, the long dark-wood counter, the teal-cushioned bar stools, the bottle shelves on the right, the small shelves with teacups and jars, the dark grey range hood on the left, the kettle and pot on the stove, the mixing bowl, the black coasters, the small menu cards with an emblem and the napkin holders. There are no candles and no cake dome on the counter. Keep its painted anime look, its warm brick-red and honey colors, its soft warm lamp lighting with gentle shadows, and its photographic post effects (soft glow around the lamps, gentle warm haze, slight diffusion). Closer shots show parts of this same set with the same props in the same places; do not invent a different room.

Each character is one person; ignore the white backgrounds and sheet layouts of Images 1 to 5. Every face, eye design, hairstyle and outfit must match its sheet; Image 7 is only Kairi's eye reference, not another person.

Placement (camera looking at the counter from the customer side, as in Image 6): behind the counter, Sakuna stands at the sink area left of center and Mahiru stands right of center in front of the bottle shelves. On the customer side, Kairi sits on the second stool from the left; Akira sits on the stool at the far right; Akane stands on the floor just behind and to the left of Akira.

Art style:
2D hand-drawn TV anime, digital ink and paint, cel-shaded characters composited into the painted background of Image 6. Match the clean flat look of Images 1 to 5. Not 3D, not CG, not photoreal.
Line art: thin, clean, even-weight lines. Character outer contour about 2.5 px at 1080p, inner detail lines about 1.5 px, no brush taper, no sketchy double lines. Lines are never pure black: character lines are a warm deep plum-brown (#3B2A33) in this warm light.
Color trace (iro-tore): inner lines of hair, highlight edges and shadow boundaries on skin and cloth are drawn in a darker tint of the neighboring fill color — pale-blue hair uses grey-blue lines, blonde hair uses amber lines, navy hair uses deep indigo lines, orange hair uses burnt-sienna lines, pink hair uses rose lines, skin uses rose-brown lines.
Shading: two-tone cel shading (base + one hard-edged shadow) with one hard highlight shape on hair. Characters are lit to match Image 6: warm lamp light from above, soft warm bounce, and the same soft glow and slight diffusion as the background.

Animation timing:
24 fps output. Body movement is smooth, natural and continuous, with real weight and easing, and with clear, readable acting; no jerky or stuttering motion. Mouths move only while that character speaks; a closed mouth stays closed. Holds are calm, with hair and cloth moving slightly. No morphing between poses, no frame-blend ghosting.

Secondary motion:
Mahiru's wavy hair and ribbon spring up when she throws her arms up and settle in two small bounces. Kairi's long straight hair moves only a little. Sakuna's long hair sways slightly as she turns her head. Akane's long hair swings once when she turns away. No floating hair.

Shots:
[0-3s] Shot 1: [wide establishing shot, the camera angle and framing of Image 6, locked-off] All five in their places. Behind the counter, Mahiru leans over a small glass in total concentration, tongue slightly out; Sakuna quietly dries a glass beside the sink; Kairi, seated, watches Mahiru from the corner of her eye; Akira has just sat down on the far-right stool, and Akane stands behind her.
[3-5s] Shot 2: [insert close-up on the counter, locked-off] Mahiru's hand slowly pours a thin stream of dark espresso from a small metal pitcher over a round scoop of vanilla ice cream in a glass; the coffee runs down the scoop and the ice cream starts to melt, a wisp of steam rising in the warm lamp light.
[5-8s] Shot 3: [medium close-up of Mahiru behind the counter, the bottle shelves behind her, slow push-in] She lifts her head, her eyes go wide and sparkle, a huge proud grin spreads across her face, and she throws both arms straight up in triumph, her hair and ribbon springing. Mahiru's line (bursting with joy and pride): 「できた！ まひる特製アフォガート！」
[8-11s] Shot 4: [medium two-shot from the counter edge, Kairi in the foreground on her stool, Sakuna softly out of focus behind the counter, locked-off] Kairi does not turn toward Mahiru; she props her chin on her gloved hand, glances sideways with a cool, slightly amused face and speaks quietly. Kairi's line (cool, teasing): 「……それ、あとで私の分もあるのよね？」 Behind her, Sakuna covers a small smile with her hand.
[11-15s] Shot 5: [medium shot at the right end of the counter, locked-off] Akira slumps back on the far-right stool with a satisfied sigh, her jacket collar crooked. Akira's line (relaxed, content): 「やっぱ、ここだな」 Akane, still a little cross with her from the door, puts one hand on her hip, lets out a short exasperated sigh, and with a quick brisk tug straightens Akira's collar like a fussy older sister — not like a servant — then folds her arms and turns her face away with slightly puffed cheeks. Akira grins at her.

Overall: keep all five characters' faces, eye designs, hair, clothes and colors identical in every shot and consistent with Images 1 to 5. Keep the background consistent with Image 6 in every shot. Hard cuts on the timestamps, no dissolves. Stable lines, no line boiling, no flicker.

No subtitles. No text, letters, words, logos or numbers anywhere; the small cards keep only their simple emblem. Normal eyes, no glowing eyes. No other people.

Audio again: only the girls' voices, espresso pouring, glass and spoon sounds and a low room tone. No music, BGM, score, melody, piano, instrumental or ambient pad.
```

## 見るポイント

- 三面図の顔・髪・衣装にどこまで似るか（特に先輩のツインテールと帽子、後輩の片目の前髪、暁のお団子と眼鏡）
- 書いた動作がどこまで出るか：減速して止まる、肩が落ちる、手をポケットから出す、指さし、振り向き
- コマ打ち（2コマ／3コマ）が出るか、ヌルヌル補間になるか
- 髪の遅れと収まり、紙・布の揺れ
- 昼の背景を夜に変換できるか、文字が出ないか、BGMが入らないか
- 秒数の区切りどおりに4ショットになっているか

Related: [冒頭マルチショット案](EP01_Seedance25_冒頭マルチショット案.md) · [EP01 v6 指示書](../字コンテ_v6/EP01_v6_指示書.md)
