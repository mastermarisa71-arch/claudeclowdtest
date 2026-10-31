// ---------- 美術・素材 ----------
// 素材庫（話数をまたいで使う）：監督は画像を落とすだけ。何の素材か・注意書きは AI が画像を見て書く。
// 話数の「美術・素材」：その話で要る背景（AI が字コンテから並べる）に、AI が素材庫から合うものを結ぶ。足りないものだけ監督が落とす。
// 生成の背景にするか雰囲気だけにするかは、カットごとに生成の係が決める（監督は決めない）。
function dropZone(el, onFiles, multiple = true) {
  const input = document.createElement("input");
  input.type = "file"; input.accept = "image/*,video/*"; input.multiple = multiple; input.hidden = true;
  el.appendChild(input);
  el.onclick = (e) => { if (e.target.tagName !== "INPUT" && e.target.tagName !== "SELECT" && e.target.tagName !== "OPTION") input.click(); };
  input.onchange = () => input.files.length && onFiles([...input.files]);
  el.ondragover = (e) => { e.preventDefault(); el.classList.add("over"); };
  el.ondragleave = () => el.classList.remove("over");
  el.ondrop = (e) => { e.preventDefault(); el.classList.remove("over"); e.dataTransfer.files.length && onFiles([...e.dataTransfer.files]); };
}
async function sendLibrary(files, extra = {}) {
  const fd = new FormData();
  files.forEach((f) => fd.append("files", f));
  Object.entries(extra).forEach(([k, v]) => fd.append(k, v));
  const r = await fetch("/api/library", { method: "POST", body: fd });
  return r.ok;
}
const KINDS = { bg: "背景", character: "キャラの設定資料", prop: "小物", layout: "配置図", effect: "エフェクト", "": "（AI が見ています）" };

