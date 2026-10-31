// ---------- 監督の入口：「いま」（工程・読み込んでいるもの・あなたの番）と「決める」（案を並べて見て選ぶ） ----------
// 文章を読ませる前に、まず“やった版”を見せる。案は今の版と左右に並べて同時に再生できる。

// ===== いま =====
async function viewEpHome(code) {
  const o = await api(`/api/episodes/${code}/overview`);
  EP_COUNTS[code] = o.decide_count;
  const ep = o.episode;
  const stIcon = { done: "✓", now: "●", todo: "" };
  $view.innerHTML = `${epTabs(code, "home")}
    <div class="row"><h1 style="margin:0">${h(code)} ${h(ep.title || "")}</h1><span class="muted">目標 ${ep.target_seconds}秒${ep.is_test ? "（テストの回）" : ""}</span></div>
    <div class="steps">${o.steps.map((s, i) => `<a class="step ${s.state}" ${s.link ? `href="${s.link}"` : ""}>
      <div class="sn">${stIcon[s.state] || i + 1}</div><div><b>${h(s.name)}</b>${s.gate ? `<span class="gate">${s.gate}</span>` : ""}
      <div class="small muted">${h(s.detail)}</div></div></a>`).join('<span class="sarrow">›</span>')}</div>
    ${o.flows.length ? `<div class="flows"><span class="small muted">シーンの工程</span>${o.flows.map((f) =>
      `<a class="fl ${f.stage}" href="#/ep/${code}/${f.stage === "director" ? "decide" : f.stage === "done" ? "vcon?scene=" + f.scene : "staff"}" title="${h(f.label)}">
        <b>${h(f.scene)}</b>${f.cycle > 1 ? `<sup>${f.cycle}</sup>` : ""}<span>${h(f.label.replace(/（.*）/, ""))}</span></a>`).join("")}</div>` : ""}
    <div class="homegrid">
      <div>
        <h2>あなたの番 <span class="small muted">上から順にやれば、工程どおりに進みます</span></h2>
        ${o.todo.map((t) => `<a class="todo ${t.kind}" href="${t.link}"><span class="tn">${t.n}</span><span>${h(t.what)}</span><span class="go">開く ›</span></a>`).join("")
          || `<p class="muted">いまはありません。AI が作業中です。</p>`}
        <h2 style="margin-top:22px">AI が作業中</h2>
        ${o.working.map((w) => `<a class="working" href="${w.link}">${h(w.what)}</a>`).join("") || `<p class="small muted">なし（頼むときは「AI に頼む」）</p>`}
      </div>
      <div>
        <h2>読み込んでいるもの <span class="small muted">AI はこれを元に作っています</span></h2>
        <table class="loaded">${o.loaded.map((l) => `<tr class="${l.ok ? "" : "ng"}"><td>${l.ok ? "✓" : "！"}</td><th>${h(l.name)}</th>
          <td>${h(l.value)}${l.path ? `<div class="small muted">${h(l.path)}</div>` : ""}</td></tr>`).join("")}</table>
        <p class="small muted">「！」はまだ入っていないもの。絵がないコマは、Vコンと「決める」で字コンテの文字が出ます。</p>
        <h2 style="margin-top:22px">作業の細かい画面</h2>
        <div class="worklinks">${[["cuts", "コマの一覧（字コンテ）"], ["shots", "ショット分け"], ["edit", "編集（ライブ）"], ["design", "設計（尺の配分）"],
          ["awaiting", "AI が通した絵・動画"], ["questions", "AI からの質問（文章）"]].map(([k, l]) => `<a class="btn" href="#/ep/${code}/${k}">${l}</a>`).join("")}
          <a class="btn" href="#/brief?ep=${code}">AI が読んでいる指示（ブリーフ）</a></div>
      </div>
    </div>`;
}

