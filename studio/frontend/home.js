// ---------- ホームの「いま AI が何をしているか」・順番待ち・AI の接続と割り振り ----------
const ROLE_JA = { "芝居": "芝居（設定）", "演出": "演出", "見る": "見る", "まとめ": "制作進行" };
const roleJa = (r) => ROLE_JA[r] || r;

// ===== AI の様子（ホームの上に出す） =====
function aiBoardHTML(p) {
  if (!p.running.length) return `<div class="card aiboard ng"><b>AI が登録されていません</b>（「AI の接続」で確かめてください）</div>`;
  const anyRun = p.running.some((a) => a.running);
  return `<div class="aiboard-head row"><h2 style="margin:0">いまの AI</h2>
      <span class="badge ${anyRun ? "proposed" : "open"}">${anyRun ? "作業中の AI があります" : "動いている AI はありません"}</span>
      <span style="flex:1"></span><a class="small" href="#/progress">その場の流れを見る ›</a></div>
    <div class="aigrid">${p.running.map((a) => {
      const st = a.running ? ["作業中", "on"] : a.idle_ok ? ["待機", "wait"] : ["動いていない", "ng"];
      const jobs = [...a.jobs.map((j) => `${j.episode ? j.episode + " " : ""}${j.stage}：${j.text}`),
                    ...a.slots.map((s) => `${s.episode} ${s.target || ""} 会議の${roleJa(s.role)}（${s.pass}周目）`)];
      return `<div class="card aicard ${st[1]}"><div class="row"><span class="dot"></span><b>${h(a.label)}</b><span style="flex:1"></span><span class="badge">${st[0]}</span></div>
        <div class="small muted">役：${a.roles.map(roleJa).join("・") || "なし"}</div>
        ${a.running ? (jobs.map((j) => `<div class="small">▶ ${h(j)}</div>`).join("") || `<div class="small">▶ 仕事を取っています…（${h((a.since || "").slice(11, 16))}から）</div>`)
          : `<div class="small ${a.idle_ok ? "muted" : "warn"}">${h(a.idle)}</div>`}
        ${!a.running && a.rest ? `<button class="small wake" data-wake="${h(a.agent)}">すぐ起こす</button>` : ""}
        ${!a.idle_ok && /ログイン|入って|役が/.test(a.idle) ? `<a class="small" href="#/agents">AI の接続へ ›</a>` : ""}</div>`;
    }).join("")}</div>`;
}

let HOME_TIMER = null;
async function homeBoard() {
  clearTimeout(HOME_TIMER);
  const box = document.getElementById("homeAI");
  if (!box) return;
  try {
    const p = await api("/api/progress");
    const q = p.queue;
    box.innerHTML = aiBoardHTML(p) + `<div class="row small" style="margin:8px 0 18px">
      <a href="#/progress?t=queue">順番待ち ${q.length} 件 ›</a>${q.slice(0, 3).map((x) => `<span class="muted">${h(x.episode || "全体")}・${h(x.stage)}</span>`).join("")}</div>`;
    box.querySelectorAll("[data-wake]").forEach((b) => (b.onclick = async () => { await api("/api/agents/wake", { method: "POST" }); homeBoard(); }));
  } catch (e) { box.innerHTML = `<div class="card ng small">AI の様子を読めませんでした：${h(e.message)}</div>`; }
  HOME_TIMER = setTimeout(() => (location.hash === "" || location.hash === "#/") && homeBoard(), 5000);
}

