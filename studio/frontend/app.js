// 月灯スタジオ：レビュー画面。ビルド不要の素の JS。
const $view = document.getElementById("view");
const STAGES = ["脚本", "設計", "字コンテ", "プロンプト", "生成", "編集", "完成"];
const AXES = ["意図", "構図", "配置・左右", "芝居", "表情", "キャラ崩れ", "光・色"];
let META = { tags: [], verdicts: [], providers: {} };

const h = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const api = async (path, opts = {}) => {
  const res = await fetch(path, {
    headers: opts.body && !(opts.body instanceof FormData) ? { "Content-Type": "application/json" } : {},
    ...opts,
    body: opts.body && !(opts.body instanceof FormData) ? JSON.stringify(opts.body) : opts.body,
  });
  if (!res.ok) throw new Error(await res.text());
  return (res.headers.get("content-type") || "").includes("json") ? res.json() : res.text();
};
const media = (t, cls = "") => {
  if (!t || !t.file_path) return `<div class="placeholder ${cls}">${t ? h(t.status) : "テイクなし"}</div>`;
  const src = `/media/${encodeURI(t.file_path)}`;
  if (t.kind === "video") return `<video src="${src}" controls loop muted></video>`;
  if (t.kind === "audio") return `<audio src="${src}" controls></audio>`;
  return `<img src="${src}" alt="">`;
};
const thumb = (t) => `<a class="thumb ${t.selected ? "sel" : ""}" href="#/cut/${t.cut_id}?take=${t.id}" title="#${t.id} ${h(t.provider)} ${h(t.status)}">
  ${t.file_path ? media(t) : h(t.status)}<span class="n">#${t.id}${t.open_reviews ? " ●" : ""}</span>${tierBadge(t)}</a>`;
const TIER = { draft: "480p", upscale: "拡大", final: "1080p", board: "仮Vコン" };
const tierBadge = (t) => (t.tier ? `<span class="tier ${t.tier}">${TIER[t.tier] || h(t.tier)}</span>` : "");

// ---------- 話数一覧 ----------
async function viewHome() {
  const eps = await api("/api/episodes");
  $view.innerHTML = `<h1>話数</h1>
    <p class="muted">エージェントが作ったものに、ここでレビューをつけます。未対応のレビューはエージェントが次の作業で読みます。</p>
    <div class="grid">${eps.map((e) => {
      const i = STAGES.indexOf(e.stage);
      return `<a class="card" href="#/ep/${e.code}"><h3>${h(e.code)} <span class="muted small">${h(e.title)}</span></h3>
        <div class="pipeline">${STAGES.map((s, j) => `<span class="${j < i ? "done" : j === i ? "now" : ""}">${s}</span>`).join("")}</div>
        <span class="stat">コマ <b>${e.n_cuts}</b></span><span class="stat">尺 <b>${e.seconds}</b>/${e.target_seconds}秒</span><br>
        <span class="stat">採用 <b>${e.n_selected}</b>/${e.n_cuts}</span><span class="stat">テイク <b>${e.n_takes}</b></span>
        ${e.n_open ? `<span class="badge open">未対応 ${e.n_open}</span>` : ""}${e.n_proposed ? `<span class="badge proposed">確認待ち ${e.n_proposed}</span>` : ""}
      </a>`;
    }).join("") || `<p class="muted">まだ話数がありません。<code>python studio/cli.py import-jikonte EP09 e009/EP09_字コンテ_4分版.xlsx</code></p>`}</div>`;
}

// ---------- 1話のコマ一覧 ----------
async function viewEpisode(code) {
  const { episode, cuts } = await api(`/api/episodes/${code}/cuts`);
  const total = cuts.reduce((s, c) => s + (c.seconds || 0), 0) || 1;
  const state = (c) => c.takes.some((t) => t.open_reviews) ? "open" : c.takes.some((t) => t.selected) ? "sel" : c.takes.length ? "has" : "";
  let scene = "";
  const rows = cuts.map((c) => {
    const head = c.scene !== scene ? ((scene = c.scene), `<tr class="scene"><td colspan="6">${h(c.scene)}</td></tr>`) : "";
    return `${head}<tr id="c${c.id}">
      <td><a href="#/cut/${c.id}?ep=${code}">${h(c.cut)}${h(c.panel)}</a><div class="muted small">${c.seconds ?? "-"}秒 ${h(c.camera_pos)} ${h(c.look)}</div></td>
      <td>${h(c.picture)}<div class="muted small">${h(c.camerawork)}</div></td>
      <td>${h(c.dialogue)}</td>
      <td class="small muted">${h(c.intent)}</td>
      <td><div class="thumbs">${c.takes.map(thumb).join("") || `<span class="muted small">—</span>`}</div></td></tr>`;
  }).join("");
  $view.innerHTML = `${epTabs(code, "cuts")}<div class="row"><h1>${h(episode.code)} ${h(episode.title)}</h1>
      <span class="muted">${cuts.length}コマ / ${total.toFixed(1)}秒（目標 ${episode.target_seconds}秒）</span>
      <span style="flex:1"></span><button id="export">Premiere 用 XML を書き出す</button></div>
    <div class="legend small muted"><span><i style="background:#3b3340"></i>テイクなし</span><span><i style="background:var(--blue)"></i>テイクあり</span>
      <span><i style="background:var(--green)"></i>採用済み</span><span><i style="background:var(--red)"></i>未対応レビュー</span></div>
    <div class="strip">${cuts.map((c) => `<a class="${state(c)}" style="width:${(100 * (c.seconds || 0.5)) / total}%" href="#/cut/${c.id}?ep=${code}" title="${h(c.cut + c.panel)} ${h(c.dialogue)}"></a>`).join("")}</div>
    <table class="cuts"><tr><th>カット</th><th>画面</th><th>台詞</th><th>演出意図</th><th>テイク</th></tr>${rows}</table>`;
  document.getElementById("export").onclick = async () => {
    const r = await api(`/api/episodes/${code}/export`, { method: "POST" });
    alert(`書き出しました\n${r.xml}\n未採用 ${r.missing.length}コマ`);
  };
}

