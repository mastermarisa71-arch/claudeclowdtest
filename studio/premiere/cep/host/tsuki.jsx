// 月灯スタジオ ⇄ Premiere Pro（ExtendScript）。パネル（index.html）から evalScript で呼ばれる。
// 入力・出力は文字列の JSON。ExtendScript には JSON がない版もあるので、ここで小さく持つ。

function tsukiStringify(v) {
  if (v === null || v === undefined) return "null";
  var t = typeof v;
  if (t === "number" || t === "boolean") return String(v);
  if (t === "string") return '"' + v.replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/\n/g, "\\n") + '"';
  if (v instanceof Array) {
    var a = [];
    for (var i = 0; i < v.length; i++) a.push(tsukiStringify(v[i]));
    return "[" + a.join(",") + "]";
  }
  var o = [];
  for (var k in v) if (v.hasOwnProperty(k)) o.push(tsukiStringify(k) + ":" + tsukiStringify(v[k]));
  return "{" + o.join(",") + "}";
}

function tsukiParse(s) { return eval("(" + s + ")"); }

function tsukiTime(sec) { var t = new Time(); t.seconds = sec; return t; }

function tsukiBin(name) {
  var root = app.project.rootItem;
  for (var i = 0; i < root.children.numItems; i++) {
    if (root.children[i].name === name) return root.children[i];
  }
  return root.createBin(name);
}

function tsukiFindItem(bin, path) {
  var norm = function (p) { return String(p).replace(/\\/g, "/").toLowerCase(); };
  for (var i = 0; i < bin.children.numItems; i++) {
    var it = bin.children[i];
    if (it.getMediaPath && norm(it.getMediaPath()) === norm(path)) return it;
  }
  return null;
}

function tsukiImport(bin, paths) {
  var need = [];
  for (var i = 0; i < paths.length; i++) if (!tsukiFindItem(bin, paths[i])) need.push(paths[i]);
  if (need.length) app.project.importFiles(need, true, bin, false);
}

// シーケンスを組む：args = {sequence, fps, video:[{name,path,start,duration,mute}], audio:[{name,track,path,start}]}
function tsukiBuild(args) {
  var bin = tsukiBin("月灯スタジオ");
  var paths = [], i;
  for (i = 0; i < args.video.length; i++) paths.push(args.video[i].path);
  for (i = 0; i < args.audio.length; i++) paths.push(args.audio[i].path);
  tsukiImport(bin, paths);

  var seq = app.project.createNewSequence(args.sequence + "_" + (new Date()).getTime(), "tsuki");
  var st = seq.getSettings();
  st.videoFrameWidth = 1920; st.videoFrameHeight = 1080;
  seq.setSettings(st);

  var placed = 0;
  for (i = 0; i < args.video.length; i++) {
    var v = args.video[i], item = tsukiFindItem(bin, v.path);
    if (!item) continue;
    seq.videoTracks[0].overwriteClip(item, v.start);
    var clips = seq.videoTracks[0].clips;
    var c = clips[clips.numItems - 1];
    c.end = tsukiTime(v.start + v.duration);
    c.name = v.name;
    placed++;
  }
  // 声・効果音・劇伴は A2 以降。A1（Seedance の音）は切っておく
  var trackOf = { "A1 声": 1, "A2 効果音": 2, "A3 劇伴": 3 };
  for (i = 0; i < args.audio.length; i++) {
    var a = args.audio[i], aitem = tsukiFindItem(bin, a.path);
    var n = trackOf[a.track] || 1;
    if (aitem && seq.audioTracks.numTracks > n) seq.audioTracks[n].overwriteClip(aitem, a.start);
  }
  if (seq.audioTracks.numTracks > 0) seq.audioTracks[0].setMute(1);
  return tsukiStringify({ sequence: seq.name, placed: placed });
}

// 今のタイムライン（監督の手直しを含む）を読む
function tsukiRead() {
  var seq = app.project.activeSequence;
  if (!seq) return tsukiStringify({ error: "アクティブなシーケンスがありません" });
  var out = { sequence: seq.name, video: [], audio: [] }, t, j;
  for (t = 0; t < seq.videoTracks.numTracks; t++) {
    var vt = seq.videoTracks[t];
    for (j = 0; j < vt.clips.numItems; j++) {
      var c = vt.clips[j];
      out.video.push({ track: t + 1, name: c.name, start: c.start.seconds, end: c.end.seconds,
                       inPoint: c.inPoint.seconds, outPoint: c.outPoint.seconds,
                       path: c.projectItem ? c.projectItem.getMediaPath() : "" });
    }
  }
  for (t = 0; t < seq.audioTracks.numTracks; t++) {
    var at = seq.audioTracks[t];
    for (j = 0; j < at.clips.numItems; j++) {
      var a = at.clips[j];
      out.audio.push({ track: t + 1, name: a.name, start: a.start.seconds, end: a.end.seconds,
                       path: a.projectItem ? a.projectItem.getMediaPath() : "" });
    }
  }
  return tsukiStringify(out);
}

