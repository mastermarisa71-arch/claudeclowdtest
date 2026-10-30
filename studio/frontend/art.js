// ---------- 美術・素材：監督がレンダー・撮処理した素材を、どのコマにどう使うかと一緒に渡す ----------
// AI が字コンテから「要る背景（場所 × カメラ位置 × ルック）」を並べる。監督はそこに素材を落として、注意書きをつける。
// 生成の係は、そのコマの背景に渡された素材を使い、注意書きを守る。キャラ・小物なども下の「ほかの素材」から渡せる。
async function viewArt(code) {
  const [a, plans] = await Promise.all([api(`/api/episodes/${code}/art`), api("/api/plans")]);
  const KIND = { bg: "背景", character: "キャラの設定資料", prop: "小物", layout: "配置図", effect: "エフェクト" };
  const ST = { open: ["まだ", "proposed"], delivered: ["渡し済み", "sel"], hold: ["使わない", ""] };
  const others = a.materials.filter((m) => !m.order_id);
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
  const noteForm = (kind, notes = {}) => `<div class="nform">${(a.note_fields[kind] || []).map(([k, l, ex]) =>
      `<label>${h(l)}<textarea data-n="${k}" data-mic="1" rows="1" placeholder="例：${h(ex)}">${h(notes[k] || "")}</textarea></label>`).join("")}
    <label>使い方<select data-use>${Object.entries(a.uses).map(([k, l]) => `<option value="${k}">${h(l)}</option>`).join("")}</select></label></div>`;
  $view.innerHTML = `${epTabs(code, "art")}<h1>美術・素材 <span class="muted small">レンダー・撮処理した素材を、使うコマと注意書きをつけて渡します。生成の係は、そのコマにこの素材を使います</span></h1>
    <div class="card row"><span class="small">AI が字コンテから、要る背景を「場所 × カメラ位置 × ルック」でまとめています（${a.orders.length}件・渡し済み ${a.orders.filter((o) => o.status === "delivered").length}）。
      字コンテが変わったら並べ直してください（渡し済みは残ります）。</span><span style="flex:1"></span><button id="replan">字コンテから並べ直す</button></div>
    <div class="orders">${a.orders.map((o) => `<div class="card order ${o.status}" data-o="${o.id}">
      <div class="row"><b>${h(o.code)}</b><span class="badge ${ST[o.status][1]}">${ST[o.status][0]}</span><span class="small">${h(o.place)}・${o.camera ? "カメラ" + h(o.camera) : "カメラ位置なし"}・ルック${h(o.look || "―")}</span>
        <span style="flex:1"></span><span class="small muted">${o.scenes.join("・")}　${o.cuts.length}コマ</span></div>
      <div class="ogrid">
        <div>${camMap(o)}<div class="small owhat">${h(o.what)}</div>
          <details><summary class="small">使うコマ（${o.cuts.length}）</summary>${o.cuts.map((c) => `<div class="small"><a href="#/ep/${code}/vcon?cut=${c.id}">${h(c.code)}</a> ${h(c.picture).slice(0, 40)}</div>`).join("")}</details></div>
        <div class="drop ${o.asset ? "has" : ""}">${o.asset ? `<img src="/media/${encodeURI(o.asset.file_path)}">` : `<div class="dz">ここに素材の画像を落とす<br><span class="small muted">（または押して選ぶ）</span></div>`}
          <input type="file" accept="image/*,video/*" hidden></div>
      </div>
      ${o.asset ? `<div class="small given"><b>${h(a.uses[o.asset.use] || "")}</b>　${Object.entries(o.asset.notes).filter(([, v]) => v).map(([k, v]) =>
        `<span class="nchip">${h((a.note_fields.bg.find((f) => f[0] === k) || [k, k])[1])}：${h(v)}</span>`).join("")}</div>` : ""}
      <details class="notes"><summary class="small">注意書き${o.asset ? "（差し替えるときに書き直す）" : "（素材を落とすと開きます）"}</summary>${noteForm("bg", o.asset?.notes)}</details>
      <div class="row"><button class="primary send" disabled>この素材を渡す</button>${o.status !== "hold" ? `<button class="hold small">この背景は使わない</button>` : `<button class="unhold small">使う</button>`}<span class="small muted omsg"></span></div>
    </div>`).join("") || `<p class="muted">まだありません。「字コンテから並べ直す」を押してください。</p>`}</div>
    <h2>ほかの素材（キャラの設定資料・小物・配置図・エフェクト）</h2>
    <div class="card order other" data-o="">
      <div class="row"><label>種類<select id="okind">${Object.entries(KIND).filter(([k]) => k !== "bg").map(([k, l]) => `<option value="${k}">${h(l)}</option>`).join("")}</select></label>
        <label>名前<input type="text" id="oname" placeholder="あかね／お客様ノート"></label>
        <label>使うシーン<input type="text" id="oscenes" placeholder="S1,S3,S8（空なら全部）"></label></div>
      <div class="ogrid"><div class="nbox">${noteForm("character")}</div>
        <div class="drop"><div class="dz">ここに素材を落とす</div><input type="file" accept="image/*,video/*" hidden></div></div>
      <div class="row"><button class="primary send" disabled>この素材を渡す</button><span class="small muted omsg"></span></div></div>
    ${others.map((m) => `<div class="card mat"><img src="/media/${encodeURI(m.file_path)}"><div><b>${h(m.name)}</b> <span class="small muted">${h(KIND[m.kind] || m.kind)}・${m.scenes.join("・") || "全部"}・${h(a.uses[m.use] || "")}</span>
      <div class="small">${Object.entries(m.notes).filter(([, v]) => v).map(([, v]) => `<span class="nchip">${h(v)}</span>`).join("")}</div></div></div>`).join("")}`;

  document.getElementById("replan").onclick = async () => { await api(`/api/episodes/${code}/art/plan`, { method: "POST" }); route(); };
  document.getElementById("okind").onchange = (e) => (document.querySelector(".other .nbox").innerHTML = noteForm(e.target.value));
  document.querySelectorAll(".order").forEach((card) => {
    const drop = card.querySelector(".drop"), input = drop.querySelector("input"), send = card.querySelector(".send");
    let file = null;
    const pick = (f) => { file = f; send.disabled = !f; card.querySelector(".notes")?.setAttribute("open", "");
      drop.innerHTML = `<img src="${URL.createObjectURL(f)}"><div class="small muted">${h(f.name)}（まだ渡していません）</div>`; drop.appendChild(input); };
    drop.onclick = () => input.click();
    input.onchange = () => input.files[0] && pick(input.files[0]);
    drop.ondragover = (e) => { e.preventDefault(); drop.classList.add("over"); };
    drop.ondragleave = () => drop.classList.remove("over");
    drop.ondrop = (e) => { e.preventDefault(); drop.classList.remove("over"); e.dataTransfer.files[0] && pick(e.dataTransfer.files[0]); };
    send.onclick = async () => {
      const fd = new FormData(), notes = {};
      card.querySelectorAll("[data-n]").forEach((t) => (notes[t.dataset.n] = t.value.trim()));
      fd.append("file", file); fd.append("notes", JSON.stringify(notes)); fd.append("use", card.querySelector("[data-use]").value);
      if (card.dataset.o) { fd.append("order_id", card.dataset.o); fd.append("kind", "bg"); }
      else { fd.append("kind", document.getElementById("okind").value); fd.append("name", document.getElementById("oname").value);
        fd.append("scenes", document.getElementById("oscenes").value.replace(/\s/g, "")); }
      const r = await fetch(`/api/episodes/${code}/art/deliver`, { method: "POST", body: fd });
      card.querySelector(".omsg").textContent = r.ok ? "渡しました。生成の係はこの素材と注意書きを使います" : "渡せませんでした";
      if (r.ok) setTimeout(route, 700);
    };
    card.querySelector(".hold")?.addEventListener("click", async () => { await api(`/api/art/orders/${card.dataset.o}`, { method: "PATCH", body: { status: "hold" } }); route(); });
    card.querySelector(".unhold")?.addEventListener("click", async () => { await api(`/api/art/orders/${card.dataset.o}`, { method: "PATCH", body: { status: "open" } }); route(); });
  });
  addMics();
}