// ---------- 1コマ：見る・印をつける・レビューする ----------
async function viewCut(id, params) {
  const d = await api(`/api/cuts/${id}`);
  const { cut, takes, reviews } = d;
  let cur = takes.find((t) => t.id == params.get("take")) || takes.find((t) => t.selected) || takes[0];
  let region = null, verdict = "修正", tags = new Set();
  const compareSet = new Set();

  const fields = [["カメラ位置", cut.camera_pos], ["画面配置", cut.layout], ["カメラワーク", cut.camerawork], ["動画化", cut.to_video],
    ["画面", cut.picture], ["芝居", cut.acting], ["表情・感情", cut.emotion], ["台詞", cut.dialogue], ["音", cut.sound],
    ["演出意図", cut.intent], ["編集メモ", cut.edit_memo]].filter(([, v]) => v);
  const reviewsFor = (t) => reviews.filter((r) => (r.target_type === "take" && r.target_id === t?.id));
  const cutReviews = reviews.filter((r) => r.target_type === "cut");

  const renderReview = (r) => `<div class="review ${r.status}">
      <div class="row"><b>${h(r.verdict)}</b><span class="badge ${r.status === "proposed" ? "proposed" : r.status === "resolved" ? "sel" : "open"}">${h(r.status)}</span>
      <span class="small muted">${h(r.tags)}</span><span class="small muted">#${r.id}</span></div>
      <div>${h(r.comment)}</div>
      ${r.agent_response ? `<div class="agent small">エージェント：${h(r.agent_response)}${r.resolved_by_take_id ? ` → <a href="#/cut/${cut.id}?take=${r.resolved_by_take_id}">#${r.resolved_by_take_id}</a>` : ""}</div>` : ""}
      ${r.status === "proposed" ? `<div class="row" style="margin-top:4px"><button data-res="${r.id}" data-st="resolved">直った</button><button data-res="${r.id}" data-st="open">まだ</button></div>` : ""}
    </div>`;

  const draw = () => {
    const boxes = reviewsFor(cur).filter((r) => r.region_json && r.region_json.includes('"x"')).map((r) => {
      const g = JSON.parse(r.region_json);
      return `<div class="box" style="left:${g.x * 100}%;top:${g.y * 100}%;width:${g.w * 100}%;height:${g.h * 100}%"><span class="lbl">#${r.id}</span></div>`;
    }).join("");
    $view.innerHTML = `<div class="row"><a href="#/ep/${h(params.get("ep") || "")}" id="back">← 一覧</a>
        <h1>${h(cut.cut)}${h(cut.panel)} <span class="muted small">${cut.seconds ?? "-"}秒 / ${h(cut.scene)}</span></h1></div>
      <div class="cutview">
        <div class="card spec"><h2 style="margin-top:0">字コンテ</h2><dl>${fields.map(([k, v]) => `<dt>${k}</dt><dd>${h(v)}</dd>`).join("")}</dl>
          <h2>このコマへのレビュー</h2>${cutReviews.map(renderReview).join("") || `<p class="muted small">なし</p>`}</div>
        <div>
          <div class="stage" id="stage">${media(cur)}${cur?.file_path ? "" : `<div class="placeholder">${h(cut.picture)}</div>`}${boxes}<div id="drag"></div></div>
          <p class="small muted">画像の上をドラッグすると、直してほしい範囲に印をつけられます。動画は再生位置がレビューに入ります。</p>
          <h2>テイク（新しい順）　<span class="small">チェックして並べて比較</span></h2>
          <div class="thumbs">${takes.map((t) => `<div><a class="thumb ${t.selected ? "sel" : ""}" href="#/cut/${cut.id}?take=${t.id}&ep=${h(params.get("ep") || "")}"
              style="${t.id === cur?.id ? "outline:2px solid var(--amber)" : ""}">${t.file_path ? media(t) : h(t.status)}<span class="n">#${t.id}</span>${tierBadge(t)}</a>
              <label class="small"><input type="checkbox" data-cmp="${t.id}"> 比較</label></div>`).join("") || `<p class="muted">まだテイクがありません。</p>`}</div>
          <div class="row" style="margin-top:8px"><button id="cmp">選んだテイクを並べる</button>
            <label class="btn">自分で作ったものを足す<input type="file" id="up" hidden></label></div>
          ${cur ? `<h2>テイク #${cur.id} の作り方</h2>
            <div class="small muted">${cur.tier ? `<b>${TIER[cur.tier] || h(cur.tier)}</b> / ` : ""}${h(cur.provider)} ${h(cur.model)} / ${h(cur.status)} ${cur.parent_take_id ? `/ 元 <a href="#/cut/${cut.id}?take=${cur.parent_take_id}">#${cur.parent_take_id}</a>` : ""} / ${h(cur.created_by)} ${h(cur.created_at)}</div>
            ${cur.error ? `<p style="color:var(--red)">${h(cur.error)}</p>` : ""}
            ${cur.agent_note ? `<p>エージェントの意図：${h(cur.agent_note)}</p>` : ""}
            ${JSON.parse(cur.refs_json || "[]").length ? `<div class="thumbs" style="margin:6px 0">${JSON.parse(cur.refs_json).map((r, i) => `<div class="thumb" title="@image${i + 1} ${h(r)}"><img src="/media/${encodeURI(r)}"><span class="n">@${i + 1}</span></div>`).join("")}</div>` : ""}
            ${cur.tier === "draft" ? `<p class="small muted">ドラフトに「良い」か「採用」をつけると、エージェントが拡大 → 1080p 本番へ進めます。</p>` : ""}
            <pre class="prompt">${h(cur.prompt) || "（プロンプトなし）"}</pre>` : ""}
        </div>
        <div class="card">
          ${cur ? `<h2 style="margin-top:0">テイク #${cur.id} にレビュー</h2>
          <div class="chips" id="verdicts">${META.verdicts.map((v) => `<button class="${v === verdict ? "on" : ""}" data-v="${v}">${v}</button>`).join("")}</div>
          <h2>どこが（観点）</h2><div class="chips" id="tags">${META.tags.map((t) => `<button class="${tags.has(t) ? "on" : ""}" data-t="${t}">${t}</button>`).join("")}</div>
          <h2>なぜ・どう直したいか</h2><textarea id="comment" placeholder="例：あかねが左を向いている。店は右なので右向きに。表情はもう少し不安げに"></textarea>
          <div class="small muted" id="regionInfo">${region ? "範囲あり" : "範囲なし"}</div>
          <div class="row" style="margin-top:8px"><button class="primary" id="send">レビューを送る</button>
            <button id="selectTake">${cur.selected ? "採用中" : "このテイクを採用"}</button></div>
          <h2>このテイクのレビュー</h2>${reviewsFor(cur).map(renderReview).join("") || `<p class="muted small">なし</p>`}`
          : `<h2 style="margin-top:0">このコマにレビュー</h2><textarea id="comment" placeholder="字コンテそのものへの指摘（意図・尺・芝居など）"></textarea>
             <div class="row" style="margin-top:8px"><button class="primary" id="sendCut">送る</button></div>`}
        </div>
      </div>`;
    bind();
  };

  const bind = () => {
    const cm = document.getElementById("comment");
    if (cm) cm.addEventListener("voice", (e) => {
      const v = parseVoice(e.detail);
      if (v.verdict) verdict = v.verdict;
      v.tags.forEach((t) => tags.add(t));
      const text = cm.value.replace(e.detail, v.comment);
      draw(); addMics(); document.getElementById("comment").value = text;
    });
    const ep = params.get("ep"); if (!ep) document.getElementById("back").href = "javascript:history.back()";
    document.querySelectorAll("[data-v]").forEach((b) => (b.onclick = () => { verdict = b.dataset.v; keep(draw); }));
    document.querySelectorAll("[data-t]").forEach((b) => (b.onclick = () => { tags.has(b.dataset.t) ? tags.delete(b.dataset.t) : tags.add(b.dataset.t); keep(draw); }));
    document.querySelectorAll("[data-cmp]").forEach((c) => { c.checked = compareSet.has(+c.dataset.cmp); c.onchange = () => (c.checked ? compareSet.add(+c.dataset.cmp) : compareSet.delete(+c.dataset.cmp)); });
    document.querySelectorAll("[data-res]").forEach((b) => (b.onclick = async () => { await api(`/api/reviews/${b.dataset.res}`, { method: "PATCH", body: { status: b.dataset.st } }); route(); }));
    document.getElementById("cmp").onclick = () => compareSet.size >= 2 ? (location.hash = `#/compare?ids=${[...compareSet].join(",")}`) : alert("2つ以上選んでください");
    document.getElementById("up").onchange = async (e) => {
      const fd = new FormData(); fd.append("file", e.target.files[0]);
      await api(`/api/cuts/${cut.id}/takes`, { method: "POST", body: fd }); route();
    };
    const sendCut = document.getElementById("sendCut");
    if (sendCut) sendCut.onclick = async () => {
      await api("/api/reviews", { method: "POST", body: { target_type: "cut", target_id: cut.id, verdict: "修正", comment: document.getElementById("comment").value } }); route();
    };
    if (!cur) return;
    document.getElementById("selectTake").onclick = async () => { await api(`/api/takes/${cur.id}/select`, { method: "POST" }); route(); };
    document.getElementById("send").onclick = async () => {
      const vid = document.querySelector("#stage video");
      const reg = region || (vid ? { t_in: vid.currentTime, t_out: vid.currentTime } : null);
      await api("/api/reviews", { method: "POST", body: { target_type: "take", target_id: cur.id, verdict, tags: [...tags], comment: document.getElementById("comment").value, region: reg } });
      region = null; tags = new Set(); verdict = "修正"; route();
    };
    // 範囲の印
    const stage = document.getElementById("stage"), drag = document.getElementById("drag");
    if (!stage.querySelector("img")) return;
    let start = null;
    stage.onmousedown = (e) => { e.preventDefault(); const r = stage.getBoundingClientRect(); start = [(e.clientX - r.left) / r.width, (e.clientY - r.top) / r.height]; };
    stage.onmousemove = (e) => {
      if (!start) return; const r = stage.getBoundingClientRect();
      const x = (e.clientX - r.left) / r.width, y = (e.clientY - r.top) / r.height;
      region = { x: Math.min(x, start[0]), y: Math.min(y, start[1]), w: Math.abs(x - start[0]), h: Math.abs(y - start[1]) };
      drag.className = "box mine"; Object.assign(drag.style, { left: region.x * 100 + "%", top: region.y * 100 + "%", width: region.w * 100 + "%", height: region.h * 100 + "%" });
    };
    stage.onmouseup = () => { start = null; document.getElementById("regionInfo").textContent = region ? "範囲あり（この範囲がレビューに入ります）" : "範囲なし"; };
  };
  // 入力中のコメントを保ったまま描き直す
  const keep = (fn) => { const c = document.getElementById("comment")?.value; fn(); if (c) document.getElementById("comment").value = c; };
  draw();
}

