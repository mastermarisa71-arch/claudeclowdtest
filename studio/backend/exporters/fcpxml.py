"""採用中のテイクを上映順に並べ、Premiere Pro に読み込める XML（xmeml v5）と ffmpeg の確認用 ffconcat を書き出す。

e001/e009 の既存の書き出し（V1 カット画像、24fps、1920x1080）と同じ形。
音声トラック・字幕オーバーレイ・After Effects 連携は次の段階で足す。
"""
from pathlib import Path
from urllib.parse import quote
from xml.sax.saxutils import escape

from .. import config


def _rate() -> str:
    return f"<rate><timebase>{config.FPS}</timebase><ntsc>FALSE</ntsc></rate>"


def _pathurl(p: Path) -> str:
    s = p.resolve().as_posix()
    if not s.startswith("/"):
        s = "/" + s                     # C:/... → /C:/...
    return "file://" + quote(s)


def timeline(cuts: list[dict], selected: dict[int, dict]) -> list[dict]:
    """cuts（上映順）と、cut_id→採用テイク から、フレーム単位の並びを作る。採用がないコマは空き（仮カット）にする。"""
    items, frame = [], 0
    for c in cuts:
        dur = max(1, round((c.get("seconds") or 1.0) * config.FPS))
        take = selected.get(c["id"])
        items.append({"cut": c, "take": take, "start": frame, "end": frame + dur})
        frame += dur
    return items


def to_xmeml(name: str, items: list[dict]) -> str:
    total = items[-1]["end"] if items else 0
    clips = []
    for i, it in enumerate(items, start=1):
        take, c = it["take"], it["cut"]
        if not take or not take.get("file_path"):
            continue
        p = config.MEDIA_DIR / take["file_path"]
        dur = it["end"] - it["start"]
        clips.append(f"""
          <clipitem id="clip-{i:03d}">
            <name>{escape(f"{c['cut']} {c['panel']}")}</name>
            <duration>{dur}</duration>{_rate()}
            <start>{it['start']}</start><end>{it['end']}</end><in>0</in><out>{dur}</out>
            <file id="file-{i:03d}">
              <name>{escape(p.name)}</name>
              <pathurl>{_pathurl(p)}</pathurl>
              <duration>{dur}</duration>{_rate()}
              <media><video><samplecharacteristics><width>{config.FRAME_W}</width><height>{config.FRAME_H}</height></samplecharacteristics></video></media>
            </file>
          </clipitem>""")
    return f"""<?xml version="1.0" encoding="utf-8"?>
<xmeml version="5">
  <sequence id="{escape(name)}">
    <name>{escape(name)}</name>
    <duration>{total}</duration>{_rate()}
    <media>
      <video>
        <format><samplecharacteristics><width>{config.FRAME_W}</width><height>{config.FRAME_H}</height><pixelaspectratio>square</pixelaspectratio></samplecharacteristics></format>
        <track>
          <name>V1 採用テイク</name>{''.join(clips)}
        </track>
      </video>
      <audio><track/></audio>
    </media>
  </sequence>
</xmeml>
"""


def to_ffconcat(items: list[dict]) -> str:
    lines = ["ffconcat version 1.0"]
    for it in items:
        take = it["take"]
        if not take or not take.get("file_path"):
            continue
        lines.append(f"file '{(config.MEDIA_DIR / take['file_path']).resolve().as_posix()}'")
        lines.append(f"duration {(it['end'] - it['start']) / config.FPS:.6f}")
    return "\n".join(lines) + "\n"
