// ---------- AI の接続（ログイン）と、資料（AI が読むもの・ルール・AI の仕事） ----------

// ===== AI の接続 =====
async function viewAgents() {
  $view.innerHTML = `<h1>AI の接続</h1><p class="muted">確かめています…</p>`;
  const a = await api("/api/agents");
  const ROLE = { "芝居": "芝居（設定）", "演出": "演出", "見る": "見る", "まとめ": "制作進行" };
  $view.innerHTML = `<h1>AI の接続 <span class="muted small">この PC の Claude と Codex にログインしておくと、月灯スタジオが裏で AI を動かします</span></h1>
    <div class="agentgrid">${a.tools.map((t) => `<div class="card agentcard ${t.logged_in ? "ok" : "ng"}">
      <div class="row"><span class="dot"></span><b>${h(t.label)}</b><span style="flex:1"></span>
        <span class="badge ${t.logged_in ? "sel" : "open"}">${!t.installed ? "入っていません" : t.logged_in ? "ログイン済み" : "ログインしていません"}</span></div>
      <div class="small muted">${h(t.detail || "")}</div>
      <div class="row">${t.installed && !t.logged_in ? `<button class="primary" data-login="${t.tool}">ログインする</button>` : ""}
        ${t.installed && t.logged_in ? `<button data-login="${t.tool}">別のアカウントでログイン</button>` : ""}
        <button data-check>確かめる</button><span class="small muted" data-msg="${t.tool}"></span></div></div>`).join("")}</div>
    <h2>裏で動く AI <label class="small" style="margin-left:12px"><input type="checkbox" id="run" ${a.run_agents ? "checked" : ""}> 仕事が来たら自動で動かす</label></h2>
    <div class="agentgrid">${Object.entries(a.agents).map(([k, v]) => `<div class="card">
      <div class="row"><b>${h(v.label)}</b><span style="flex:1"></span><span class="badge ${v.running ? "proposed" : ""}">${v.running ? "作業中" : "待機"}</span></div>
      <div class="small">役：${v.roles.map((r) => ROLE[r] || r).join("・") || "―"}</div>
      ${v.last ? `<div class="small muted">前回：${h(v.last)}</div>` : ""}
      <details data-log="${k}"><summary class="small">作業の記録を見る</summary><pre class="brief small">読み込み中…</pre></details></div>`).join("")}</div>`;
  document.querySelectorAll("[data-login]").forEach((b) => (b.onclick = async () => {
    const r = await api(`/api/agents/${b.dataset.login}/login`, { method: "POST" });
    document.querySelector(`[data-msg="${b.dataset.login}"]`).textContent = r.message;
  }));
  document.querySelectorAll("[data-check]").forEach((b) => (b.onclick = () => viewAgents()));
  document.getElementById("run").onchange = (e) => api("/api/agents/run", { method: "POST", body: { run: e.target.checked } });
  document.querySelectorAll("[data-log]").forEach((d) => (d.ontoggle = async () => {
    if (!d.open) return;
    d.querySelector("pre").textContent = await (await fetch(`/api/agents/${d.dataset.log}/log`)).text();
  }));
}

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