// ===== 素材庫 =====
async function viewLibrary(params) {
  const [lib, kinds] = await Promise.all([api("/api/library"), api("/api/library/kinds")]);
  const tab = (params && params.get("k")) ?? (localStorageGet("lib.tab") || "all");
  const tabs = [["all", "すべて"], ...Object.entries(kinds), ["", "仕分け待ち"]];
  const count = (k) => (k === "all" ? lib.length : lib.filter((a) => (a.kind || "") === k).length);
  const shown = tab === "all" ? lib : lib.filter((a) => (a.kind || "") === tab);
  const isRef = tab === "reference";
  $view.innerHTML = `<h1>素材庫 <span class="muted small">話数をまたいで使う素材。種類ごとに置き場所があります。何の素材か・注意書きは AI が画像を見て書きます</span></h1>
    <div class="libtabs">${tabs.map(([k, l]) => `<a class="btn ${k === tab ? "on" : ""}" data-k="${k}">${h(l)} <span class="small muted">${count(k)}</span></a>`).join("")}</div>
    <div class="card"><div class="drop big" id="libDrop"><div class="dz"><b>${tab === "all" || tab === "" ? "ここに落とす（種類は AI が分けます）" : `「${h(kinds[tab])}」に落とす`}</b>（何枚でも）<br>
        <span class="small muted">${isRef ? "目指すルックや映像表現の参考（他作品の画、写真、色見本、動画）。生成には使わず、AI が目指す見た目として読みます" : "レンダー・撮処理したもの、キャラの設定資料など"}</span></div></div>
      <div class="row"><input type="text" id="libHint" placeholder="${isRef ? "どこを参考にしたいか（任意）　例：夜の店内の色。窓の光の入り方。手持ち風のカメラ" : "ひとこと（任意）　例：店内の夕方、カメラA"}" style="flex:1"><span class="small muted" id="libMsg"></span></div></div>
    <div class="libgrid">${shown.map((a) => `<div class="card libitem" data-a="${a.id}">
      ${/\.(mp4|mov|webm)$/i.test(a.file_path) ? `<video src="/media/${encodeURI(a.file_path)}" muted controls></video>` : `<img src="/media/${encodeURI(a.file_path)}">`}
      <div class="row"><input type="text" class="lname" value="${h(a.name)}">
        <select class="lkind">${[["", "仕分け待ち"], ...Object.entries(kinds)].map(([k, l]) => `<option value="${k}" ${k === (a.kind || "") ? "selected" : ""}>${h(l)}</option>`).join("")}</select></div>
      ${a.place ? `<div class="small">${h(a.place)}</div>` : ""}
      ${a.hint ? `<div class="small">監督：${h(a.hint)}</div>` : ""}
      ${a.description ? `<div class="small muted">AI：${h(a.description)}</div>` : a.described ? "" : `<div class="small muted">AI が画像を見て書きます…</div>`}
      <div>${Object.entries(a.notes || {}).filter(([, v]) => v).map(([k, v]) => `<span class="nchip">${h({ look: "見るところ", break: "崩れやすい", avoid: "気をつける", light: "光", comp: "撮処理" }[k] || k)}：${h(v)}</span>`).join("")}</div>
      ${a.used_in.length ? `<div class="small">使う所：${a.used_in.map(h).join("、")}</div>` : ""}
      <div class="row"><span style="flex:1"></span><button class="small ldel">使わない</button></div></div>`).join("") || `<p class="muted">まだありません。</p>`}</div>`;
  document.querySelectorAll(".libtabs [data-k]").forEach((b) => (b.onclick = () => { localStorageSet("lib.tab", b.dataset.k); viewLibrary(new URLSearchParams(`k=${b.dataset.k}`)); }));
  dropZone(document.getElementById("libDrop"), async (files) => {
    document.getElementById("libMsg").textContent = `${files.length} 件を入れています…`;
    await sendLibrary(files, { hint: document.getElementById("libHint").value, kind: tab === "all" ? "" : tab });
    viewLibrary(new URLSearchParams(`k=${tab}`));
  });
  document.querySelectorAll(".libitem").forEach((el) => {
    el.querySelector(".lname").onchange = (e) => api(`/api/library/${el.dataset.a}`, { method: "PATCH", body: { name: e.target.value } });
    el.querySelector(".lkind").onchange = async (e) => { await api(`/api/library/${el.dataset.a}`, { method: "PATCH", body: { kind: e.target.value } }); viewLibrary(new URLSearchParams(`k=${tab}`)); };
    el.querySelector(".ldel").onclick = async () => { await api(`/api/library/${el.dataset.a}`, { method: "PATCH", body: { active: 0 } }); viewLibrary(new URLSearchParams(`k=${tab}`)); };
  });
}