// ---------- 並べて比較 ----------
async function viewCompare(params) {
  const takes = await api(`/api/takes?ids=${params.get("ids")}`);
  const axes = {}; let winner = null;
  const draw = () => {
    $view.innerHTML = `<h1>並べて比較 <span class="muted small">観点ごとに良い方を選び、理由を書くとエージェントの次の生成に効きます</span></h1>
      <div class="compare" style="grid-template-columns:repeat(${takes.length},1fr)">${takes.map((t) => `
        <div class="col ${winner === t.id ? "win" : ""}"><div class="row"><b>#${t.id}</b><span class="small muted">${h(t.cut)}${h(t.panel)} ${h(t.provider)} ${h(t.model)}</span></div>
          <div class="stage">${media(t)}</div>
          ${t.agent_note ? `<p class="small">${h(t.agent_note)}</p>` : ""}
          <details><summary class="small muted">プロンプト</summary><pre class="prompt">${h(t.prompt)}</pre></details>
          <button class="${winner === t.id ? "primary" : ""}" data-win="${t.id}">総合でこれ</button></div>`).join("")}</div>
      <h2>観点ごと</h2><table class="axes">${AXES.map((a) => `<tr><td>${a}</td>${takes.map((t) => `<td><button class="${axes[a] === t.id ? "on" : ""}" data-ax="${a}" data-id="${t.id}">#${t.id}</button></td>`).join("")}</tr>`).join("")}</table>
      <h2>理由</h2><textarea id="reason" placeholder="例：#12 は表情が良いが、#15 の方が配置が字コンテどおり。#15 の配置で #12 の表情にしたい"></textarea>
      <div class="row" style="margin-top:8px"><button class="primary" id="save">比較を残す</button></div>`;
    document.querySelectorAll("[data-win]").forEach((b) => (b.onclick = () => { winner = +b.dataset.win; keep(); }));
    document.querySelectorAll("[data-ax]").forEach((b) => (b.onclick = () => { axes[b.dataset.ax] = +b.dataset.id; keep(); }));
    document.getElementById("save").onclick = async () => {
      await api("/api/comparisons", { method: "POST", body: { take_ids: takes.map((t) => t.id), winner_take_id: winner, axes, reason: document.getElementById("reason").value } });
      history.back();
    };
  };
  const keep = () => { const r = document.getElementById("reason").value; draw(); document.getElementById("reason").value = r; };
  draw();
}

