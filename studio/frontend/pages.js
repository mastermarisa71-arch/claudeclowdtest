// ---------- AI の接続（ログイン）と、資料（AI が読むもの・ルール・AI の仕事） ----------

// AI の接続は home.js

// ===== 資料 =====
async function viewDocs(params) {
  const tab = params.get("t") || "docs";
  const tabs = [["docs", "AI が読む資料"], ["rules", "ルール（AI が守ること）"], ["jobs", "AI の仕事"]];
  const head = `<h1>資料</h1><div class="row tabs">${tabs.map(([k, l]) => `<a class="btn ${k === tab ? "on" : ""}" href="#/docs?t=${k}">${l}</a>`).join("")}</div>`;
  if (tab === "rules") { await viewRules(); $view.querySelector("h1")?.remove(); $view.insertAdjacentHTML("afterbegin", head); return; }
  if (tab === "jobs") {
    const reqs = await api("/api/requests?status=open,claimed,done,cancelled");
    const ST = { open: ["まだ", "proposed"], claimed: ["作業中", "open"], done: ["済み", "sel"], cancelled: ["取り消し", ""] };
    $view.innerHTML = head + `<p class="small muted">制作進行や工程が積んだ仕事と、その結果。頼みごとは右下のチャットから。</p>
      ${reqs.map((r) => `<div class="card job"><div class="row"><span class="badge ${ST[r.status][1]}">${ST[r.status][0]}</span><b>#${r.id}</b>
        <span class="small muted">${h(r.episode || "全体")}　${h(r.claimed_by || "")}　${h((r.done_at || r.claimed_at || r.ts || "").slice(5, 16))}</span></div>
        <div class="small">${h(r.text).replace(/\n/g, "<br>")}</div>${r.result ? `<div class="small agent">結果：${h(r.result)}</div>` : ""}</div>`).join("") || `<p class="muted">まだありません。</p>`}`;
    return;
  }
  const docs = await api("/api/docs");
  $view.innerHTML = head + `
    <div class="card"><div class="drop" id="docDrop"><div class="dz"><b>AI に読んでほしい資料を落とす</b>（Word・PDF・テキスト・画像、何個でも）<br>
      <span class="small muted">「07_資料」に入り、制作進行が読んで、関係する所に反映します（反映の前に確かめます）</span></div></div>
      <div class="row"><input type="text" id="docNote" placeholder="何のために読んでほしいか（任意）　例：2話の新しい設定。キャラの口調が変わった" style="flex:1"><span class="small muted" id="docMsg"></span></div></div>
    <div class="docs">
      <div class="doclist">${docs.map((d) => `<details ${d.dir === "07_資料" || d.dir === "00_正本" ? "open" : ""}><summary><b>${h(d.label)}</b> <span class="small muted">${d.files.length}</span></summary>
        ${d.files.map((f) => `<a class="docfile ${f.text ? "" : "bin"}" data-p="${h(f.path)}">${h(f.name)}</a>`).join("") || `<div class="small muted">（まだない）</div>`}</details>`).join("")}</div>
      <div class="docview card"><p class="muted small">左の資料を押すと、ここに中身が出ます。</p></div></div>`;
  dropZone(document.getElementById("docDrop"), async (files) => {
    document.getElementById("docMsg").textContent = `${files.length} 件を入れています…`;
    const fd = new FormData(); files.forEach((f) => fd.append("files", f)); fd.append("note", document.getElementById("docNote").value);
    const r = await fetch("/api/docs/upload", { method: "POST", body: fd });
    document.getElementById("docMsg").textContent = r.ok ? "入れました。制作進行が読みます" : "入れられませんでした";
    setTimeout(() => viewDocs(params), 800);
  });
  document.getElementById("docDrop").querySelector("input").accept = "";
  document.querySelectorAll(".docfile").forEach((a) => (a.onclick = async () => {
    document.querySelectorAll(".docfile").forEach((x) => x.classList.toggle("on", x === a));
    const box = document.querySelector(".docview");
    if (a.classList.contains("bin")) { box.innerHTML = `<p class="small muted">${h(a.dataset.p)}（文字のファイルではないので、ここでは表示できません。AI は読めます）</p>`; return; }
    const t = await (await fetch(`/api/docs/read?path=${encodeURIComponent(a.dataset.p)}`)).text();
    box.innerHTML = `<div class="small muted">${h(a.dataset.p)}</div><div class="doctext">${md(t.replace(/^---[\s\S]*?---\n/, ""))}</div>`;
  }));
}