// ===== 話数の美術・素材 =====
async function viewArt(code) {
  const [a, plans, lib] = await Promise.all([api(`/api/episodes/${code}/art`), api("/api/plans"), api("/api/library")]);
  const camMap = (o) => {     // 見取り図の上に、カメラの位置と向き
    const p = plans[o.plan];
    if (!p || !o.camera_xy) return "";
    const [cx, cy, ang] = o.camera_xy, W = 160, H = 107;
    const rad = ((ang < 0 ? 90 : ang) - 90) * Math.PI / 180;
    return `<svg viewBox="0 0 ${W} ${H}" class="minimap">
      <rect width="${W}" height="${H}" class="floor"/>${(p.areas || []).map((r) => `<rect x="${r.x * W}" y="${r.y * H}" width="${r.w * W}" height="${r.h * H}" class="${r.solid ? "solid" : r.door ? "door" : "ar"}"/>`).join("")}
      ${ang < 0 ? `<circle cx="${cx * W}" cy="${cy * H}" r="6" class="cam"/>` : `<path d="M${cx * W},${cy * H} l${Math.cos(rad - 0.45) * 40},${Math.sin(rad - 0.45) * 40} l${Math.cos(rad + 0.45) * 40 - Math.cos(rad - 0.45) * 40},${Math.sin(rad + 0.45) * 40 - Math.sin(rad - 0.45) * 40} z" class="fov"/>
      <circle cx="${cx * W}" cy="${cy * H}" r="5" class="cam"/>`}<text x="${cx * W}" y="${cy * H - 8}" class="ct">${h(o.camera)}</text></svg>`;
  };
  const missing = a.orders.filter((o) => o.status === "open").length;
  $view.innerHTML = `${epTabs(code, "art")}<h1>美術・素材 <span class="muted small">この話で要る背景。AI が字コンテから並べ、<a href="#/library">素材庫</a>から合うものを結びます。足りないものだけ落としてください</span></h1>
    <div class="card row"><span>要る背景 ${a.orders.length}件・結んだもの ${a.orders.length - missing}件・<b>足りない ${missing}件</b></span><span style="flex:1"></span>
      <button id="replan">字コンテから並べ直す</button></div>
    <div class="orders">${a.orders.map((o) => `<div class="card order ${o.status}" data-o="${o.id}">
      <div class="row"><b>${h(o.code)}</b><span class="badge ${o.status === "delivered" ? "sel" : "proposed"}">${o.status === "delivered" ? "結んだ" : o.status === "hold" ? "使わない" : "足りない"}</span>
        <span class="small">${h(o.place)}・${o.camera ? "カメラ" + h(o.camera) : "カメラ位置なし"}・ルック${h(o.look || "―")}</span>
        <span style="flex:1"></span><span class="small muted">${o.scenes.join("・")}　${o.cuts.length}コマ</span></div>
      <div class="ogrid">
        <div>${camMap(o)}<div class="small owhat">${h(o.what)}</div>
          <details><summary class="small">使うコマ（${o.cuts.length}）</summary>${o.cuts.map((c) => `<div class="small"><a href="#/ep/${code}/vcon?cut=${c.id}">${h(c.code)}</a> ${h(c.picture).slice(0, 40)}</div>`).join("")}</details></div>
        <div><div class="drop ${o.asset ? "has" : ""}">${o.asset ? `<img src="/media/${encodeURI(o.asset.file_path)}"><div class="small">${h(o.asset.name)}</div>`
          : `<div class="dz">足りない背景<br><span class="small muted">ここに落とすと素材庫に入り、この背景に結びます</span></div>`}</div>
          <select class="pick"><option value="">素材庫から選ぶ…</option>${lib.filter((x) => !x.kind || x.kind === "bg").map((x) => `<option value="${x.id}" ${o.asset_id === x.id ? "selected" : ""}>${h(x.name)}${x.place ? "（" + h(x.place) + "）" : ""}</option>`).join("")}</select></div>
      </div>
      <div class="row"><span class="small muted omsg"></span><span style="flex:1"></span>${o.status !== "hold" ? `<button class="hold small">この背景は使わない</button>` : `<button class="unhold small">使う</button>`}</div>
    </div>`).join("") || `<p class="muted">まだありません。字コンテができると AI が並べます（「字コンテから並べ直す」でも）。</p>`}</div>`;
  document.getElementById("replan").onclick = async () => { await api(`/api/episodes/${code}/art/plan`, { method: "POST" }); route(); };
  document.querySelectorAll(".order").forEach((card) => {
    dropZone(card.querySelector(".drop"), async (files) => {
      card.querySelector(".omsg").textContent = "入れています…";
      await sendLibrary(files.slice(0, 1), { order_id: card.dataset.o });
      route();
    }, false);
    card.querySelector(".pick").onchange = async (e) => { if (!e.target.value) return;
      await api(`/api/art/orders/${card.dataset.o}/link`, { method: "POST", body: { asset_id: +e.target.value } }); route(); };
    card.querySelector(".hold")?.addEventListener("click", async () => { await api(`/api/art/orders/${card.dataset.o}`, { method: "PATCH", body: { status: "hold" } }); route(); });
    card.querySelector(".unhold")?.addEventListener("click", async () => { await api(`/api/art/orders/${card.dataset.o}`, { method: "PATCH", body: { status: "open" } }); route(); });
  });
}
