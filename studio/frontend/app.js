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
  ${t.file_path ? media(t) : h(t.status)}<span class="n">#${t.id}${t.open_reviews ? " ●" : ""}</span></a>`;

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
  $view.innerHTML = `<div class="row"><h1>${h(episode.code)} ${h(episode.title)}</h1>
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
              style="${t.id === cur?.id ? "outline:2px solid var(--amber)" : ""}">${t.file_path ? media(t) : h(t.status)}<span class="n">#${t.id}</span></a>
              <label class="small"><input type="checkbox" data-cmp="${t.id}"> 比較</label></div>`).join("") || `<p class="muted">まだテイクがありません。</p>`}</div>
          <div class="row" style="margin-top:8px"><button id="cmp">選んだテイクを並べる</button>
            <label class="btn">自分で作ったものを足す<input type="file" id="up" hidden></label></div>
          ${cur ? `<h2>テイク #${cur.id} の作り方</h2>
            <div class="small muted">${h(cur.provider)} ${h(cur.model)} / ${h(cur.status)} ${cur.parent_take_id ? `/ 元 <a href="#/cut/${cut.id}?take=${cur.parent_take_id}">#${cur.parent_take_id}</a>` : ""} / ${h(cur.created_by)} ${h(cur.created_at)}</div>
            ${cur.error ? `<p style="color:var(--red)">${h(cur.error)}</p>` : ""}
            ${cur.agent_note ? `<p>エージェントの意図：${h(cur.agent_note)}</p>` : ""}
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
  const list = await api(`/api/reviews?status=${status}`);
  const tabs = [["open,working,proposed", "対応中すべて"], ["proposed", "エージェントの返答待ち確認"], ["open", "未着手"], ["resolved", "解決済み"]];
  $view.innerHTML = `<h1>レビュー</h1><div class="row">${tabs.map(([s, l]) => `<a class="btn ${s === status ? "on" : ""}" href="#/reviews?status=${s}">${l}</a>`).join("")}</div>
    ${list.map((r) => `<div class="review ${r.status}"><div class="row">
      ${r.take_file ? `<a class="thumb" href="#/cut/${r.cut_ref}?take=${r.target_id}">${media({ kind: r.take_kind, file_path: r.take_file })}</a>` : ""}
      <div style="flex:1"><div class="row"><b>${h(r.verdict)}</b><span class="badge">${h(r.status)}</span>
        <a href="#/cut/${r.cut_ref}${r.target_type === "take" ? `?take=${r.target_id}` : ""}">${h(r.cut || "")}${h(r.panel || "")}</a>
        <span class="small muted">${h(r.target_type)}:${r.target_id} [${h(r.tags)}] #${r.id} ${h(r.created_at)}</span></div>
        <div>${h(r.comment)}</div>${r.agent_response ? `<div class="agent small">エージェント：${h(r.agent_response)}</div>` : ""}</div></div></div>`).join("") || `<p class="muted">なし</p>`}`;
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

// ---------- ルーター ----------
async function route() {
  const [path, qs] = location.hash.slice(1).split("?");
  const params = new URLSearchParams(qs || "");
  const parts = (path || "/").split("/").filter(Boolean);
  try {
    if (parts[0] === "ep") await viewEpisode(parts[1]);
    else if (parts[0] === "cut") await viewCut(parts[1], params);
    else if (parts[0] === "compare") await viewCompare(params);
    else if (parts[0] === "reviews") await viewReviews(params);
    else if (parts[0] === "rules") await viewRules();
    else if (parts[0] === "brief") await viewBrief(params);
    else await viewHome();
  } catch (e) { $view.innerHTML = `<pre class="brief">${h(e.message)}</pre>`; }
}
window.addEventListener("hashchange", route);
api("/api/meta").then((m) => { META = m; route(); });