// ===== 順番待ち（進み具合と、話数の中で使う） =====
function queueHTML(items, showEp = true) {
  if (!items.length) return `<p class="muted">順番待ちはありません。</p>`;
  let n = 0;
  return items.map((q) => {
    const working = q.status === "claimed";
    const num = working ? "作業中" : ++n;
    return `<div class="card qrow ${working ? "working" : ""}"><span class="qn">${num}</span>
      <div style="flex:1"><div class="small"><b>${showEp ? h(q.episode || "全体") + "・" : ""}${h(q.stage)}</b>
        <span class="muted">${h(q.kind)}・${h(roleJa(q.role))}${working && q.by ? `・${h(q.by)} がやっています` : ""}</span></div>
        <div class="small muted">${h(q.text)}</div></div>
      <div class="qbtns">${!working && q.kind === "仕事" ? `<button class="small" data-q="request/${q.id}/top" title="いちばん先にする">⤒</button>
        <button class="small" data-q="request/${q.id}/up" title="ひとつ上へ">↑</button><button class="small" data-q="request/${q.id}/down" title="ひとつ下へ">↓</button>` : ""}
        ${working ? `<button class="small" data-q="${q.kind === "仕事" ? "request" : "slot"}/${q.id}/stop">中止</button>` : ""}
        <button class="small" data-q="${q.kind === "仕事" ? "request" : "slot"}/${q.id}/delete">消す</button></div></div>`;
  }).join("");
}
function bindQueue(root, again) {
  root.querySelectorAll("[data-q]").forEach((b) => (b.onclick = async () => {
    const [kind, id, action] = b.dataset.q.split("/");
    if ((action === "stop" || action === "delete") && !confirm(action === "stop" ? "作業中の AI を止めて、この仕事を中止しますか？" : "この順番待ちを消しますか？")) return;
    b.disabled = true;
    try { await api(`/api/queue/${kind}/${id}`, { method: "POST", body: { action } }); } catch (e) { alert(e.message); }
    again();
  }));
}

// 話数の「いま」の下に、その話の順番待ちを出す
async function epQueue(code) {
  const p = await api("/api/progress");
  const items = p.queue.filter((q) => q.episode === code);
  const box = document.createElement("div");
  box.innerHTML = `<h2 style="margin-top:22px">この話の順番待ち <span class="small muted">${items.length} 件</span></h2>${queueHTML(items, false)}`;
  $view.appendChild(box);
  bindQueue(box, () => route());
}