// ---------- レビューの受け箱 ----------
async function viewReviews(params) {
  const status = params.get("status") || "open,working,proposed";
  const by = params.get("by") || "";
  const list = await api(`/api/reviews?status=${status}${by ? `&by=${by}` : ""}`);
  const tabs = [["open,working,proposed", "", "対応中すべて"], ["proposed", "", "エージェントの返答を確認"], ["open", "human", "自分の未着手"],
    ["working", "agent", "AIが止めたもの"], ["resolved", "", "解決済み"]];
  $view.innerHTML = `<h1>レビュー</h1><div class="row">${tabs.map(([s, b, l]) => `<a class="btn ${s === status && b === by ? "on" : ""}" href="#/reviews?status=${s}${b ? `&by=${b}` : ""}">${l}</a>`).join("")}</div>
    ${list.map((r) => `<div class="review ${r.status}"><div class="row">
      ${r.take_file ? `<a class="thumb" href="#/cut/${r.cut_ref}?take=${r.target_id}">${media({ kind: r.take_kind, file_path: r.take_file })}</a>` : ""}
      <div style="flex:1"><div class="row">${r.created_by === "agent" ? `<span class="badge proposed">AI</span>` : ""}<b>${h(r.verdict)}</b><span class="badge">${h(r.status)}</span>
        <a href="#/cut/${r.cut_ref}${r.target_type === "take" ? `?take=${r.target_id}` : ""}">${h(r.cut || "")}${h(r.panel || "")}</a>
        <span class="small muted">${h(r.target_type)}:${r.target_id} [${h(r.tags)}] #${r.id} ${h(r.created_at)}</span></div>
        <div>${h(r.comment)}</div>${r.agent_response ? `<div class="agent small">エージェント：${h(r.agent_response)}</div>` : ""}
        ${r.status === "proposed" ? `<textarea data-reply="${r.id}" placeholder="返事（例：①は正本どおりで。②はあかねで。③は鈴も残したい）"></textarea>
          <div class="row" style="margin-top:4px"><button data-rv="${r.id}" data-st="resolved">これでいい</button><button data-rv="${r.id}" data-st="open">返事を送る（まだ）</button></div>` : ""}
        </div></div></div>`).join("") || `<p class="muted">なし</p>`}`;
  // エージェントの返答に、その場で答える。返事は新しいレビューとして残り、エージェントの次のブリーフに入る
  document.querySelectorAll("[data-rv]").forEach((b) => (b.onclick = async () => {
    const r = list.find((x) => x.id == b.dataset.rv);
    const text = document.querySelector(`[data-reply="${r.id}"]`).value.trim();
    if (text) await api("/api/reviews", { method: "POST", body: { target_type: r.target_type, target_id: r.target_id, verdict: b.dataset.st === "resolved" ? "良い" : "修正", tags: (r.tags || "").split(",").filter(Boolean), comment: `（#${r.id} への返事）${text}` } });
    await api(`/api/reviews/${r.id}`, { method: "PATCH", body: { status: "resolved" } });   // 元の問いは閉じ、中身は返事のレビューで続ける
    route();
  }));
}

// ---------- ルール（エージェントの提案を承認する） ----------
async function viewRules() {
  const list = await api("/api/learnings");
  $view.innerHTML = `<h1>ルール</h1><p class="muted">レビューのくり返しから、エージェントが「次からこうする」を提案します。承認したものだけがブリーフに入り、全話の生成で守られます。</p>
    ${list.map((l) => `<div class="review ${l.status === "proposed" ? "proposed" : l.status === "approved" ? "resolved" : ""}">
      <div class="row"><span class="badge">${h(l.status)}</span><span class="small muted">${h(l.scope)} / 元のレビュー ${h(l.source_review_ids)}</span></div>
      ${l.status === "proposed" ? `<textarea data-txt="${l.id}">${h(l.rule_text)}</textarea>
        <div class="row"><button class="primary" data-ok="${l.id}">承認</button><button data-ng="${l.id}">却下</button></div>` : `<div>${h(l.rule_text)}</div>`}</div>`).join("") || `<p class="muted">まだ提案はありません。</p>`}`;
  const decide = (id, approve) => api(`/api/learnings/${id}`, { method: "POST", body: { approve, rule_text: document.querySelector(`[data-txt="${id}"]`).value } }).then(route);
  document.querySelectorAll("[data-ok]").forEach((b) => (b.onclick = () => decide(b.dataset.ok, true)));
  document.querySelectorAll("[data-ng]").forEach((b) => (b.onclick = () => decide(b.dataset.ng, false)));
}

async function viewBrief(params) {
  const text = await api(`/api/brief${params.get("ep") ? `?episode=${params.get("ep")}` : ""}`);
  $view.innerHTML = `<h1>エージェントが見ているもの</h1><p class="muted">エージェントは作業の前にこのブリーフを読みます（<code>python studio/cli.py brief EP09</code>）。</p><pre class="brief">${h(text)}</pre>`;
}

// ---------- 話数のタブ ----------
// 監督がふだん使うのは左の4つ。設計・コマ・ショットなどの細かい画面は「詳しく」に入れる
const epTabs = (code, now) => `<div class="row tabs">${[["vcon", "Vコン（見て直す）"], ["awaiting", "AIが通したもの"], ["questions", "AIからの質問"], ["stats", "実績"]]
  .map(([k, l]) => `<a class="btn ${k === now ? "on" : ""}" href="#/ep/${code}${k === "vcon" ? "" : "/" + k}">${l}</a>`).join("")}
  <span style="flex:1"></span>
  <select class="more" onchange="if(this.value) location.hash=this.value">
    <option value="">詳しく（エージェント向け）</option>
    ${[["design", "設計（シーン）"], ["cuts", "コマの一覧"], ["shots", "ショット分け"], ["edit", "編集（ライブ）"]].map(([k, l]) =>
      `<option value="#/ep/${code}/${k}" ${k === now ? "selected" : ""}>${l}</option>`).join("")}
    <option value="#/brief?ep=${code}">ブリーフ</option>
  </select></div>`;