// ===== アニマティック：絵（なければ字コンテの文字）を秒どおりに並べ、カメラの動きもつけて再生 =====
const MOVE_LABEL = { track_in: "トラックアップ", track_out: "トラックバック", pan_left: "← パン", pan_right: "パン →", tilt_up: "↑ ティルト", tilt_down: "↓ ティルト" };
const STATUS_LABEL = { changed: "変える", new: "足す", dropped: "案では削る" };
function moveTransform(move, p) {
  switch (move) {
    case "track_in": return `scale(${1 + 0.4 * p})`;
    case "track_out": return `scale(${1.4 - 0.4 * p})`;
    case "pan_right": return `scale(1.2) translateX(${7 - 14 * p}%)`;
    case "pan_left": return `scale(1.2) translateX(${-7 + 14 * p}%)`;
    case "tilt_up": return `scale(1.2) translateY(${-7 + 14 * p}%)`;
    case "tilt_down": return `scale(1.2) translateY(${7 - 14 * p}%)`;
    default: return "none";
  }
}
function animatic(el, segs, opts = {}) {
  const total = segs.reduce((s, x) => s + x.seconds, 0) || 1;
  const starts = segs.map((_, k) => segs.slice(0, k).reduce((s, x) => s + x.seconds, 0));
  el.innerHTML = `<div class="anim">
      <div class="astage"><div class="aframe"></div><div class="amove"></div><div class="abadge"></div><div class="asub"></div></div>
      <div class="astrip">${segs.map((s, k) => `<i class="${s.status}" data-k="${k}" style="flex:${s.seconds}" title="${h(s.code)} ${s.seconds}秒 ${h(s.picture)}"></i>`).join("")}<b class="ahead"></b></div>
      <div class="row arow"><button class="aplay">▶</button><span class="atc small muted"></span><span style="flex:1"></span>
        <span class="small"><b>${total.toFixed(1)}秒</b>${opts.label ? `　${h(opts.label)}` : ""}</span></div></div>`;
  const frame = el.querySelector(".aframe"), stage = el.querySelector(".astage");
  let t = 0, cur = -1, playing = false, raf = 0, last = 0;
  const segAt = (tt) => { let k = segs.length - 1; while (k > 0 && starts[k] > tt) k--; return k; };
  const draw = () => {
    const k = segAt(t), s = segs[k];
    if (!s) return;
    const p = Math.min(1, Math.max(0, (t - starts[k]) / (s.seconds || 1)));
    if (k !== cur) {
      cur = k;
      const tk = s.take;
      frame.innerHTML = tk && tk.file_path
        ? (tk.kind === "video" ? `<video src="/media/${encodeURI(tk.file_path)}" muted playsinline></video>` : `<img src="/media/${encodeURI(tk.file_path)}">`)
        : `<div class="acard"><div class="acode">${h(s.code)}</div><div class="apic">${h(s.picture)}</div></div>`;
      const v = frame.querySelector("video");
      if (v) { const go = () => { v.currentTime = (s.offset || 0) + (t - starts[k]); if (playing) v.play().catch(() => {}); };
        v.readyState >= 1 ? go() : v.addEventListener("loadedmetadata", go, { once: true }); }
      el.querySelector(".asub").textContent = s.dialogue || "";
      el.querySelector(".abadge").innerHTML = `${h(s.code)}・${s.seconds}秒${STATUS_LABEL[s.status] ? `<span class="st ${s.status}">${STATUS_LABEL[s.status]}</span>` : ""}`;
      el.querySelector(".amove").textContent = MOVE_LABEL[s.move] || "";
      stage.classList.toggle("dropped", s.status === "dropped");
      el.querySelectorAll(".astrip i").forEach((x) => x.classList.toggle("on", +x.dataset.k === k));
    }
    frame.style.transform = moveTransform(s.move, p);
    el.querySelector(".ahead").style.left = `${(100 * t) / total}%`;
    el.querySelector(".atc").textContent = `${t.toFixed(1)} / ${total.toFixed(1)}秒`;
  };
  const tick = (now) => {
    if (!playing) return;
    t += (now - last) / 1000; last = now;
    if (t >= total) { t = total - 0.001; draw(); pause(); opts.onend && opts.onend(); return; }
    draw(); raf = requestAnimationFrame(tick);
  };
  const play = () => { if (t >= total - 0.01) seek(0); playing = true; last = performance.now(); el.querySelector(".aplay").textContent = "■";
    frame.querySelector("video")?.play().catch(() => {}); raf = requestAnimationFrame(tick); };
  const pause = () => { playing = false; cancelAnimationFrame(raf); el.querySelector(".aplay").textContent = "▶"; frame.querySelector("video")?.pause(); };
  const seek = (tt) => { t = Math.max(0, Math.min(total - 0.001, tt)); cur = -1; draw(); };
  el.querySelector(".aplay").onclick = () => (playing ? pause() : play());
  el.querySelector(".astrip").onclick = (e) => { const r = e.currentTarget.getBoundingClientRect(); seek(((e.clientX - r.left) / r.width) * total); };
  seek(0);
  return { play, pause, seek, total, get playing() { return playing; } };
}