// ===== AI の接続と割り振り =====
async function viewAgents() {
  $view.innerHTML = `<h1>AI の接続</h1><p class="muted">ログインの状態を確かめています…（数秒かかります）</p>`;
  const [a, pr, MS] = await Promise.all([api("/api/agents"), api("/api/progress"), api("/api/agents/models")]);
  const opts = (list, cur) => list.map(([v, l]) => `<option value="${h(v)}" ${v === (cur || "") ? "selected" : ""}>${h(l)}</option>`).join("");
  const names = Object.keys(a.agents);
  $view.innerHTML = `<h1>AI の接続 <span class="muted small">AI ごとに別のアカウントでログインできます。ログインしておくと、月灯スタジオが裏で AI を動かします</span></h1>
    <h2>裏で動く AI <label class="small" style="margin-left:12px"><input type="checkbox" id="run" ${a.run_agents ? "checked" : ""}> 仕事が来たら自動で動かす</label></h2>
    <div class="agentgrid">${names.map((k) => { const v = a.agents[k]; const ok = v.installed && v.logged_in;
      const r = pr.running.find((x) => x.agent === k) || {};
      return `<div class="card agentcard ${ok ? "ok" : "ng"}">
      <div class="row"><span class="dot"></span><b>${h(v.label)}</b><span class="small muted">（${h(k)}）</span><span style="flex:1"></span>
        <span class="badge ${v.running ? "proposed" : ok ? "sel" : "open"}">${v.running ? "作業中" : !v.installed ? "入っていません" : ok ? "ログイン中" : "ログインしていません"}</span></div>
      <div class="small">アカウント：<b>${ok ? h(v.account || "（メールが読めませんでした）") : "―"}</b></div>
      <div class="small muted">${v.tool === "codex" ? "Codex（ChatGPT）" : "Claude"}${v.config_dir ? `・ログインの置き場所：${h(v.config_dir)}` : v.tool === "codex" ? "" : "・ふつうの置き場所（この PC の Claude と同じ）"}</div>
      <div class="small">役：${v.roles.map(roleJa).join("・") || "なし"}</div>
      <div class="row small modelrow">モデル <select data-model="${h(k)}">${opts(MS[v.tool === "codex" ? "codex" : "claude"].models, v.model)}</select>
        考える深さ <select data-effort="${h(k)}">${opts(MS[v.tool === "codex" ? "codex" : "claude"].efforts, v.effort)}</select>
        <span class="muted" data-mmsg="${h(k)}"></span></div>
      ${!v.running && r.idle ? `<div class="small ${r.idle_ok ? "muted" : "warn"}">${h(r.idle)}</div>` : ""}
      ${v.last ? `<div class="small muted">前回：${h(v.last)}</div>` : ""}
      <div class="row"><button class="${ok ? "" : "primary"}" data-loginas="${h(k)}">${ok ? "別のアカウントでログインし直す" : "ログインする"}</button>
        <span class="small muted" data-msg="${h(k)}"></span></div>
      <details data-log="${h(k)}"><summary class="small">作業の記録を見る</summary><pre class="brief small">読み込み中…</pre></details></div>`; }).join("")}</div>
    <div class="row"><button id="recheck">ログインの状態を確かめ直す</button>
      <span class="small muted">claude-a と claude-b を同じメールにすると、使用量が分かれません。claude-b はもう一つのアカウントでログインしてください。</span></div>

    <h2>AI の割り振り <span class="small muted">どの役（作業）をどの AI に頼むか。変えるとすぐ効きます</span></h2>
    <div class="card"><table class="loaded assign">${Object.entries(a.roles).map(([role, name]) => `<tr><th>${h(roleJa(role))}</th><td class="small muted">${h(name)}</td>
      <td><select data-role="${h(role)}"><option value="">（だれもやらない）</option>${names.map((k) => `<option value="${h(k)}" ${a.assign[role] === k ? "selected" : ""}>${h(a.agents[k].label)}</option>`).join("")}</select></td></tr>`).join("")}</table>
      <div class="small muted">「見る」は、作った本人には回りません。同じ AI が2つの役をやってもかまいません。</div>
      <h3 style="margin-top:14px">AI の呼び名</h3>
      <table class="loaded">${names.map((k) => `<tr><th>${h(k)}</th><td><input type="text" data-label="${h(k)}" value="${h(a.agents[k].label)}" style="width:100%"></td></tr>`).join("")}</table>
      <div class="row"><button class="primary" id="saveAssign">割り振りを保存</button><span class="small muted" id="assignMsg"></span></div></div>

    <h2>きょうの使用量 <span class="small muted">月灯スタジオから動かした分</span></h2>
    <div class="card"><table class="loaded"><tr><th></th><td class="small muted">回数</td><td class="small muted">入力トークン</td><td class="small muted">出力トークン</td><td class="small muted">時間</td><td class="small muted">目安（API 料金換算）</td><td class="small muted">エラー</td></tr>
      ${pr.usage_today.map((u) => `<tr><th>${h(u.agent)}</th><td>${u.n}</td><td>${(u.tin || 0).toLocaleString()}</td><td>${(u.tout || 0).toLocaleString()}</td>
        <td>${Math.round((u.secs || 0) / 60)}分</td><td>${u.cost ? "$" + u.cost : "―"}</td><td>${u.errors || 0}</td></tr>`).join("") || `<tr><td colspan="7" class="muted">きょうはまだ動いていません</td></tr>`}</table>
      <p class="small muted">契約の残りは公式の画面で確かめてください：<a href="https://claude.ai/settings/usage" target="_blank">Claude の使用量</a>・<a href="https://chatgpt.com/codex/settings/usage" target="_blank">Codex の使用量</a>。</p></div>`;
  document.querySelectorAll("[data-loginas]").forEach((b) => (b.onclick = async () => {
    const k = b.dataset.loginas;
    if (a.agents[k].config_dir && !confirm(`${a.agents[k].label} のログインを始めます。\nブラウザが開いたら、claude.ai で「${k} に使うアカウント」に切り替えてから許可してください。\n（今ブラウザで別のアカウントにログインしていると、そのアカウントになってしまいます）`)) return;
    b.disabled = true;
    const r = await api(`/api/agents/${k}/login-as`, { method: "POST" });
    document.querySelector(`[data-msg="${k}"]`).textContent = r.message;
    b.disabled = false;
  }));
  document.querySelectorAll("[data-model], [data-effort]").forEach((sel) => (sel.onchange = async () => {
    const k = sel.dataset.model || sel.dataset.effort, m = document.querySelector(`[data-mmsg="${k}"]`);
    m.textContent = "保存中…";
    try {
      await api(`/api/agents/${k}/model`, { method: "PUT", body: { model: document.querySelector(`[data-model="${k}"]`).value, effort: document.querySelector(`[data-effort="${k}"]`).value } });
      m.textContent = "保存しました（次に起きたときから）";
    } catch (e) { m.textContent = "保存できませんでした：" + e.message; }
  }));
  document.getElementById("recheck").onclick = async () => { await api("/api/agents/check", { method: "POST" }); viewAgents(); };
  document.getElementById("run").onchange = (e) => api("/api/agents/run", { method: "POST", body: { run: e.target.checked } });
  document.getElementById("saveAssign").onclick = async (e) => {
    const assign = {}, labels = {};
    document.querySelectorAll("[data-role]").forEach((s) => (assign[s.dataset.role] = s.value));
    document.querySelectorAll("[data-label]").forEach((i) => (labels[i.dataset.label] = i.value));
    e.target.disabled = true;
    try { await api("/api/staff/assign", { method: "PUT", body: { assign, labels } }); document.getElementById("assignMsg").textContent = "保存しました"; setTimeout(viewAgents, 700); }
    catch (err) { document.getElementById("assignMsg").textContent = "保存できませんでした：" + err.message; e.target.disabled = false; }
  };
  document.querySelectorAll("[data-log]").forEach((d) => (d.ontoggle = async () => {
    if (!d.open) return;
    d.querySelector("pre").textContent = await (await fetch(`/api/agents/${d.dataset.log}/log`)).text();
  }));
}