// ---------- 設計：シーンごとの狙い・尺・動線 ----------
async function viewDesign(code) {
  const [{ episode: ep, scenes, spent }, use] = await Promise.all([api(`/api/episodes/${code}/scenes`), api(`/api/episodes/${code}/usage`)]);
  const planned = scenes.reduce((s, x) => s + (x.target_seconds || 0), 0);
  const actual = scenes.reduce((s, x) => s + (x.actual_seconds || 0), 0);
  const max = Math.max(ep.target_seconds, planned, actual, 1);
  const pct = Math.min(100, (100 * spent) / (ep.budget_credits || 50000));
  $view.innerHTML = `${epTabs(code, "design")}<h1>${h(code)} 設計</h1>
    <div class="card row" style="gap:20px">
      <label>目標尺（秒）<input type="text" id="tgt" value="${ep.target_seconds}" style="width:80px"></label>
      <label>締切<input type="text" id="dl" value="${h(ep.deadline || "")}" placeholder="2026-10-22" style="width:120px"></label>
      <label>予算（円）<input type="text" id="bud" value="${ep.budget_credits || ""}" style="width:90px"></label>
      <button id="saveEp">保存</button>
      <div style="flex:1;min-width:220px"><div class="small muted">使用 ${Math.round(spent).toLocaleString()}円 / ${(ep.budget_credits || 50000).toLocaleString()}円${ep.is_test ? "（テスト）" : ""}　${use.by_kind.map((k) => `${h(k.provider)}/${h(k.kind)} ${k.n}回`).join("・")}</div>
        <div class="meter"><i style="width:${pct}%;background:${pct > 85 ? "var(--red)" : "var(--amber)"}"></i></div></div>
    </div>
    <h2>尺の配分　<span class="small">上＝設計の目標 ${planned.toFixed(1)}秒 / 下＝今の字コンテ ${actual.toFixed(1)}秒 / 線＝話数の目標 ${ep.target_seconds}秒</span></h2>
    <div class="alloc">${["target_seconds", "actual_seconds"].map((f) => `<div class="strip" style="position:relative">${scenes.map((x, i) =>
      `<a style="width:${(100 * (x[f] || 0)) / max}%;background:hsl(${(i * 47) % 360} 30% 40%)" title="${h(x.code)} ${x[f]}秒">${h(x.code)}</a>`).join("")}
      <span class="goal" style="left:${(100 * ep.target_seconds) / max}%"></span></div>`).join("")}</div>
    <div class="grid" style="grid-template-columns:repeat(auto-fill,minmax(420px,1fr))">${scenes.map((x) => `<div class="card">
      <div class="row"><h3 style="margin:0">${h(x.code)}</h3><span class="badge ${x.status === "approved" ? "sel" : x.status === "review" ? "proposed" : ""}">${h(x.status)}</span>
        <span class="small muted">${h(x.place)} ${h(x.time)} ルック${h(x.look)} カメラ ${h(x.cameras)}</span></div>
      <div class="small muted">目標 ${x.target_seconds}秒 / 今 ${x.actual_seconds}秒 ${x.actual_seconds > x.target_seconds * 1.15 ? `<span style="color:var(--red)">長い</span>` : ""}</div>
      <dl class="spec"><dt>見せたいもの</dt><dd>${h(x.purpose)}</dd><dt>感情の流れ</dt><dd>${h(x.emotion)}</dd>
        <dt>立ち位置と動線</dt><dd>${h(x.blocking)}</dd><dt>小物</dt><dd>${h(x.props)}</dd></dl>
      <textarea data-sc="${h(x.code)}" placeholder="この設計へのレビュー（エージェントが次に読みます）"></textarea>
      <div class="row" style="margin-top:6px"><button class="primary" data-ok="${h(x.code)}">この設計でいく</button><button data-fix="${h(x.code)}">直してほしい</button></div>
    </div>`).join("") || `<p class="muted">まだ設計がありません。エージェントが脚本を読んで <code>scene-set</code> で作ります。</p>`}</div>`;
  document.getElementById("saveEp").onclick = async () => {
    await api(`/api/episodes/${code}`, { method: "PATCH", body: { target_seconds: +document.getElementById("tgt").value, deadline: document.getElementById("dl").value, budget_credits: +document.getElementById("bud").value || 0 } });
    route();
  };
  const sceneReview = async (sc, ok) => {
    const text = document.querySelector(`[data-sc="${sc}"]`).value;
    await api(`/api/episodes/${code}/scenes/${sc}`, { method: "PATCH", body: { status: ok ? "approved" : "review" } });
    if (text) await api("/api/reviews", { method: "POST", body: { target_type: "episode", target_id: ep.id, verdict: ok ? "良い" : "修正", tags: ["意図"], comment: `[設計 ${sc}] ${text}` } });
    route();
  };
  document.querySelectorAll("[data-ok]").forEach((b) => (b.onclick = () => sceneReview(b.dataset.ok, true)));
  document.querySelectorAll("[data-fix]").forEach((b) => (b.onclick = () => sceneReview(b.dataset.fix, false)));
}

// ---------- ショット：1本の動画（最大30秒）に何を入れるか ----------
async function viewShots(code) {
  const list = await api(`/api/episodes/${code}/shots`);
  const total = list.reduce((s, x) => s + x.seconds, 0);
  $view.innerHTML = `${epTabs(code, "shots")}<h1>ショット <span class="muted small">${list.length}本 / ${total.toFixed(1)}秒。字コンテと仮Vコンを並べて、1本で出すかたまりを決める（1本30秒まで）</span></h1>
    ${list.map((x) => `<div class="card" style="margin-bottom:10px">
      <div class="row"><b>${h(x.code)}</b><span class="badge ${x.status === "approved" ? "sel" : ""}">${h(x.status)}</span>
        <span class="muted small">${h(x.range)}　${x.seconds}秒　${x.cuts.length}コマ</span>
        ${x.seconds > 30 ? `<span class="badge open">30秒超</span>` : ""}<span style="flex:1"></span>
        ${x.takes.map((t) => `<a class="badge ${t.selected ? "sel" : ""}" href="#/cut/${x.cuts[0]?.id}?take=${t.id}&ep=${code}">#${t.id} ${TIER[t.tier] || t.tier || ""}</a>`).join("")}
        <button data-ok="${h(x.code)}">${x.status === "approved" ? "承認済み" : "この分け方でいく"}</button></div>
      <div class="small">${h(x.note)}</div>
      <div class="thumbs" style="margin-top:6px">${x.cuts.map((c) => `<a class="thumb" href="#/cut/${c.id}?ep=${code}" title="${h(c.picture)}">${c.thumb ? `<img src="/media/${encodeURI(c.thumb)}">` : ""}<span class="n">${h(c.cut)}${h(c.panel)} ${c.seconds}s</span></a>`).join("")}</div>
    </div>`).join("") || `<p class="muted">まだショットがありません。エージェントが <code>shot-plan</code> で分けます。</p>`}`;
  document.querySelectorAll("[data-ok]").forEach((b) => (b.onclick = () => api(`/api/episodes/${code}/shots/${b.dataset.ok}`, { method: "PATCH", body: { status: "approved" } }).then(route)));
}

