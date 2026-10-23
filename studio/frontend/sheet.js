// ---------- シーン整理：脚本と字コンテの間。シーンごとに「何が変わるか」「誰が何をしたくて、何をするか」 ----------
// 監督は文章を読み込むより、変化（前→後）・キャラの温度・区切りの帯を見て、ちがうところを押して一言で返す。
async function viewSheet(code) {
  const { episode: ep, scenes } = await api(`/api/episodes/${code}/scenes`);
  const total = scenes.reduce((s, x) => s + (x.target_seconds || 0), 0) || 1;
  const dots = (n) => `<span class="dots">${[1, 2, 3, 4, 5].map((i) => `<i class="${i <= (+n || 0) ? "on" : ""}"></i>`).join("")}</span>`;
  const hue = (i) => `hsl(${(i * 47) % 360} 30% 40%)`;
  const done = scenes.filter((x) => x.status === "approved").length;
  $view.innerHTML = `${epTabs(code, "sheet")}<h1>シーン整理 <span class="muted small">脚本 → <b>シーン整理</b> → 字コンテ。ここで決めた変化と芝居から、カットの意図を作ります。ちがうところを押して、一言（🎤）で返してください</span></h1>
    <div class="sheetbar">${scenes.map((x, i) => `<a data-jump="${h(x.code)}" style="width:${(100 * (x.target_seconds || 0)) / total}%;background:${hue(i)}"
      class="${x.status === "approved" ? "ok" : ""}" title="${h(x.code)} ${h(x.change_before)} → ${h(x.change_after)}">${h(x.code)}</a>`).join("")}</div>
    <p class="small muted">${done} / ${scenes.length} シーン承認済み　帯の幅＝目標尺（合計 ${total}秒 / 話数の目標 ${ep.target_seconds}秒）</p>
    ${scenes.map((x, i) => `<div class="card scene" id="sc-${h(x.code)}" data-sc="${h(x.code)}" style="border-left:6px solid ${hue(i)}">
      <div class="row"><h2 style="margin:0">${h(x.code)}</h2>
        <span class="muted">${h(x.place)}・${h(x.time)}　${x.target_seconds}秒</span>
        <span class="badge ${x.status === "approved" ? "sel" : "proposed"}">${x.status === "approved" ? "承認済み" : "確認待ち"}</span>
        <span style="flex:1"></span><a class="small" href="#/ep/${code}?scene=${h(x.code)}">Vコンで見る</a></div>
      <div class="pick change" data-what="変化">
        <div class="before">${h(x.change_before) || "<span class='muted'>（前）未整理</span>"}</div>
        <div class="arrow">➜</div>
        <div class="after">${h(x.change_after) || "<span class='muted'>（後）未整理</span>"}</div>
      </div>
      ${x.turn ? `<div class="pick small" data-what="きっかけ"><b>きっかけ</b>　${h(x.turn)}</div>` : ""}
      <div class="pick small" data-what="見せたいもの"><b>見せたいもの</b>　${h(x.purpose)}</div>
      ${x.characters.length ? `<div class="chars">${x.characters.map((c) => `<div class="pick char" data-what="${h(c.name)}">
        <div class="row"><b>${h(c.name)}</b>${dots(c.tension)}</div>
        <div class="small"><span class="lbl">したい</span>${h(c.want)}</div>
        <div class="small"><span class="lbl">する</span>${h(c.does)}</div>
        <div class="small muted"><span class="lbl">内心</span>${h(c.inner)}</div></div>`).join("")}</div>` : ""}
      ${x.beats.length ? `<div class="beats">${x.beats.map((b, k) => `<div class="pick beat" data-what="区切り${k + 1}"
        style="flex:${+b.seconds || 1}" title="${h(b.why)}"><span class="sec">${h(b.seconds)}s</span><b>${h(b.who)}</b> ${h(b.does)}
        ${b.why ? `<div class="why">${h(b.why)}</div>` : ""}</div>`).join("")}</div>` : ""}
      ${x.blocking ? `<div class="pick small muted" data-what="動線"><b>立ち位置と動線</b>　${h(x.blocking)}</div>` : ""}
      <details data-script="${h(x.code)}"><summary class="small">脚本を見る</summary><div class="script small muted">読み込み中…</div></details>
      <div class="reply">
        <div class="small muted" data-picked>直したいところを押すと、ここに入ります</div>
        <textarea placeholder="例：あかねはもっと隠そうとしてほしい。打ち明けるのは最後の一言だけ"></textarea>
        <div class="row"><button class="primary" data-ok>このシーンでいく</button><button data-ng>直してほしい</button><span class="small muted" data-msg></span></div>
      </div>
    </div>`).join("") || `<p class="muted">まだシーン整理がありません。エージェントが脚本を読んで作ります（<code>scene-sheet</code>）。</p>`}`;

  document.querySelectorAll(".scene").forEach((card) => {
    const sc = card.dataset.sc, picked = new Set();
    const show = () => (card.querySelector("[data-picked]").textContent = picked.size ? `直したいところ：${[...picked].join("・")}` : "直したいところを押すと、ここに入ります");
    card.querySelectorAll(".pick").forEach((el) => (el.onclick = () => {
      const w = el.dataset.what;
      picked.has(w) ? picked.delete(w) : picked.add(w);
      el.classList.toggle("picked", picked.has(w));
      show();
      if (picked.has(w)) card.querySelector("textarea").focus();
    }));
    card.querySelector("details").ontoggle = async (e) => {
      const box = card.querySelector(".script");
      if (!e.target.open || box.dataset.loaded) return;
      const r = await api(`/api/episodes/${code}/scenes/${sc}/script`);
      box.dataset.loaded = 1;
      box.innerHTML = r.found ? `<b>${h(r.heading)}</b><br>${r.lines.map(h).join("<br>")}` : "脚本の範囲がまだ指定されていません";
    };
    const send = async (ok) => {
      const text = card.querySelector("textarea").value.trim();
      if (!ok && !text && !picked.size) { card.querySelector("[data-msg]").textContent = "どこを直すか押すか、一言書いてください"; return; }
      await api(`/api/episodes/${code}/scenes/${sc}`, { method: "PATCH", body: { status: ok ? "approved" : "review" } });
      if (text || picked.size || !ok)
        await api("/api/reviews", { method: "POST", body: { target_type: "episode", target_id: ep.id, verdict: ok ? "良い" : "修正",
          tags: ["意図", ...(picked.size ? ["芝居"] : [])], comment: `[シーン整理 ${sc}${picked.size ? "・" + [...picked].join("・") : ""}] ${text || (ok ? "このままでいい" : "")}` } });
      route();
    };
    card.querySelector("[data-ok]").onclick = () => send(true);
    card.querySelector("[data-ng]").onclick = () => send(false);
  });
  document.querySelectorAll("[data-jump]").forEach((a) => (a.onclick = () => document.getElementById(`sc-${a.dataset.jump}`).scrollIntoView({ behavior: "smooth" })));
  addMics();
  const target = new URLSearchParams(location.hash.split("?")[1] || "").get("scene");
  if (target) document.getElementById(`sc-${target}`)?.scrollIntoView();
}