// ===== エラー（進み具合のタブ） =====
const RESOLVED = { 0: ["未対応", "open"], 1: ["直した", "sel"], 2: ["あとで成功（直ったとみなす）", "sel"] };
function errorsHTML(er) {
  const open = er.runs.filter((r) => !r.resolved).length;
  return `<h2>いま使えるもの・使えないもの</h2><div class="card"><table class="loaded">${er.health.map((x) => `<tr class="${x.ok ? "" : "ng"}"><td>${x.ok ? "✓" : "✖"}</td><th>${h(x.name)}</th><td class="small">${h(x.detail)}</td></tr>`).join("")}</table></div>
    <div class="card"><div class="row"><b>エラー：未対応 ${open} 件</b><span class="small muted">（全部で ${er.runs.length} 件）</span><span style="flex:1"></span><button class="primary" id="copyErr">報告をまとめてコピー</button></div>
      <p class="small muted">コピーした報告を、開発の Claude にそのまま貼ってください。</p></div>
    ${er.runs.map((r) => { const [lbl, cls] = RESOLVED[r.resolved || 0] || RESOLVED[0];
      const where = `${r.episode || ""} ${r.stage || (r.kind === "tool" ? "画面" : "作業")}`.trim();
      return `<div class="card ${r.resolved ? "resolved" : ""}"><div class="row"><span class="badge ${cls}">${lbl}</span><b>${h(where)}でエラー</b>
        <span class="small muted">${h(r.agent)}・${h((r.started_at || "").slice(5, 16))}・#${r.id}</span><span style="flex:1"></span>
        ${r.resolved ? `<button class="small" data-res="${r.id}/0">未対応に戻す</button>` : `<button class="small" data-res="${r.id}/1">直した</button>`}</div>
        <details><summary class="small">くわしく</summary><div class="small muted">${h(r.command)}</div><pre class="brief small">${h(r.error)}</pre></details></div>`; }).join("") || `<p class="muted">エラーはありません。</p>`}`;
}