// ---------- AI が通したもの：監督が上から流し見する ----------
async function viewAwaiting(code) {
  const list = await api(`/api/episodes/${code}/awaiting`);
  $view.innerHTML = `${epTabs(code, "awaiting")}<h1>AIが通したもの <span class="muted small">${list.length}件。キー 1＝良い・2＝採用・3＝話して直し。気になるものだけ開いて直しを書く</span></h1>
    <div class="grid" style="grid-template-columns:repeat(auto-fill,minmax(300px,1fr))">${list.map((t) => `<div class="card">
      <a class="stage" style="display:block" href="#/cut/${t.cut_id}?take=${t.id}&ep=${code}">${media(t)}</a>
      <div class="row"><b>${h(t.cut)}${h(t.panel)}</b><span class="small muted">#${t.id} ${h(t.provider)}</span></div>
      <div class="small agent">AI：${h(t.ai_comment) || "観点すべて合格"}</div>
      <div class="row" style="margin-top:6px"><button data-good="${t.id}">良い</button><button data-sel="${t.id}">採用</button>
        <button data-voice="${t.id}" title="話してレビュー（例：『修正、あかねの向きが逆』）">🎤</button>
        <a class="btn" href="#/cut/${t.cut_id}?take=${t.id}&ep=${code}">直しを書く</a></div></div>`).join("") || `<p class="muted">確認待ちはありません。</p>`}</div>`;
  const quick = (id, verdict) => api("/api/reviews", { method: "POST", body: { target_type: "take", target_id: +id, verdict } }).then(route);
  document.querySelectorAll("[data-good]").forEach((b) => (b.onclick = () => quick(b.dataset.good, "良い")));
  document.querySelectorAll("[data-sel]").forEach((b) => (b.onclick = () => quick(b.dataset.sel, "採用")));
  document.querySelectorAll("[data-voice]").forEach((b) => (b.onclick = () => { b.classList.add("on"); listen((text) => {
    const v = parseVoice(text);
    api("/api/reviews", { method: "POST", body: { target_type: "take", target_id: +b.dataset.voice, verdict: v.verdict || "修正", tags: v.tags, comment: v.comment } }).then(route);
  }); }));
  // キーボード：先頭のカードに 1＝良い 2＝採用 3＝話して直し
  document.onkeydown = (e) => {
    if (!location.hash.includes("/awaiting") || e.target.tagName === "TEXTAREA" || e.target.tagName === "INPUT") return;
    const first = document.querySelector("[data-good]");
    if (!first) return;
    if (e.key === "1") quick(first.dataset.good, "良い");
    if (e.key === "2") quick(first.dataset.good, "採用");
    if (e.key === "3") document.querySelector("[data-voice]").click();
  };
}

// ---------- 編集（ライブ）：採用テイクを通しで再生し、エージェントの操作を見ながら手直しする ----------
async function viewEdit(code, params) {
  const plist = await api(`/api/episodes/${code}/playlist`);
  const cuts = plist.map((p) => ({ ...p.cut, _play: p }));
  const pick = (c) => c._play.take;
  const total = cuts.reduce((s, c) => s + (c.seconds || 0), 0) || 1;
  let i = Math.max(0, cuts.findIndex((c) => c.id == params.get("cut"))), playing = false, timer = null;
  const fmt = (sec) => `${Math.floor(sec / 60)}:${(sec % 60).toFixed(1).padStart(4, "0")}`;
  const startOf = (k) => cuts.slice(0, k).reduce((s, c) => s + (c.seconds || 0), 0);
  $view.innerHTML = `${epTabs(code, "edit")}
    <div class="editor">
      <div><div class="stage" id="mon"></div><div class="sub" id="sub"></div><div id="snd" class="row"></div>
        <div class="row" style="margin:8px 0"><button id="prev">◀</button><button class="primary" id="play">再生</button><button id="next">▶</button>
          <span id="tc" class="muted"></span><span style="flex:1"></span>
          <button id="export">Premiere 用 XML</button></div>
        <div class="strip tl" id="tl">${cuts.map((c, k) => `<a data-k="${k}" class="${pick(c) ? (pick(c).selected ? "sel" : "has") : ""}" style="width:${(100 * (c.seconds || 0.5)) / total}%"></a>`).join("")}</div>
        <div class="card" id="cutpanel"></div></div>
      <div class="card live"><h2 style="margin-top:0">エージェントの操作</h2><div id="feed" class="small"></div></div>
    </div>`;
  const show = () => {
    const c = cuts[i], t = pick(c);
    document.getElementById("mon").innerHTML = t ? media(t) : `<div class="placeholder">${h(c.picture)}</div>`;
    document.getElementById("sub").textContent = c.dialogue || "";
    document.getElementById("tc").textContent = `${c.cut}${c.panel}　${fmt(startOf(i))} / ${fmt(total)}`;
    document.querySelectorAll("#tl a").forEach((a) => a.classList.toggle("now", +a.dataset.k === i));
    const vid = document.querySelector("#mon video");
    const aud = c._play.audio || [];
    document.getElementById("snd").innerHTML = aud.map((a) => `<audio src="/media/${encodeURI(a.file_path)}" data-role="${h(a.role)}"></audio>`).join("")
      + (aud.length ? `<span class="small muted">音：${aud.map((a) => ({ actor: "声優", voice: "仮の声", sfx: "効果音", music: "劇伴" }[a.role] || a.role)).join("・")}</span>` : "");
    if (playing) document.querySelectorAll("#snd audio").forEach((a) => a.play().catch(() => {}));
    if (vid) {   // ショットの動画は、このコマの位置から映す。Seedance の音は使わない
      vid.muted = true;
      const seek = () => { vid.currentTime = c._play.offset || 0; if (playing) vid.play().catch(() => {}); };
      vid.readyState >= 1 ? seek() : vid.addEventListener("loadedmetadata", seek, { once: true });
    }
    document.getElementById("tc").textContent += c._play.shot ? `　${c._play.shot}${t ? `（${TIER[t.tier] || t.tier || ""}）` : ""}` : "";
    document.getElementById("cutpanel").innerHTML = `<div class="row"><b>${h(c.cut)}${h(c.panel)}</b><span class="small muted">${h(c.camerawork)}</span>
        <span style="flex:1"></span><a href="#/cut/${c.id}?ep=${code}">このコマを開く</a></div>
      <div class="row small"><label>尺（秒）<input type="text" id="sec" value="${c.seconds ?? ""}" style="width:70px"></label>
        <label style="flex:1">台詞<input type="text" id="dia" value="${h(c.dialogue)}"></label>
        <label style="flex:1">編集メモ<input type="text" id="memo" value="${h(c.edit_memo)}"></label><button id="saveCut">手直しを保存</button></div>`;
    document.getElementById("saveCut").onclick = async () => {
      const body = { seconds: +document.getElementById("sec").value, dialogue: document.getElementById("dia").value, edit_memo: document.getElementById("memo").value };
      await api(`/api/cuts/${c.id}`, { method: "PATCH", body }); Object.assign(c, body); show();
    };
  };
  const step = () => { if (i < cuts.length - 1) { i++; show(); timer = setTimeout(step, (cuts[i].seconds || 1) * 1000); } else stop(); };
  const stop = () => { playing = false; clearTimeout(timer); document.getElementById("play").textContent = "再生"; };
  document.getElementById("play").onclick = () => { if (playing) return stop(); playing = true; document.getElementById("play").textContent = "停止"; timer = setTimeout(step, (cuts[i].seconds || 1) * 1000); };
  document.getElementById("prev").onclick = () => { stop(); i = Math.max(0, i - 1); show(); };
  document.getElementById("next").onclick = () => { stop(); i = Math.min(cuts.length - 1, i + 1); show(); };
  document.querySelectorAll("#tl a").forEach((a) => (a.onclick = () => { stop(); i = +a.dataset.k; show(); }));
  document.getElementById("export").onclick = async () => { const r = await api(`/api/episodes/${code}/export`, { method: "POST" }); alert(`書き出しました\n${r.xml}\n未採用 ${r.missing.length}コマ`); };
  const feed = document.getElementById("feed");
  const events = await api("/api/events?limit=30");
  feed.innerHTML = events.map(eventLine).join("");
  liveHandlers.edit = (e) => {
    feed.insertAdjacentHTML("afterbegin", eventLine(e));
    const cutId = e.payload?.cut; const k = cuts.findIndex((c) => c.id === cutId);
    if (k >= 0) document.querySelector(`#tl a[data-k="${k}"]`)?.classList.add("flash");
  };
  show();
}