// ===== 決める：AI の案を、今の版と並べて見て選ぶ =====
async function viewDecide(code) {
  const [vs, choices, rounds, fl] = await Promise.all([api(`/api/episodes/${code}/versions`), api(`/api/choices?episode=${code}&status=open`),
    api(`/api/rounds?episode=${code}`), api(`/api/episodes/${code}/flows`)]);
  const atDirector = fl.flows.filter((f) => f.stage === "director");
  const byChoice = {}, single = [];
  vs.forEach((v) => (v.choice_id ? (byChoice[v.choice_id] ||= []).push(v) : single.push(v)));
  const plain = choices.filter((c) => !byChoice[c.id]);
  EP_COUNTS[code] = vs.length + plain.length + atDirector.length;
  const fromRound = (v) => v.round_id ? `<a class="small" href="#/ep/${code}/staff">AI 会議 #${v.round_id} から</a>` : `<span class="small muted">${h(v.made_by)}</span>`;
  const reasons = (v) => v.reasons.length ? `<details class="why"><summary class="small">なぜこの案？（AI たちの見立て）</summary>${v.reasons.map((r) =>
      `<div class="small"><span class="rolechip" style="${roleStyle(r.role)}">${h(r.role)}</span> ${h(r.text)}</div>`).join("")}</details>` : "";
  const decideRow = (id) => `<div class="row decide" data-v="${id}">
      <button class="primary" data-d="adopt">案にする</button><button data-d="keep">今のまま</button>
      <input type="text" placeholder="ちがうときは一言（🎤）　例：寄るのはもっと遅く" class="dnote"><button class="qmic">🎤</button><button data-d="other">ちがう</button>
      <span class="small muted dmsg"></span></div>`;
  $view.innerHTML = `${epTabs(code, "decide")}<h1>決める <span class="muted small">映像を見て OK か指示を出す／AI の案を今の版と並べて選ぶ</span></h1>
    ${atDirector.map((f) => `<div class="card flowcard" data-scene="${h(f.scene)}">
      <div class="row"><span class="badge proposed">${h(f.scene)}</span><b>映像を見て決める</b><span class="small muted">${f.cycle}周目・映像会議 #${f.round?.id} の結論</span>
        <span style="flex:1"></span><a class="small" href="#/ep/${code}/staff">話し合いを見る</a></div>
      <div class="pair"><div class="fplayer"></div>
        <div><div class="concl"><div class="ctitle">AI 会議の結論</div><div class="csum">${h(f.summary?.summary || "")}</div>
          ${(f.summary?.items || []).filter((i) => i.decision !== "drop").map((i) => `<div class="small">・${h(i.text)}</div>`).join("")}</div>
          ${f.views.map((p) => `<div class="small view"><span class="rolechip" style="${roleStyle(p.role)}">${h(p.role)}</span> ${h(p.summary)}</div>`).join("")}</div></div>
      <div class="row"><button class="primary" data-ok>OK（このシーンは完成）</button>
        <input type="text" class="dnote" placeholder="こうしたい（一言・🎤）　例：打ち明けはもっと溜めて。カメラは寄らない"><button class="qmic">🎤</button>
        <button data-redo>この指示で作り直す</button><span class="small muted dmsg"></span></div></div>`).join("")}
    ${single.map((v) => `<div class="card vcard" data-vid="${v.id}">
      <div class="row"><span class="badge proposed">${h(v.scene)}</span><b>${h(v.title)}</b>${fromRound(v)}<span style="flex:1"></span>
        <span class="secs"></span><button class="both">▶ 両方再生</button></div>
      <div class="pair"><div><div class="plabel">今の版</div><div class="pbase"></div></div><div><div class="plabel alt">案</div><div class="palt"></div></div></div>
      <div class="diffs"></div>${v.note ? `<details class="why"><summary class="small">AI のまとめ（文章）</summary><div class="small muted">${h(v.note)}</div></details>` : ""}${reasons(v)}${decideRow(v.id)}</div>`).join("")}
    ${Object.entries(byChoice).map(([cid, list]) => { const c = choices.find((x) => x.id == cid) || {}; return `<div class="card vcard choice2" data-cid="${cid}">
      <div class="row"><span class="badge proposed">${h(list[0].scene)}</span><span class="badge">2択</span><b>${h(c.question || list[0].title)}</b>${fromRound(list[0])}
        <span style="flex:1"></span><button class="both">▶ 両方再生</button></div>
      ${c.why ? `<div class="small muted">割れた理由：${h(c.why)}</div>` : ""}
      <div class="pair">${list.map((v) => `<div data-vid="${v.id}"><div class="plabel alt">${h(v.option)}　${h(v.title)}</div><div class="palt"></div><div class="diffs small"></div>
        <button class="primary pick" data-pick="${v.id}">${h(v.option)} にする</button></div>`).join("")}</div>
      <div class="row"><input type="text" class="dnote" placeholder="一言（任意）"><button class="qmic">🎤</button><span class="small muted dmsg"></span></div></div>`; }).join("")}
    ${plain.length ? `<h2>2択（文章だけ）</h2><div class="card">${plain.map(choiceHTML).join("")}</div>` : ""}
    ${!vs.length && !plain.length && !atDirector.length ? `<p class="muted">いま決めることはありません。${rounds.some((r) => r.status === "open") ? "AI 会議が進行中です。" : ""}</p>` : ""}`;
  bindChoices(document);
  // 映像を見て決める：シーンを今の絵・動画で流す → OK か、一言で作り直し
  for (const card of document.querySelectorAll(".flowcard")) {
    const sc = card.dataset.scene;
    const segs = await api(`/api/episodes/${code}/scenes/${sc}/segments`);
    animatic(card.querySelector(".fplayer"), segs, { label: sc });
    const go = async (verdict) => {
      const note = card.querySelector(".dnote").value.trim();
      if (verdict === "redo" && !note) { card.querySelector(".dmsg").textContent = "どうしたいか、一言ください"; return; }
      await api(`/api/episodes/${code}/flows/${sc}/direct`, { method: "POST", body: { verdict, note } });
      card.classList.add("decided"); card.querySelectorAll("button").forEach((x) => (x.disabled = true));
      card.querySelector(".dmsg").textContent = verdict === "ok" ? "OK にしました" : "伝えました。まとめ役が作り直し、また映像会議にかけます";
    };
    card.querySelector("[data-ok]").onclick = () => go("ok");
    card.querySelector("[data-redo]").onclick = () => go("redo");
  }
  document.querySelectorAll(".qmic").forEach((b) => (b.onclick = () => { b.classList.add("on");
    listen((t) => { b.classList.remove("on"); const inp = b.previousElementSibling; inp.value = (inp.value ? inp.value + " " : "") + t; }); }));

  // 1つの案：今の版と案
  for (const card of document.querySelectorAll(".vcard:not(.choice2)")) {
    const c = await api(`/api/versions/${card.dataset.vid}/compare`);
    const pb = animatic(card.querySelector(".pbase"), c.base, { label: `${c.base.filter((s) => s.status === "dropped").length}コマを案では削る` });
    const pa = animatic(card.querySelector(".palt"), c.alt, {});
    const d = c.alt_seconds - c.base_seconds;
    card.querySelector(".secs").innerHTML = `${c.base_seconds}秒 → <b>${c.alt_seconds}秒</b> <span class="${d < 0 ? "minus" : "plus"}">（${d > 0 ? "+" : ""}${d.toFixed(1)}秒）</span>`;
    // 変わるところ：数を色で（削る／足す／変える）、中身は開いたときだけ
    const kind = (x) => (x.startsWith("削る") ? "dropped" : x.startsWith("足す") ? "new" : "changed");
    const cnt = (k) => c.diff.filter((x) => kind(x) === k).length;
    card.querySelector(".diffs").innerHTML = `<span class="dchip dropped">削る ${cnt("dropped")}</span><span class="dchip new">足す ${cnt("new")}</span>
      <span class="dchip changed">変える ${cnt("changed")}</span><span class="small muted">（帯の色と同じ。帯を押すとそこから再生）</span>
      <details class="why" style="width:100%"><summary class="small">どこが変わるか（${c.diff.length}か所）</summary>
        ${c.diff.map((x) => `<div class="small"><span class="dchip ${kind(x)}">${h(x.split("：")[0])}</span> ${h(x.split("：").slice(1).join("："))}</div>`).join("")}</details>`;
    card.querySelector(".both").onclick = () => { pb.seek(0); pa.seek(0); pb.play(); pa.play(); };
  }
  // 2択：A の版と B の版
  for (const card of document.querySelectorAll(".choice2")) {
    const players = [], cols = [...card.querySelectorAll("[data-vid]")], cs = [];
    for (const col of cols) {
      const c = await api(`/api/versions/${col.dataset.vid}/compare`);
      cs.push(c);
      players.push(animatic(col.querySelector(".palt"), c.alt, { label: `今 ${c.base_seconds}秒 → ${c.alt_seconds}秒` }));
    }
    // A と B でちがうところだけを出す（共通の直しは「共通」にまとめる）
    const shared = cs[0].diff.filter((x) => cs.every((c) => c.diff.includes(x)));
    cols.forEach((col, k) => {
      const own = cs[k].diff.filter((x) => !shared.includes(x));
      col.querySelector(".diffs").innerHTML = `<b>この案だけ：</b>` + (own.map((x) => `<div>${h(x)}</div>`).join("") || "<div class='muted'>（共通の直しだけ）</div>");
    });
    if (shared.length) card.querySelector(".pair").insertAdjacentHTML("afterend",
      `<details class="why"><summary class="small">A・B 共通の直し（${shared.length}か所）</summary>${shared.map((x) => `<div class="small">${h(x)}</div>`).join("")}</details>`);
    card.querySelector(".both").onclick = () => players.forEach((p) => { p.seek(0); p.play(); });
    card.querySelectorAll("[data-pick]").forEach((b) => (b.onclick = async () => {
      await api(`/api/versions/${b.dataset.pick}/decide`, { method: "POST", body: { verdict: "adopt", note: card.querySelector(".dnote").value } });
      card.classList.add("decided"); card.querySelectorAll("button").forEach((x) => (x.disabled = true));
      card.querySelector(".dmsg").textContent = "決めました。選んだものを覚えて、作り直しに回します";
    }));
  }
  document.querySelectorAll(".decide [data-d]").forEach((b) => (b.onclick = async () => {
    const row = b.closest(".decide"), note = row.querySelector(".dnote").value.trim();
    if (b.dataset.d === "other" && !note) { row.querySelector(".dmsg").textContent = "どうちがうか、一言ください"; return; }
    await api(`/api/versions/${row.dataset.v}/decide`, { method: "POST", body: { verdict: b.dataset.d, note } });
    row.closest(".vcard").classList.add("decided"); row.querySelectorAll("button").forEach((x) => (x.disabled = true));
    row.querySelector(".dmsg").textContent = { adopt: "案にしました。AI が字コンテに反映します", keep: "今のままにしました", other: "伝えました。AI が作り直します" }[b.dataset.d];
  }));
}
const ROLE_COLOR = { "芝居": "#e07a7a", "演出": "#7fa6d9", "見る": "#7fc79a", "まとめ": "#f0b45a" };
const roleStyle = (r) => `border-color:${ROLE_COLOR[r] || "#888"};color:${ROLE_COLOR[r] || "#ccc"}`;