// ===== 画面の下の帯：送ったものの様子（送信中・順番待ち・実行中・済み）。どの画面にいても見える =====
const TRACK_KEY = "tsuki_sent";
const loadSent = () => { try { return JSON.parse(localStorage.getItem(TRACK_KEY) || "[]"); } catch { return []; } };
const saveSent = (l) => { try { localStorage.setItem(TRACK_KEY, JSON.stringify(l.slice(-8))); } catch {} };
function track(item) { saveSent([...loadSent(), { ...item, at: Date.now() }]); sendBar(); }
let BAR_TIMER = null;
// 帯の場所とたたみ具合は、この PC のブラウザに覚えておく
function barPref(set) {
  let p = {};
  try { p = JSON.parse(localStorage.getItem("tsuki_sendbar") || "{}"); } catch {}
  if (set) { p = { ...p, ...set }; try { localStorage.setItem("tsuki_sendbar", JSON.stringify(p)); } catch {} }
  return p;
}
function placeBar(bar) {
  const p = barPref();
  if (p.x == null) return;
  const x = Math.min(Math.max(0, p.x), innerWidth - 120), y = Math.min(Math.max(0, p.y), innerHeight - 40);
  Object.assign(bar.style, { left: x + "px", top: y + "px", bottom: "auto" });
}
function dragBar(bar, handle) {
  handle.onpointerdown = (e) => {
    if (e.target.closest("button, a")) return;
    const r = bar.getBoundingClientRect(), dx = e.clientX - r.left, dy = e.clientY - r.top;
    handle.setPointerCapture(e.pointerId);
    handle.onpointermove = (m) => Object.assign(bar.style, { left: m.clientX - dx + "px", top: m.clientY - dy + "px", bottom: "auto" });
    handle.onpointerup = (u) => { handle.onpointermove = null; barPref({ x: u.clientX - dx, y: u.clientY - dy }); };
  };
}
async function sendBar() {
  clearTimeout(BAR_TIMER);
  let bar = document.getElementById("sendbar");
  if (!bar) { bar = document.createElement("div"); bar.id = "sendbar"; document.body.appendChild(bar); }
  const list = loadSent().filter((x) => !x.hidden && Date.now() - x.at < 24 * 3600e3);
  if (!list.length) { bar.style.display = "none"; return; }
  let busy = false;
  const rows = await Promise.all(list.slice(-4).reverse().map(async (x) => {
    let st = "確かめています…", cls = "wait";
    try {
      if (x.kind === "request") {
        const r = await api(`/api/requests/${x.id}`);
        if (r.status === "open") [st, cls] = [`順番待ち（${r.position}番目）`, "wait"];
        else if (r.status === "claimed") [st, cls] = [`実行中（${r.claimed_by}）`, "run"];
        else if (r.status === "done") [st, cls] = [`済み：${(r.result || "").slice(0, 60)}`, "done"];
        else [st, cls] = ["取り消しました", "done"];
      } else {
        const o = await api(`/api/episodes/${x.code}/overview`);
        const f = o.flows.find((f) => f.scene === x.sc);
        [st, cls] = f ? [f.label, f.stage === "done" ? "done" : f.stage === "director" ? "you" : "run"] : ["回しています…", "wait"];
      }
    } catch { [st, cls] = ["様子が読めません", "ng"]; }
    if (cls === "wait" || cls === "run") busy = true;
    return `<div class="sb ${cls}"><span class="sbdot"></span><span class="sbl">${h(x.label)}</span><b>${h(st)}</b><button class="small" data-hide="${x.at}" title="この行を消す">×</button></div>`;
  }));
  bar.style.display = "";
  const folded = barPref().folded;
  const nRun = rows.filter((r) => /class="sb (run|wait)"/.test(r)).length;
  bar.classList.toggle("folded", !!folded);
  bar.innerHTML = `<div class="row small sbhead" title="ここをつかんで動かせます"><span class="grip">⠿</span><b>送ったもの</b>
      ${folded ? `<span class="muted">${nRun ? `進行中 ${nRun}` : "すべて済み"}</span>` : `<a href="#/progress?t=queue">順番待ちを見る ›</a>`}
      <span style="flex:1"></span><button class="small" data-fold>${folded ? "ひらく" : "たたむ"}</button></div>${folded ? "" : rows.join("")}`;
  placeBar(bar);
  bar.querySelector("[data-fold]").onclick = () => { barPref({ folded: !folded }); sendBar(); };
  dragBar(bar, bar.querySelector(".sbhead"));
  bar.querySelectorAll("[data-hide]").forEach((b) => (b.onclick = () => { saveSent(loadSent().map((x) => (String(x.at) === b.dataset.hide ? { ...x, hidden: true } : x))); sendBar(); }));
  BAR_TIMER = setTimeout(sendBar, busy ? 3000 : 15000);
}
sendBar();