// ---------- ライブ：エージェントの操作を全画面で受け取る ----------
const ACTIONS = { add_take: "テイクを作成", self_review: "セルフレビュー", respond_review: "レビューに返答", propose_learning: "ルールを提案",
  set_scene: "設計を更新", update_cut: "コマを手直し", import_jikonte: "字コンテを取り込み", add_review: "レビュー", select_take: "採用",
  compare: "比較", update_episode: "話数を更新", review_status: "レビューの状態", decide_learning: "ルールを判断" };
const eventLine = (e) => `<div class="ev ${e.actor}"><span class="muted">${h((e.ts || "").slice(11, 19))}</span> <b>${e.actor === "agent" ? "AI" : "自分"}</b> ${h(ACTIONS[e.action] || e.action)}
  <span class="muted">${h(JSON.stringify(e.payload || {}).slice(0, 80))}</span></div>`;
const liveHandlers = {};
try {
  const es = new EventSource("/api/stream");
  es.onmessage = (m) => {
    const e = JSON.parse(m.data); e.payload = JSON.parse(e.payload_json || "{}");
    Object.values(liveHandlers).forEach((f) => f(e));
    if (e.actor === "agent") { const d = document.getElementById("toast"); d.innerHTML = eventLine(e); d.className = "show"; clearTimeout(d._t); d._t = setTimeout(() => (d.className = ""), 4000); }
  };
} catch (e) { /* SSE が使えない環境では通知なしで動く */ }

// ---------- 音声入力：話した言葉をそのままレビューに ----------
// 先頭の言葉で判定（「採用」「良い」「保留」「修正」「却下」）、観点の言葉（配置・表情…）はタグに拾う。
const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
function parseVoice(text) {
  const t = text.trim();
  const verdict = META.verdicts.find((v) => t.startsWith(v)) || (/^(OK|オッケー|いいね|いい)/.test(t) ? "良い" : null);
  const tagWords = { "配置": "配置・左右", "左右": "配置・左右", "向き": "配置・左右", "表情": "表情", "芝居": "芝居", "動き": "芝居",
    "崩れ": "キャラ崩れ", "顔": "キャラ崩れ", "構図": "構図", "光": "光・色", "色": "光・色", "背景": "背景", "カメラ": "カメラワーク",
    "尺": "尺・テンポ", "テンポ": "尺・テンポ", "間": "尺・テンポ", "台詞": "台詞・声", "声": "台詞・声", "音": "音", "つなぎ": "つなぎ", "意図": "意図", "小物": "小物" };
  const tags = [...new Set(Object.entries(tagWords).filter(([w]) => t.includes(w)).map(([, tg]) => tg))];
  const comment = verdict ? t.slice(verdict.length).replace(/^[、。,\s]+/, "") : t;
  return { verdict, tags, comment };
}
function listen(onText) {
  if (!SR) { alert("このブラウザは音声入力に対応していません（Chrome / Edge で使えます）"); return; }
  const r = new SR(); r.lang = "ja-JP"; r.interimResults = false;
  r.onresult = (e) => onText(e.results[0][0].transcript);
  r.start();
  return r;
}
function addMics() {   // 文字を書く欄すべてに 🎤 を付ける
  document.querySelectorAll("textarea:not([data-mic])").forEach((ta) => {
    ta.dataset.mic = "1";
    const b = document.createElement("button");
    b.type = "button"; b.className = "mic"; b.textContent = "🎤"; b.title = "話して入力（先頭に『良い』『修正』などで判定も入る）";
    b.onclick = () => { b.classList.add("on"); listen((t) => { b.classList.remove("on"); ta.value = (ta.value ? ta.value + " " : "") + t;
      ta.dispatchEvent(new CustomEvent("voice", { detail: t })); }); };
    ta.insertAdjacentElement("afterend", b);
  });
}

