r"""9話を「制作中」として月灯スタジオに載せる（動作確認用の仮制作）。

エージェントが手順どおりに進めた制作前段階（G1 設計 → G2 仮Vコンの準備 → ショット分け → プロンプトの仕上げ）を、
どの PC でも同じ状態に再現する。DB は git に入らないので、このスクリプトが作業の記録を兼ねる。

  python studio/seeds/EP09_仮制作.py            # 空の DB に 9話を載せる（すでにあれば止まる）
  python studio/seeds/EP09_仮制作.py --reset    # 9話を消してから載せ直す
  python studio/seeds/EP09_仮制作.py --reset --refs "C:\Users\kaka\Desktop\e002素材\参照"
                                                  # 参照画像のフォルダがあれば、参照素材の棚にも入れる

設計の考え方・監督への確認事項は 月灯_vault/02_各話/EP09/EP09_演出設計_3分版.md
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from studio.backend import core, db, seedance, storyboard  # noqa: E402
from studio.backend.importers import jikonte  # noqa: E402

EP = "EP09"
AGENT = "claude-cloud（仮制作）"
PROMPTS = ROOT / "月灯_vault/02_各話/EP09/プロンプト"

# ---- G1 設計（3分版。4分版の字コンテのシーンに合わせ、目標尺で詰める） ----
SCENES = [
    ("S1", dict(place="月灯り店内", time="夕方（営業前）", look="B", target=25, cameras="A,C",
                purpose="いつもの営業前の中で、あかねだけが落ち着かない。打ち明けた直後、扉の向こうで物音",
                emotion="あかね：上の空（同じグラスを運ぶ）→不安（エプロンの裾を握る）→物音で門番の顔へ切り替わる",
                blocking="朔奈＝カウンター内・席2の前で酒瓶を並べる／まひる＝カウンター内・席4の前で仕込み／海凪＝ピアノ（手前左）／"
                         "あかね＝グラスを持って客席を往復→入口の横（門番の位置）で3人の方を向いて打ち明ける",
                props="グラス（あかねが持ったまま）、酒瓶（カウンター上→物音で下へ）、お客様ノート（入口の横の棚）")),
    ("S2", dict(place="月灯り店内", time="夕方", look="C", target=18, cameras="A,C",
                purpose="いつもの入店の合図（メモ→鈴）とちがう激しいノック。暁が仕事着のまま飛び込み「今日、ここに来る」",
                emotion="全員：警戒→暁と分かって一瞬ゆるむ→「今日来る」で凍る。朔奈だけが先に店長の顔になる",
                blocking="あかね＝扉の前／暁＝扉から入って後ろ手に閉め、入口の前に立つ（社員証を首にかけたまま）／3人＝カウンターの前に寄る",
                props="暁の社員証（外さないまま＝ただごとではない）")),
    ("S3", dict(place="月灯り店内", time="夕方", look="C", target=18, cameras="A,F",
                purpose="一斉に証拠を消す速いテンポ。ピアノの蓋を閉じる重さ。ステラ騒ぎの一息。"
                        "【案】あかねがステラを抱き止めようとして、お客様ノートを入口の棚に戻してしまう（片付け忘れ→S8）",
                emotion="速さと焦り。海凪だけが一瞬止まる（蓋）。ステラでほんの少し笑いが戻り、おばあの声で凍る",
                blocking="朔奈＝カウンター内で酒瓶を箱へ／あかね・まひる＝客席のグラスと皿／海凪＝ピアノ／暁＝入口の受け箱のメモ／ステラ＝カウンターの上→床",
                props="お客様ノート（棚に戻ったまま＝片付け忘れ【案】）、合言葉のメモの束、酒瓶の箱")),
    ("S4", dict(place="パン屋", time="夕方（閉店後）", look="F", target=8, cameras="パン屋",
                purpose="パンを見ない先輩。動じないおばあ",
                emotion="先輩：仕事の顔（パンの前で目が輝かない）／おばあ：いつもの調子",
                blocking="おばあ＝レジ台／先輩＝入口から陳列台の前（手を後ろで組む）／後輩＝少し後ろ（ポケットに手）")),
    ("S5", dict(place="月灯り店内→控室", time="夕方", look="C", target=8, cameras="控室",
                purpose="屋根裏へ逃げる。最後に暁が折りたたみ階段を引き上げる",
                emotion="焦り。まひるの腕の中で暴れるステラ",
                blocking="控室＝白い LED。天井の端の蓋から折りたたみ階段。上がる順：あかね→まひる（ステラ）→海凪→朔奈→暁")),
    ("S6", dict(place="パン屋", time="夕方", look="F", target=14, cameras="パン屋",
                purpose="先輩の推理（黒板が閉店後に書き換わる）と、おばあの肝の据わり方。後輩がさりげなく先輩をなだめる",
                emotion="先輩：静かな確信／おばあ：笑ってかわす／後輩：だるそうに筋を通す",
                blocking="S4 と同じ。最後におばあが奥（控室側）へ手で示す")),
    ("S7", dict(place="屋根裏", time="夕方", look="C", target=10, cameras="屋根裏",
                purpose="この回で一番怖い場面。床板の隙間の白い光の中を足音が横切る。ステラの「ニャ」で全員が凍る。いちばん長く止める",
                emotion="息を殺す。音を引き、足音と呼吸だけ",
                blocking="傾いた天井と梁の下に5人とステラが身を寄せる。まひる＝ステラを抱く／あかね＝手ぶら（ノートは下に置き忘れ【案】）")),
    ("S8", dict(place="控室→月灯り店内", time="夕方", look="C", target=22, cameras="A,入口",
                purpose="誰もいない店を見回す先輩の余裕。ピアノの蓋。【正本】入口の棚の、片付け忘れたお客様ノートを開き、"
                        "4人の字の「今日も、誰も捕まらなかった。」を読む→何も持たずに閉じて置く。「また明日来るぞ」",
                emotion="先輩：余裕→ノートで一瞬止まる（いい店だと確信。誰にも言わない）。後輩は気づかない",
                blocking="先輩＝控室の扉から入り、手を後ろで組んで客席→ピアノ→入口の棚。後輩＝カウンターの前でポケットに手",
                props="お客様ノート（入口の棚）。酒も客もいない。照明は消え、窓の夕方の光だけ")),
    ("S9", dict(place="屋根裏", time="夕方", look="E", target=6, cameras="屋根裏",
                purpose="こわさが抜ける", emotion="本気の安堵。全員が床に崩れ落ちる")),
    ("S10", dict(place="屋根裏", time="夜", look="B", target=12, cameras="屋根裏",
                 purpose="「お泊まり！？」で空気がほどける。【正本】暁も泊まる（帰る件は削る）",
                 emotion="まひる：ぱっと明るく／海凪：つっこみ／朔奈：暁へ心からの「ありがとう」",
                 blocking="ランプ一つの暖かい光。暁＝梁にもたれる")),
    ("S11", dict(place="屋根裏", time="夜〜深夜", look="E", target=39, cameras="屋根裏,ベランダ",
                 purpose="パジャマで笑う→灯りを消した夜、自分を責めるあかね→【正本】「せいじゃない」を一人ずつ"
                         "（まひる→海凪「あかねさんばかりに、ごめんなさい」→暁「いつも頑張ってたな」→朔奈「あかねちゃんのせいじゃない」）"
                         "→「絶対に、ここは守る」→みんなが寝たあと、ベランダで暁にだけ本音（「みんなが捕まるのはいや」）→暁「少し休もう」",
                 emotion="あかね：自責→頼る→決意→本音。10話の「閉めよう」の芽",
                 blocking="布団を並べる。ステラはまひるのそば。ベランダ＝屋根裏の小窓の外。暁が先に出ている",
                 props="4人のパジャマ（仮デザイン）、ランプ")),
    ("S12", dict(place="屋根裏→パン屋の屋根", time="深夜", look="E", target=0, cameras="―",
                 purpose="【削る案】決定ログ 10/8「ステラは脱走しない（9話の天窓から消える…はなし）」。4分版の13秒を S11 へ回す",
                 emotion="―")),
]

# ---- ショット分け（Seedance 2.5：1本30秒まで。字コンテと仮Vコンを並べて、つながりで分けた） ----
SHOTS = [
    ("SH01", ["S1-01", "S1-02", "S1-03"], "営業前の繰り返し（同じグラス）を引き→寄りで1本"),
    ("SH02", ["S1-04", "S1-05", "S1-06"], "打ち明け。8話のフラッシュ（先輩の目）を挟むが、視線のやりとりなので1本"),
    ("SH03", ["S1-07", "S1-08", "S2-01"], "物音→扉へ→激しいノックまで、同じ緊張を切らずに1本"),
    ("SH04", ["S2-02", "S2-03", "S2-04"], "暁が飛び込んで「今日来る」まで"),
    ("SH05", ["S2-05", "S3-01"], "「営業は中止」から片付けの開始へ、勢いをつなぐ"),
    ("SH06", ["S3-02", "S3-03", "S3-04"], "メモの回収→ステラ騒ぎ（ノートを置き忘れる一拍）→「来た」"),
    ("SH07", ["S4-01", "S4-02"], "パン屋：先輩とおばあ"),
    ("SH08", ["S5-01", "S5-02"], "控室から屋根裏へ。階段を引き上げるまで"),
    ("SH09", ["S6-01", "S6-02", "S6-03"], "問答は間が命なので1本（尺は詰める）"),
    ("SH10", ["S7-01", "S7-02", "S7-03", "S8-01"], "屋根裏の足音と、天井の蓋を見上げる先輩を1本で交互に"),
    ("SH11", ["S8-02", "S8-03", "S8-04", "S8-05"], "誰もいない店を見回す先輩。ここにノートを読む芝居を足す（設計 S8）"),
    ("SH12", ["S8-06", "S8-07", "S8-08"], "入口→屋根裏の反応→「また明日来るぞ」"),
    ("SH13", ["S9-01", "S9-02"], "安堵"),
    ("SH14", ["S10-01", "S10-02"], "「お泊まり！？」"),
    ("SH15", ["S10-03", "S10-04"], "暁への「ありがとう」（暁が帰る件は設計で削る→字コンテ v2 で差し替え）"),
    ("SH16", ["S11-01", "S11-02"], "パジャマで笑う→寝落ち"),
    ("SH17", ["S11-03"], "独白。ここに「せいじゃない」とベランダを足す（字コンテ v2）"),
    ("SH18", ["S12-01", "S12-02"], "【保留】決定ログでは削る。監督の判断までは生成しない"),
]

# 参照素材（e009/EP09_reference_map.csv のファイル名）。--refs のフォルダにあるものだけ棚に入れる
REFS = [
    ("character", "あかね", "akane_moto_260909.png"), ("character", "朔奈", "sakuna_moto_260909.png"),
    ("character", "まひる", "mahiru_moto_260909.png"), ("character", "海凪", "kairi_moto_260909.png"),
    ("character", "暁", "akira_moto_260909.png"), ("character", "ステラ", "stera_moto_260914.png"),
    ("character", "先輩", "senpai_moto_260914.png"), ("character", "後輩", "kohai_moto_260914.png"),
    ("layout", "店内配置図", "月灯_店内配置図_カメラ位置.png"),
    # 背景は今は1枚ずつ。Blender のカメラ位置ごとのレンダーができたら bg-render --asset-name 店内:A などで置き換える
    ("bg", "店内:A", "月明かり店内.png"), ("bg", "店内:入口の内側", "月明かり店内.png"),
    ("bg", "パン屋:P2", "パン屋店内.png"), ("bg", "屋根裏:屋根裏", "月明かり屋根裏部屋.png"),
    ("bg", "控室:控室", "月明かり控室.png"), ("bg", "屋根の上:屋根の上", "パン屋外観.png"),
]

QUESTIONS = ("確認したいこと（設計ノート 02_各話/EP09/EP09_演出設計_3分版.md）："
             "①4分版（10/6）と正本・決定ログ（10/8〜）の食い違い。先輩がノートを読む／暁も泊まる／「せいじゃない」／ベランダ／"
             "ステラの天窓を削る、を正本どおりに組む案でよいか。"
             "②お客様ノートを置き忘れるのはあかね（S3 のステラ騒ぎで棚に戻してしまう）でよいか。"
             "③S8 は「ノートを読む」を主にし、4分版の「鈴を鳴らして仕組みを見抜く」は外す案（22秒に収まらない）。"
             "④3分に詰めるため、S6 の問答と S10 の暁の帰りを削る。")

REQUEST = "9話を制作中として、脚本と字コンテから制作前段階（設計・仮Vコンの準備・ショット分け・プロンプト）を途中まで進めて"
RESULT = ("G1 設計（3分版、12シーン・目標180秒）を「確認待ち」で登録。仮Vコン 21シート、ショット 18本に分けた。"
          "SB01（仮Vコン）と SH01・SH03（480p ドラフト）のプロンプトを仕上げて点検済み（vault 02_各話/EP09/プロンプト）。"
          "生成は HAMSTER 保留のため未送信。参照素材（キャラ設定資料・Blender 背景）が棚に未登録。"
          "正本と4分版の食い違い3点を設計ノートの「確認したいこと」に。")


def main(reset: bool, refs: str | None) -> None:
    db.init()
    with db.session() as conn:
        ep = db.episode_by_code(conn, EP)
        if ep and not reset:
            print(f"{EP} はもうあります。載せ直すなら --reset")
            return
        if ep:
            for t in ("cuts", "takes", "reviews", "scenes", "shots", "boards", "documents", "usage", "comparisons"):
                conn.execute(f"DELETE FROM {t} WHERE episode_id=?", (ep["id"],))
            conn.execute("DELETE FROM requests WHERE episode=?", (EP,))
            conn.execute("DELETE FROM episodes WHERE id=?", (ep["id"],))

        # 監督の依頼 → エージェントが取る
        rid = core.add_request(conn, REQUEST, EP)
        core.claim_request(conn, AGENT, rid)

        # 参照素材の棚（あるものだけ）
        if refs:
            from studio.backend import shots as shotlib
            for kind, name, fname in REFS:
                f = Path(refs) / fname
                if f.exists():
                    shotlib.add_asset(conn, kind, name, str(f), note="EP09 の参照（e009）")
                else:
                    print(f"参照がありません：{f}")

        # 字コンテ（4分版）を取り込む。設計は3分で引くので、尺は字コンテ v2 で詰める
        jikonte.import_file(conn, EP, ROOT / "e009/EP09_字コンテ_4分版.xlsx", "4分版",
                            vault_rel="e009/EP09_字コンテ_4分版.xlsx")
        ep = db.episode_by_code(conn, EP)
        db.update(conn, "episodes", ep["id"], {"title": "本当のこわさ", "target_seconds": 180, "is_test": 1,
                                               "stage": "設計", "deadline": "2026-10-22"})

        # G1 設計
        for i, (code, f) in enumerate(SCENES, 1):
            target = f.pop("target")
            core.set_scene(conn, EP, code, seq=i, target_seconds=target, status="review", **f)

        # 仮Vコンのシート分けとショット分け
        storyboard.plan_boards(conn, EP)
        conn.execute("DELETE FROM shots WHERE episode_id=?", (ep["id"],))
        for code, cuts, note in SHOTS:
            seedance.set_shot(conn, EP, code, cuts, note)

        # 仕上げたプロンプトを点検（送るのは HAMSTER 接続後）
        for shot in ("SH01", "SH03"):
            p = PROMPTS / f"{shot}_480p.txt"
            if p.exists():
                sh = db.one(conn.execute("SELECT id FROM shots WHERE episode_id=? AND code=?", (ep["id"], shot)))
                b = seedance.build_brief(conn, sh["id"], "draft")
                issues = seedance.lint(p.read_text(encoding="utf-8"), len(b["refs"]) or 6)
                print(f"{shot} の点検：" + ("問題なし" if not issues else " / ".join(issues)))

        # G1 の確認事項を、監督のレビュー受け箱に「エージェントの返答を確認」として積む
        rv = core.add_review(conn, target_type="episode", target_id=ep["id"], verdict="保留", tags=["意図", "尺・テンポ"],
                             comment="【G1 設計の確認のお願い】9話 3分版", created_by="agent")
        core.respond_review(conn, rv, QUESTIONS, status="proposed")

        core.finish_request(conn, rid, RESULT)
    print("9話を載せました。画面：http://localhost:8765/#/ep/EP09/design")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--reset", action="store_true")
    ap.add_argument("--refs", help="参照画像のフォルダ（キャラの設定資料・背景・配置図）")
    a = ap.parse_args()
    main(a.reset, a.refs)