// ===== 字コンテのタブの上：シーンごとの工程と、監督のチェック（仮字コンテ・生成の前） =====
async function flowPanel(code) {
  const { flows } = await api(`/api/episodes/${code}/flows`);
  const box = document.createElement("div");
  box.className = "card flowpanel";
  const STEPS = ["仮字コンテ（演出）", "監督チェック", "字コンテ会議", "字コンテ", "プロンプト・素材", "監督の生成チェック", "480p", "映像会議", "監督"];
  const at = { rough: 0, rough_check: 1, rough_ok: 1, jikonte_meeting: 2, jikonte: 3, prep: 4, gate: 5, making: 6, remaking: 6, video_meeting: 7, director: 8, done: 9 };
  box.innerHTML = `<h2 style="margin:0 0 4px">シーンの工程 <span class="small muted">監督が「生成する」を押すまで、お金のかかる生成は回りません</span></h2>
    <div class="small muted">${STEPS.map((s, i) => `${i + 1}. ${s}`).join(" → ")}</div>
    ${flows.map((f) => {
      const mine = ["rough_check", "gate", "director"].includes(f.stage);
      const report = f.request && f.request.result ? `<div class="small report">${h(f.request.result).replace(/\n/g, "<br>")}</div>` : "";
      const btns = f.stage === "rough_check" || f.stage === "rough_ok"
        ? `${f.stage === "rough_check" ? `<button class="primary" data-ck="ok">仮字コンテ OK</button>` : ""}<button data-ck="now" title="ほかのシーンを待たずに字コンテ会議を開く">このシーンだけ先に会議へ</button><button data-ck="redo">直して</button>`
        : f.stage === "gate" ? `<button class="primary" data-ck="go">生成する（480p）</button><button data-ck="redo">直して</button>`
        : f.stage === "director" ? `<a class="btn primary" href="#/ep/${code}/decide">映像を見て決める ›</a>` : "";
      return `<div class="flowrow ${mine ? "mine" : ""}" data-sc="${h(f.scene)}"><div class="row"><b>${h(f.scene)}</b>
        <span class="badge ${mine ? "open" : f.stage === "done" ? "sel" : "proposed"}">${h(f.stage_label)}</span>
        <span class="small muted">${at[f.stage] ?? "?"}/9${f.request && f.request.status === "claimed" ? `・${h(f.request.claimed_by)} が作業中` : ""}</span></div>
        ${(f.stage === "rough_check" || f.stage === "gate") ? report : ""}
        ${btns ? `<div class="row">${btns}${f.stage !== "director" ? `<input type="text" class="cknote" placeholder="ひとこと（直してのときは必須。Enter で「直して」）" style="flex:1">` : ""}<span class="small muted ckmsg"></span></div>` : ""}</div>`;
    }).join("") || `<p class="small muted">まだ工程に入ったシーンはありません（「② シーン整理」で「このシーンでいく」を押すと始まります）</p>`}`;
  $view.insertBefore(box, $view.children[2] || null);
  box.querySelectorAll(".flowrow").forEach((row) => {
    const sc = row.dataset.sc, note = row.querySelector(".cknote"), msg = (t) => (row.querySelector(".ckmsg").textContent = t);
    const go = async (action) => {
      if (action === "redo" && !note.value.trim()) { msg("どう直してほしいか書いてください"); return; }
      if (action === "go" && !confirm(`${sc} の 480p ドラフトを生成します（お金がかかります）。よろしいですか？`)) return;
      msg("送信中…");
      try {
        const r = await api(`/api/episodes/${code}/flows/${sc}/check`, { method: "POST", body: { action, note: note.value.trim() } });
        if (r.request) track({ kind: "request", id: r.request, label: `${code} ${sc}：${{ redo: "直して", go: "480p 生成" }[action] || action}` });
        else track({ kind: "flow", code, sc, label: `${code} ${sc} の工程` });
        msg(r.opened && r.opened.length ? `全シーンの仮字コンテがそろったので、字コンテ会議を開きました（${r.opened.join("・")}）` : "送りました");
        setTimeout(route, 900);
      } catch (e) { msg("送れませんでした：" + e.message); }
    };
    row.querySelectorAll("[data-ck]").forEach((b) => (b.onclick = () => go(b.dataset.ck)));
    if (note) note.onkeydown = (e) => { if (e.key === "Enter" && !e.isComposing) { e.preventDefault(); go("redo"); } };
  });
}