// ---------- 実績：工程ごとの費用と待ち時間 ----------
async function viewStats(code) {
  const r = await api(`/api/episodes/${code}/stats`);
  const pct = Math.min(100, (100 * r.spent) / r.budget);
  $view.innerHTML = `${epTabs(code, "stats")}<h1>${h(code)} 実績 <span class="muted small">どの工程で、いくら使い、どれだけ待ったか</span></h1>
    <div class="card"><div class="row"><b>${r.spent.toLocaleString()}円</b><span class="muted">/ ${r.budget.toLocaleString()}円${r.is_test ? "（テストの回）" : ""}</span></div>
      <div class="meter"><i style="width:${pct}%;background:${pct > 85 ? "var(--red)" : "var(--amber)"}"></i></div></div>
    <table class="cuts" style="margin-top:12px"><tr><th>工程</th><th>回数</th><th>失敗</th><th>採用</th><th>費用</th><th>動画の秒数</th>
      <th>生成の待ち（平均／合計 分）</th><th>監督のレビューまで（平均 分）</th></tr>
      ${r.stages.map((s) => `<tr><td>${h(s.stage)}</td><td>${s.n}</td><td>${s.failed}</td><td>${s.adopted}</td><td>${s.yen.toLocaleString()}円</td>
        <td>${s.video_seconds}</td><td>${s.gen_wait_min ?? "-"} / ${s.gen_wait_total_min}</td><td>${s.review_wait_min ?? "-"}</td></tr>`).join("")}</table>
    <p class="small muted">生成の待ちは「送ってから出来上がるまで」、レビューまでは「出来上がってから監督が最初に見るまで」。テストの回の数字で、段取りと予算の目安を直していく。</p>`;
}

// ---------- 依頼：監督 → エージェント（この PC でも、クラウドの Claude でも） ----------
async function viewRequests() {
  const [list, eps] = await Promise.all([api("/api/requests"), api("/api/episodes")]);
  $view.innerHTML = `<h1>依頼 <span class="muted small">話して積んでおけば、どの Claude が取っても同じ形で進めます（二重には進めない）</span></h1>
    <div class="card"><div class="row"><select id="rqEp" style="width:auto"><option value="">話数なし</option>${eps.map((e) => `<option>${h(e.code)}</option>`).join("")}</select></div>
      <textarea id="rqText" placeholder="例：EP09 の S1 の設計を、あかねが最初から落ち着かない方向で直して"></textarea>
      <div class="row" style="margin-top:6px"><button class="primary" id="rqAdd">依頼する</button></div></div>
    ${list.map((r) => `<div class="review ${r.status === "done" ? "resolved" : r.status === "claimed" ? "proposed" : "open"}">
      <div class="row"><b>#${r.id}</b><span class="badge">${h(r.status)}${r.claimed_by ? "：" + h(r.claimed_by) : ""}</span><span class="small muted">${h(r.episode)} ${h(r.ts)}</span>
        <span style="flex:1"></span>
        ${r.status === "open" ? `<button data-hand="${r.id}" data-mode="local">この PC の Claude へ</button><button data-hand="${r.id}" data-mode="remote">クラウドの Claude へ</button><button data-cancel="${r.id}">取り消す</button>` : ""}</div>
      <div>${h(r.text)}</div>${r.result ? `<div class="agent small">結果：${h(r.result)}</div>` : ""}</div>`).join("") || `<p class="muted">依頼はまだありません。</p>`}
    <div id="handBox" class="card" style="display:none;margin-top:10px"><div class="row"><b>依頼文</b><span class="muted small">コピーして、渡したい Claude に貼る</span><span style="flex:1"></span><button id="copy">コピー</button></div><pre class="brief" id="handText"></pre></div>`;
  document.getElementById("rqAdd").onclick = async () => {
    const text = document.getElementById("rqText").value.trim();
    if (!text) return;
    await api("/api/requests", { method: "POST", body: { text, episode: document.getElementById("rqEp").value } }); route();
  };
  document.querySelectorAll("[data-cancel]").forEach((b) => (b.onclick = () => api(`/api/requests/${b.dataset.cancel}`, { method: "PATCH", body: { status: "cancelled" } }).then(route)));
  document.querySelectorAll("[data-hand]").forEach((b) => (b.onclick = async () => {
    document.getElementById("handText").textContent = await api(`/api/handoff?request_id=${b.dataset.hand}&mode=${b.dataset.mode}`);
    document.getElementById("handBox").style.display = "block";
  }));
  document.getElementById("copy").onclick = () => navigator.clipboard.writeText(document.getElementById("handText").textContent);
}

// ---------- ルーター ----------
async function route() {
  delete liveHandlers.edit;
  const [path, qs] = location.hash.slice(1).split("?");
  const params = new URLSearchParams(qs || "");
  const parts = (path || "/").split("/").filter(Boolean);
  try {
    if (parts[0] === "ep" && parts[2] === "design") await viewDesign(parts[1]);
    else if (parts[0] === "ep" && parts[2] === "awaiting") await viewAwaiting(parts[1]);
    else if (parts[0] === "ep" && parts[2] === "shots") await viewShots(parts[1]);
    else if (parts[0] === "ep" && parts[2] === "stats") await viewStats(parts[1]);
    else if (parts[0] === "ep" && parts[2] === "edit") await viewEdit(parts[1], params);
    else if (parts[0] === "ep" && parts[2] === "cuts") await viewEpisode(parts[1]);
    else if (parts[0] === "ep" && parts[2] === "questions") await viewQuestions(parts[1]);
    else if (parts[0] === "ep") await viewVcon(parts[1], params);
    else if (parts[0] === "cut") await viewCut(parts[1], params);
    else if (parts[0] === "compare") await viewCompare(params);
    else if (parts[0] === "reviews") await viewReviews(params);
    else if (parts[0] === "requests") await viewRequests();
    else if (parts[0] === "rules") await viewRules();
    else if (parts[0] === "brief") await viewBrief(params);
    else await viewHome();
  } catch (e) { $view.innerHTML = `<pre class="brief">${h(e.message)}</pre>`; }
  addMics();
}
window.addEventListener("hashchange", route);
api("/api/meta").then((m) => { META = m; route(); });