// ===== 進み具合：いま誰が何をしているか（その場で流れる）・順番待ち・エラー =====
let PROG_TIMER = null;
async function viewProgress(params) {
  clearTimeout(PROG_TIMER);
  const tab = params.get("t") || "now";
  const tabs = [["now", "いま動いている AI"], ["queue", "順番待ち"], ["log", "記録"], ["errors", "エラー"]];
  const [p, er] = await Promise.all([api("/api/progress"), api("/api/errors")]);
  const errN = er.runs.filter((r) => !r.resolved).length;
  const head = `<h1>進み具合 <span class="muted small">2秒ごとに新しくなります</span></h1><div class="row tabs">${tabs.map(([k, l]) =>
    `<a class="btn ${k === tab ? "on" : ""}" href="#/progress?t=${k}">${l}${k === "queue" && p.queue.length ? `<span class="cnt">${p.queue.length}</span>` : ""}${k === "errors" && errN ? `<span class="cnt">${errN}</span>` : ""}</a>`).join("")}</div>`;
  const keepScroll = [...document.querySelectorAll(".livebox")].map((b) => b.scrollHeight - b.scrollTop - b.clientHeight < 30);
  let body = "";
  if (tab === "now") {
    body = p.running.map((a, i) => `<div class="card runcard ${a.running ? "on" : ""}">
      <div class="row"><span class="dot"></span><b>${h(a.label)}</b><span class="small muted">役：${a.roles.join("・")}</span><span style="flex:1"></span>
        <span class="badge ${a.running ? "proposed" : a.rest ? "open" : ""}">${a.running ? `作業中（${h((a.since || "").slice(11, 16))}から）` : a.rest ? `休み（あと${Math.ceil(a.rest / 60)}分）` : "待機"}</span>
        ${!a.running && a.rest ? `<button class="small wake">すぐ起こす</button>` : ""}</div>
      ${a.jobs.map((j) => `<div class="small">いまの仕事：<b>#${j.id}</b> ${h(j.episode || "")} ${h(j.text)}</div>`).join("")}
      ${a.slots.map((s) => `<div class="small">いまの会議：#${s.round} ${h(s.episode)} ${h(s.target || "")} の ${h(s.role)}（${s.pass}周目）</div>`).join("")}
      ${a.last && !a.running ? `<div class="small muted">前回：${h(a.last)}</div>` : ""}
      <div class="livebox">${a.live.length ? a.live.map((l) => `<div class="ll ${/✖|⚠/.test(l) ? "bad" : /💬/.test(l) ? "say" : /🔧/.test(l) ? "tool" : ""}">${h(l)}</div>`).join("") : `<div class="small muted">（まだ何も流れていません）</div>`}</div>
    </div>`).join("");
  } else if (tab === "queue") {
    body = `<p class="small muted">上から順に、その役の AI が取って進めます。↑↓で順番を入れ替え、「中止」で作業中の AI を止め、「消す」で取り消せます。同じ仕事は二重に積まれません。</p>` + queueHTML(p.queue);
  } else if (tab === "log") {
    body = `<table class="loaded">${p.runs.map((r) => `<tr class="${r.status === "error" ? "ng" : ""}"><td>${r.status === "ok" ? "✓" : r.status === "running" ? "…" : "✖"}</td>
      <th>${h(r.agent)}</th><td class="small">${h((r.started_at || "").slice(5, 16))}　${r.seconds || 0}秒　トークン ${(r.tokens_in || 0).toLocaleString()}／${(r.tokens_out || 0).toLocaleString()}
      ${r.result ? `<div class="muted">${h(r.result.slice(0, 200))}</div>` : ""}${r.error ? `<div style="color:var(--red)">${h(r.error.slice(0, 300))}</div>` : ""}</td></tr>`).join("")}</table>`;
  } else {
    body = errorsHTML(er);
  }
  $view.innerHTML = head + body;
  bindQueue($view, () => viewProgress(params));
  document.querySelectorAll("[data-res]").forEach((b) => (b.onclick = async () => {
    const [id, v] = b.dataset.res.split("/"); await api(`/api/errors/${id}`, { method: "PATCH", body: { resolved: +v } }); viewProgress(params); }));
  document.querySelectorAll(".wake").forEach((b) => (b.onclick = async () => { await api("/api/agents/wake", { method: "POST" }); viewProgress(params); }));
  document.querySelectorAll(".livebox").forEach((b, i) => { if (keepScroll[i] !== false) b.scrollTop = b.scrollHeight; });
  document.getElementById("copyErr")?.addEventListener("click", async (e) => {
    try { await navigator.clipboard.writeText(er.report); e.target.textContent = "コピーしました"; }
    catch { const t = document.createElement("textarea"); t.value = er.report; document.body.appendChild(t); t.select(); document.execCommand("copy"); t.remove(); e.target.textContent = "コピーしました"; }
  });
  if (location.hash.startsWith("#/progress") && tab !== "errors") PROG_TIMER = setTimeout(() => location.hash.startsWith("#/progress") && viewProgress(params), tab === "queue" ? 5000 : 2000);
}
