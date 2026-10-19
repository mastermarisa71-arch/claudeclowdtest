// 月灯スタジオ：監督の主画面。並べた仮Vコン・ドラフトを見て、止めて、印をつけて、話して直しを伝える。
// app.js の api / h / media / parseVoice / listen / META / TIER を使う。

const VC = { tool: "arrow", shapes: [], drawing: null };

// ---------- Vコン：見て、止めて、印をつけて、話す ----------
async function viewVcon(code, params) {
  const [plist, marks] = await Promise.all([api(`/api/episodes/${code}/playlist`), api(`/api/episodes/${code}/marks`)]);
  const cuts = plist.map((p) => ({ ...p.cut, _play: p }));
  if (!cuts.length) { $view.innerHTML = `${epTabs(code, "vcon")}<p class="muted">字コンテがまだありません。</p>`; return; }
  const total = cuts.reduce((s, c) => s + (c.seconds || 0), 0) || 1;
  const startOf = (k) => cuts.slice(0, k).reduce((s, c) => s + (c.seconds || 0), 0);
  const marksOf = (c) => marks.filter((m) => m.cut_id === c.id);
  let i = 0;
  if (params.get("cut")) i = Math.max(0, cuts.findIndex((c) => c.id == params.get("cut")));
  if (params.get("scene")) i = Math.max(0, cuts.findIndex((c) => c.scene === params.get("scene")));
  let playing = false, timer = null;
  VC.shapes = [];
  const fmt = (sec) => `${Math.floor(sec / 60)}:${(sec % 60).toFixed(1).padStart(4, "0")}`;
  const sceneStarts = cuts.map((c, k) => (k === 0 || cuts[k - 1].scene !== c.scene ? k : -1)).filter((k) => k >= 0);

  $view.innerHTML = `${epTabs(code, "vcon")}
    <div class="vcon">
      <div>
        <div class="stage vstage" id="mon"></div>
        <div class="row transport">
          <button id="prev" title="前のコマ（←）">◀</button>
          <button class="primary" id="play" title="再生／止める（スペース）">再生</button>
          <button id="next" title="次のコマ（→）">▶</button>
          <span id="tc" class="muted"></span><span style="flex:1"></span>
          <span class="small muted">止めて、画面に描いて、🎤で話す</span>
        </div>
        <div class="vtl" id="tl">${cuts.map((c, k) => {
          const m = marksOf(c), open = m.some((x) => x.created_by === "human" && x.status !== "resolved");
          return `<a data-k="${k}" class="${c._play.take ? "has" : ""} ${open ? "marked" : ""}" style="width:${(100 * (c.seconds || 0.5)) / total}%" title="${h(c.cut + c.panel)}"></a>`;
        }).join("")}</div>
        <div class="scenes">${sceneStarts.map((k) => `<a data-k="${k}" style="left:${(100 * startOf(k)) / total}%">${h(cuts[k].scene)}</a>`).join("")}</div>
      </div>
      <div class="vside">
        <div id="info"></div>
        <div class="card review-box">
          <div class="row"><b>このコマに直しを伝える</b></div>
          <div class="row tools">
            <button data-tool="arrow" title="矢印（A）">➚ 矢印</button>
            <button data-tool="box" title="囲み（B）">▢ 囲み</button>
            <button id="undo" title="最後の印を消す">↶ 消す</button>
          </div>
          <button class="bigmic" id="talk">🎤 話して伝える</button>
          <textarea id="vtext" data-mic="1" placeholder="例：あかねはもっと右、扉の前まで。表情はもっと不安げに"></textarea>
          <div class="row" style="margin-top:6px">
            <button class="primary" id="sendFix">直してほしい</button>
            <button id="sendGood">このままで良い</button>
          </div>
          <div class="small muted" id="sent"></div>
        </div>
        <div id="history"></div>
      </div>
    </div>`;

  const mon = document.getElementById("mon");
  const show = async () => {
    const c = cuts[i], t = c._play.take;
    VC.shapes = [];
    mon.innerHTML = (t ? media(t) : `<div class="placeholder card-ph"><div class="small muted">まだ絵がありません（仮Vコン待ち）</div>
        <div class="ph-pic">${h(c.picture)}</div>${c.dialogue ? `<div class="ph-dia">${h(c.dialogue)}</div>` : ""}</div>`)
      + `<canvas id="draw"></canvas>`;
    document.getElementById("tc").textContent = `${c.cut}${c.panel}　${c.scene}　${fmt(startOf(i))} / ${fmt(total)}${t ? `　${TIER[t.tier] || ""}` : ""}`;
    document.querySelectorAll("#tl a").forEach((a) => a.classList.toggle("now", +a.dataset.k === i));
    const vid = mon.querySelector("video");
    if (vid) {
      vid.muted = true; vid.controls = false;
      const seek = () => { vid.currentTime = c._play.offset || 0; if (playing) vid.play().catch(() => {}); };
      vid.readyState >= 1 ? seek() : vid.addEventListener("loadedmetadata", seek, { once: true });
    }
    bindCanvas(); redraw();
    // 右側：このコマで何が起きるか（台詞・画面）と、脚本の該当箇所
    const sc = await api(`/api/cuts/${c.id}/script`).catch(() => ({ found: false }));
    document.getElementById("info").innerHTML = `
      <div class="card info">
        <div class="row"><b>${h(c.cut)}${h(c.panel)}</b><span class="muted small">${h(c.scene)}・${c.seconds ?? "-"}秒</span><span style="flex:1"></span>
          <a class="small" href="#/cut/${c.id}?ep=${code}">テイクを並べる</a></div>
        ${c.dialogue ? `<div class="dia">${h(c.dialogue)}</div>` : ""}
        <div class="pic">${h(c.picture)}</div>
        ${c.intent ? `<div class="small muted">ねらい：${h(c.intent)}</div>` : ""}
        ${sc.found ? `<details open><summary class="small muted">脚本：${h(sc.heading)}</summary>
          <div class="script">${sc.lines.map((l) => `<div class="${l.hit ? "hit" : ""}">${h(l.text)}</div>`).join("")}</div></details>` : ""}
      </div>`;
    const ms = marksOf(c);
    document.getElementById("history").innerHTML = ms.length ? `<div class="small muted">このコマへのレビュー</div>` + ms.map((m) => `
      <div class="review ${m.status}"><div class="row">${m.created_by === "agent" ? `<span class="badge proposed">AI</span>` : ""}<b>${h(m.verdict)}</b>
        <span class="badge">${h(m.status)}</span></div>
        ${m.attachment ? `<img class="mark-img" src="/media/${encodeURI(m.attachment)}">` : ""}
        <div>${h(m.comment)}</div>${m.agent_response ? `<div class="agent small">AI：${h(m.agent_response)}</div>` : ""}</div>`).join("") : "";
  };

  // ---- 描く ----
  function bindCanvas() {
    const cv = document.getElementById("draw");
    const fit = () => { cv.width = mon.clientWidth; cv.height = mon.clientHeight; redraw(); };
    fit(); new ResizeObserver(fit).observe(mon);
    const pos = (e) => { const r = cv.getBoundingClientRect(); return [(e.clientX - r.left) / r.width, (e.clientY - r.top) / r.height]; };
    cv.onpointerdown = (e) => { stop(); const [x, y] = pos(e); VC.drawing = { type: VC.tool, x1: x, y1: y, x2: x, y2: y }; cv.setPointerCapture(e.pointerId); };
    cv.onpointermove = (e) => { if (!VC.drawing) return; const [x, y] = pos(e); VC.drawing.x2 = x; VC.drawing.y2 = y; redraw(); };
    cv.onpointerup = () => {
      const d = VC.drawing; VC.drawing = null;
      if (!d || Math.hypot(d.x2 - d.x1, d.y2 - d.y1) < 0.01) return redraw();
      VC.shapes.push(d.type === "box" ? { type: "box", x: Math.min(d.x1, d.x2), y: Math.min(d.y1, d.y2), w: Math.abs(d.x2 - d.x1), h: Math.abs(d.y2 - d.y1) } : d);
      redraw();
    };
  }
  function paint(ctx, W, H, shapes, color, lw) {
    ctx.strokeStyle = color; ctx.fillStyle = color; ctx.lineWidth = lw; ctx.lineCap = "round";
    for (const s of shapes) {
      if (s.type === "box") { ctx.strokeRect(s.x * W, s.y * H, s.w * W, s.h * H); continue; }
      const x1 = s.x1 * W, y1 = s.y1 * H, x2 = s.x2 * W, y2 = s.y2 * H, a = Math.atan2(y2 - y1, x2 - x1), L = 8 + lw * 3;
      ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(x2, y2); ctx.lineTo(x2 - L * Math.cos(a - 0.45), y2 - L * Math.sin(a - 0.45));
      ctx.lineTo(x2 - L * Math.cos(a + 0.45), y2 - L * Math.sin(a + 0.45)); ctx.closePath(); ctx.fill();
    }
  }
  function redraw() {
    const cv = document.getElementById("draw"); if (!cv) return;
    const ctx = cv.getContext("2d"); ctx.clearRect(0, 0, cv.width, cv.height);
    // 前に送った印（このコマのもの）は薄く
    for (const m of marksOf(cuts[i])) {
      try { const g = JSON.parse(m.region_json || "{}"); paint(ctx, cv.width, cv.height, g.shapes || [], "rgba(240,180,90,.35)", 2); } catch (e) {}
    }
    paint(ctx, cv.width, cv.height, VC.shapes.concat(VC.drawing ? [VC.drawing.type === "box"
      ? { type: "box", x: Math.min(VC.drawing.x1, VC.drawing.x2), y: Math.min(VC.drawing.y1, VC.drawing.y2), w: Math.abs(VC.drawing.x2 - VC.drawing.x1), h: Math.abs(VC.drawing.y2 - VC.drawing.y1) }
      : VC.drawing] : []), "#ff5a5a", 4);
  }
  // 印を描いたまま止めた画面を1枚の絵にする（エージェントが見る）
  function snapshot() {
    const W = 960, H = 540, cv = document.createElement("canvas"); cv.width = W; cv.height = H;
    const ctx = cv.getContext("2d"), c = cuts[i];
    ctx.fillStyle = "#222"; ctx.fillRect(0, 0, W, H);
    const src = mon.querySelector("img, video");
    try { if (src) ctx.drawImage(src, 0, 0, W, H); } catch (e) {}
    if (!src) { ctx.fillStyle = "#bbb"; ctx.font = "22px sans-serif"; wrap(ctx, c.picture || "", 40, 80, W - 80, 32); }
    paint(ctx, W, H, VC.shapes, "#ff3b3b", 6);
    ctx.fillStyle = "rgba(0,0,0,.6)"; ctx.fillRect(0, 0, 220, 34); ctx.fillStyle = "#fff"; ctx.font = "18px sans-serif";
    ctx.fillText(`${c.cut}${c.panel}`, 10, 24);
    return cv.toDataURL("image/png");
  }
  function wrap(ctx, text, x, y, w, lh) {
    let line = "";
    for (const ch of text) { if (ctx.measureText(line + ch).width > w) { ctx.fillText(line, x, y); y += lh; line = ch; } else line += ch; }
    ctx.fillText(line, x, y);
  }

  // ---- 送る ----
  async function send(defaultVerdict) {
    const c = cuts[i], t = c._play.take, text = document.getElementById("vtext").value.trim();
    if (defaultVerdict === "修正" && !text && !VC.shapes.length) { document.getElementById("sent").textContent = "印を描くか、話すか、書いてください"; return; }
    const v = parseVoice(text);
    const vid = mon.querySelector("video");
    const region = { t: vid ? Math.max(0, vid.currentTime - (c._play.offset || 0)) : 0, shapes: VC.shapes };
    await api("/api/reviews", { method: "POST", body: {
      target_type: t ? "take" : "cut", target_id: t ? t.id : c.id, verdict: v.verdict || defaultVerdict, tags: v.tags,
      comment: v.verdict ? v.comment : text, region, image: VC.shapes.length || text ? snapshot() : null } });
    marks.push({ cut_id: c.id, verdict: v.verdict || defaultVerdict, status: "open", comment: text, region_json: JSON.stringify(region), created_by: "human" });
    document.getElementById("vtext").value = ""; VC.shapes = [];
    document.getElementById("sent").textContent = `${c.cut}${c.panel} に送りました。エージェントが次に読みます`;
    document.querySelector(`#tl a[data-k="${i}"]`)?.classList.add("marked");
    show();
  }

  // ---- 再生 ----
  const step = () => { if (i < cuts.length - 1) { i++; show(); timer = setTimeout(step, (cuts[i].seconds || 1) * 1000); } else stop(); };
  function stop() { playing = false; clearTimeout(timer); mon.querySelector("video")?.pause(); const b = document.getElementById("play"); if (b) b.textContent = "再生"; }
  function play() { playing = true; document.getElementById("play").textContent = "止める"; mon.querySelector("video")?.play().catch(() => {}); timer = setTimeout(step, (cuts[i].seconds || 1) * 1000); }
  const go = (k) => { stop(); i = Math.min(cuts.length - 1, Math.max(0, k)); show(); };
  document.getElementById("play").onclick = () => (playing ? stop() : play());
  document.getElementById("prev").onclick = () => go(i - 1);
  document.getElementById("next").onclick = () => go(i + 1);
  document.querySelectorAll("#tl a, .scenes a").forEach((a) => (a.onclick = () => go(+a.dataset.k)));
  document.querySelectorAll("[data-tool]").forEach((b) => (b.onclick = () => { VC.tool = b.dataset.tool; document.querySelectorAll("[data-tool]").forEach((x) => x.classList.toggle("on", x === b)); }));
  document.querySelector(`[data-tool="${VC.tool}"]`).classList.add("on");
  document.getElementById("undo").onclick = () => { VC.shapes.pop(); redraw(); };
  document.getElementById("sendFix").onclick = () => send("修正");
  document.getElementById("sendGood").onclick = () => send("良い");
  const talk = document.getElementById("talk");
  talk.onclick = () => { stop(); talk.classList.add("on"); talk.textContent = "🎤 聞いています…";
    listen((txt) => { talk.classList.remove("on"); talk.textContent = "🎤 話して伝える";
      const ta = document.getElementById("vtext"); ta.value = (ta.value ? ta.value + " " : "") + txt; }); };
  document.onkeydown = (e) => {
    if (!location.hash.match(/^#\/ep\/[^/?]+(\?|$)/) || ["TEXTAREA", "INPUT"].includes(e.target.tagName)) return;
    if (e.key === " ") { e.preventDefault(); playing ? stop() : play(); }
    if (e.key === "ArrowLeft") go(i - 1);
    if (e.key === "ArrowRight") go(i + 1);
    if (e.key === "a") document.querySelector('[data-tool="arrow"]').click();
    if (e.key === "b") document.querySelector('[data-tool="box"]').click();
    if (e.key === "m") talk.click();
  };
  show();
}

// ---------- AIからの質問：項目ごとに「それでいい／ちがう」で答える ----------
async function viewQuestions(code) {
  const list = (await api(`/api/reviews?episode=${code}&status=proposed,open,working&by=agent`)).filter((r) => r.agent_response || r.comment);
  const items = (text) => {
    const parts = String(text || "").split(/(?=[①②③④⑤⑥⑦⑧⑨⑩])/).map((s) => s.trim()).filter(Boolean);
    const head = parts.length > 1 && !/^[①-⑩]/.test(parts[0]) ? parts.shift() : "";
    return { head, parts };
  };
  const sceneLinks = (t) => h(t).replace(/\b(S\d{1,2})\b/g, `<a href="#/ep/${code}?scene=$1">$1</a>`);
  $view.innerHTML = `${epTabs(code, "questions")}<h1>AIからの質問 <span class="muted small">項目ごとに答えて、最後に「返事を送る」。シーン名を押すと、そこから Vコンが開きます</span></h1>
    ${list.map((r) => { const it = items(r.agent_response || r.comment); return `<div class="card q" data-q="${r.id}">
      <div class="row"><b>${h(r.comment)}</b><span class="muted small">#${r.id}</span></div>
      ${it.head ? `<p class="small muted">${sceneLinks(it.head)}</p>` : ""}
      ${(it.parts.length ? it.parts : [r.agent_response]).map((p, k) => `<div class="qitem" data-k="${k}">
        <div class="qtext">${sceneLinks(p)}</div>
        <div class="row"><button data-ans="ok">それでいい</button><button data-ans="ng">ちがう</button>
          <input type="text" placeholder="どうしたいか（任意）"><button class="qmic" title="話して入力">🎤</button></div></div>`).join("")}
      <div class="row" style="margin-top:8px"><button class="primary" data-send="${r.id}">返事を送る</button><span class="small muted" data-done="${r.id}"></span></div>
    </div>`; }).join("") || `<p class="muted">いま AI からの質問はありません。</p>`}`;
  document.querySelectorAll(".qitem [data-ans]").forEach((b) => (b.onclick = () => {
    b.parentElement.querySelectorAll("[data-ans]").forEach((x) => x.classList.toggle("on", x === b));
    b.closest(".qitem").dataset.ans = b.dataset.ans;
  }));
  document.querySelectorAll(".qmic").forEach((b) => (b.onclick = () => { b.classList.add("on");
    listen((t) => { b.classList.remove("on"); const inp = b.previousElementSibling; inp.value = (inp.value ? inp.value + " " : "") + t; }); }));
  document.querySelectorAll("[data-send]").forEach((b) => (b.onclick = async () => {
    const r = list.find((x) => x.id == b.dataset.send), card = b.closest(".q");
    const ans = [...card.querySelectorAll(".qitem")].map((q) => {
      const mark = (q.querySelector(".qtext").textContent.match(/^[①-⑩]/) || [""])[0];
      const a = q.dataset.ans === "ok" ? "それでいい" : q.dataset.ans === "ng" ? "ちがう" : "（未回答）";
      const note = q.querySelector("input").value.trim();
      return `${mark}${a}${note ? "：" + note : ""}`;
    });
    const allOk = [...card.querySelectorAll(".qitem")].every((q) => q.dataset.ans === "ok");
    await api("/api/reviews", { method: "POST", body: { target_type: r.target_type, target_id: r.target_id,
      verdict: allOk ? "良い" : "修正", tags: (r.tags || "").split(",").filter(Boolean), comment: `（#${r.id} への返事）${ans.join("／")}` } });
    await api(`/api/reviews/${r.id}`, { method: "PATCH", body: { status: "resolved" } });
    card.querySelector(`[data-done="${r.id}"]`).textContent = "送りました。エージェントが次に読みます";
    b.disabled = true;
  }));
}