// クリップの差し替え：args = {name, path}（同じ名前のクリップを、同じ位置・長さで新しいテイクに）
function tsukiReplace(args) {
  var seq = app.project.activeSequence, bin = tsukiBin("月灯スタジオ");
  tsukiImport(bin, [args.path]);
  var item = tsukiFindItem(bin, args.path), vt = seq.videoTracks[0];
  for (var j = 0; j < vt.clips.numItems; j++) {
    var c = vt.clips[j];
    if (c.name === args.name) {
      var s = c.start.seconds, e = c.end.seconds;
      vt.overwriteClip(item, s);
      var nc = vt.clips[j];
      nc.end = tsukiTime(e); nc.name = args.name;
      return tsukiStringify({ replaced: args.name, start: s, end: e });
    }
  }
  return tsukiStringify({ error: "クリップがありません: " + args.name });
}

// マーカー：args = {at, name, comment}（エージェントのメモや、監督への質問を置く）
function tsukiMarker(args) {
  var m = app.project.activeSequence.markers.createMarker(args.at);
  m.name = args.name || "AI";
  m.comments = args.comment || "";
  return tsukiStringify({ marker: m.name });
}

// ---------- After Effects ----------
// コンポを作る：args = {name, path, duration, fps, texts:[{text,x,y,size,t_in,t_out}], zoom:{from,to,t0,t1}, render, out, take}
// 黒板・メモの文字合成、編集での小さな寄り引き、書き出しをエージェントが下ごしらえし、監督が AE の画面で仕上げる。
function aeComp(args) {
  app.beginUndoGroup("月灯スタジオ");
  var item = app.project.importFile(new ImportOptions(new File(args.path)));
  var comp = app.project.items.addComp(args.name, 1920, 1080, 1, args.duration, args.fps);
  var L = comp.layers.add(item);
  var base = 100 * 1920 / item.width;
  L.property("Scale").setValue([base, base]);
  if (args.zoom && args.zoom.to) {
    var sc = L.property("Scale"), z0 = base * (args.zoom.from || 1), z1 = base * args.zoom.to;
    sc.setValueAtTime(args.zoom.t0 || 0, [z0, z0]);
    sc.setValueAtTime(args.zoom.t1 || args.duration, [z1, z1]);
  }
  for (var i = 0; i < (args.texts || []).length; i++) {
    var tx = args.texts[i], T = comp.layers.addText(tx.text);
    var src = T.property("Source Text"), doc = src.value;
    doc.fontSize = tx.size || 48; doc.fillColor = tx.color || [1, 1, 1];
    src.setValue(doc);
    T.property("Position").setValue([(tx.x || 0.5) * 1920, (tx.y || 0.5) * 1080]);
    T.inPoint = tx.t_in || 0; T.outPoint = tx.t_out || args.duration;
    T.name = "AI文字: " + tx.text;
  }
  app.endUndoGroup();
  comp.openInViewer();
  var res = { comp: comp.name, layers: comp.numLayers };
  if (args.render) {
    var rq = app.project.renderQueue.items.add(comp);
    rq.outputModule(1).file = new File(args.out);
    app.project.renderQueue.render();
    res.rendered = args.out; res.take = args.take;
  }
  return tsukiStringify(res);
}

// 今のコンポ（監督の手直しを含む）を読む
function aeRead() {
  var comp = app.project.activeItem;
  if (!comp || !(comp instanceof CompItem)) return tsukiStringify({ error: "コンポを開いてください" });
  var out = { comp: comp.name, duration: comp.duration, video: [] };
  for (var i = 1; i <= comp.numLayers; i++) {
    var l = comp.layer(i), o = { name: l.name, start: l.inPoint, end: l.outPoint };
    try { if (l.property("Source Text")) o.text = String(l.property("Source Text").value.text); } catch (e) {}
    out.video.push(o);
  }
  return tsukiStringify(out);
}

// 動作確認：アプリと版、開いているプロジェクト
function tsukiHello() {
  var proj = "";
  try { proj = BridgeTalk.appName === "aftereffects" ? (app.project.file ? app.project.file.name : "（未保存）") : app.project.name; } catch (e) {}
  return tsukiStringify({ app: BridgeTalk.appName, version: String(app.version), project: proj });
}

function tsukiRun(cmdJson) {
  try {
    var cmd = tsukiParse(cmdJson);
    if (cmd.command === "hello") return tsukiHello();
    if (BridgeTalk.appName === "aftereffects") {
      if (cmd.command === "comp") return aeComp(cmd.args);
      if (cmd.command === "read") return aeRead();
      return tsukiStringify({ error: "After Effects では使えない命令: " + cmd.command });
    }
    if (cmd.command === "build") return tsukiBuild(cmd.args);
    if (cmd.command === "read") return tsukiRead();
    if (cmd.command === "replace") return tsukiReplace(cmd.args);
    if (cmd.command === "marker") return tsukiMarker(cmd.args);
    return tsukiStringify({ error: "知らない命令: " + cmd.command });
  } catch (e) {
    return tsukiStringify({ error: String(e) });
  }
}
