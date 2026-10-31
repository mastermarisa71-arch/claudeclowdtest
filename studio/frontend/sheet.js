// ---------- シーン整理：脚本と字コンテの間で「あらすじを立てる」。この話の芯 → 物語の流れ → シーンごとのブロック ----------
// シーンのブロック：① 映像で伝えたいこと ② 変化 ③ あらすじ ④ キャラ。AI（演出）が下書きし、監督がその場で直す（直した欄は正）。
// 基本は AI が案を出し、監督が選ぶ／自分の案を出す。
// - 展開のカーブ：区切りごとの高さと山場。点を上下にドラッグで直す、ダブルクリックで山場の名前
// - 配置図：区切りごとのキャラの位置。コマをドラッグで直す、▶ で区切りを順に動かして見る
// - 2択：AI が迷ったところを A／B で聞く。選んだものを覚え、「キャラの決まりにする」とキャラのノートに残る
const CHAR_COLOR = { "あかね": "#e07a7a", "朔奈": "#b49ae0", "まひる": "#f0b45a", "海凪": "#7fa6d9", "暁": "#f08a4a",
  "おばあ": "#c9b28a", "ステラ": "#888", "先輩": "#7fc79a", "後輩": "#9fd0c0" };
const ccolor = (n) => CHAR_COLOR[n] || "#aaa";
const sceneHue = (i) => `hsl(${(i * 47) % 360} 30% 40%)`;

// 監督がその場で直す欄。AI の下書きか、監督が直したか（正）を出す
function edBlock(field, label, value, human, opts = {}) {
  return `<div class="ed ${opts.cls || ""}" data-field="${field}">
    <div class="edl"><b>${label}</b>${opts.hint ? `<span class="small muted">　${opts.hint}</span>` : ""}
      <span class="who ${human ? "human" : ""}">${human ? "監督が直した" : "AI の下書き"}</span><button class="edbtn" title="直す">✎</button></div>
    <div class="edv">${value ? h(value).replace(/\n/g, "<br>") : `<span class="muted">（まだ）</span>`}</div></div>`;
}
// 欄を押すと、その場で直せる（保存すると「監督が直した」になり、AI は書き換えない）
function bindEditors(root, save) {
  root.querySelectorAll(".ed[data-field]").forEach((el) => {
    const open = () => {
      if (el.querySelector("textarea")) return;
      const v = el.querySelector(".edv");
      const old = v.innerText.trim() === "（まだ）" ? "" : v.innerText.trim();
      v.innerHTML = `<textarea rows="${Math.max(2, Math.ceil(old.length / 40))}">${h(old)}</textarea>
        <div class="row"><button class="primary edsave">保存</button><button class="edcancel">やめる</button><span class="small muted">保存すると AI に伝わり、この欄は監督の版が正になります</span></div>`;
      addMics();
      const ta = v.querySelector("textarea"); ta.focus();
      v.querySelector(".edcancel").onclick = (e) => { e.stopPropagation(); v.innerHTML = old ? h(old).replace(/\n/g, "<br>") : `<span class="muted">（まだ）</span>`; };
      v.querySelector(".edsave").onclick = async (e) => {
        e.stopPropagation();
        const val = ta.value.trim();
        if (val !== old) { await save(el.dataset.field, val, el); el.querySelector(".who").className = "who human"; el.querySelector(".who").textContent = "監督が直した"; }
        v.innerHTML = val ? h(val).replace(/\n/g, "<br>") : `<span class="muted">（まだ）</span>`;
      };
    };
    el.querySelector(".edbtn").onclick = open;
    el.querySelector(".edv").onclick = open;
  });
}

async function viewSheet(code) {
  const [{ episode: ep, scenes }, choices] = await Promise.all([api(`/api/episodes/${code}/scenes`), api(`/api/choices?episode=${code}`)]);
  const total = scenes.reduce((s, x) => s + (x.target_seconds || 0), 0) || 1;
  const dots = (n) => `<span class="dots">${[1, 2, 3, 4, 5].map((i) => `<i class="${i <= (+n || 0) ? "on" : ""}"></i>`).join("")}</span>`;
  const done = scenes.filter((x) => x.status === "approved").length;
  const epHuman = JSON.parse(ep.human_fields || "[]");
  const live = scenes;
  $view.innerHTML = `${epTabs(code, "sheet")}<h1>シーン整理 <span class="muted small">脚本 → <b>シーン整理（あらすじを立てる）</b> → 字コンテ・Vコン。AI（演出）が下書きし、監督がその場で直します</span></h1>
    <div class="card story">
      ${edBlock("theme", "この話の芯", ep.theme, epHuman.includes("theme"), { hint: "映像で伝えたいこと（1〜2文）", cls: "theme" })}
      ${edBlock("story_flow", "物語の流れ", ep.story_flow, epHuman.includes("story_flow"), { hint: "シーンをまたいで、どう転がっていくか" })}
      <div class="chain">${live.map((x, i) => `<a class="blk ${x.status === "approved" ? "ok" : ""}" data-jump="${h(x.code)}" style="border-color:${sceneHue(i)};flex:${Math.max(4, x.target_seconds || 4)}">
        <span class="bc" style="background:${sceneHue(i)}">${h(x.code)}</span><span class="bt">${h(x.change_after || x.purpose || "")}</span></a>`).join("")}</div>
      <div class="row"><span class="small muted">${done} / ${scenes.length} シーン承認済み　ブロックの幅＝目標尺（合計 ${total}秒 / 目標 ${ep.target_seconds}秒）。押すとそのシーンへ</span><span style="flex:1"></span>
        <button id="askDraft" title="演出の役の AI に、脚本から下書きを頼む（監督が直した欄は書き換えない）">AI（演出）に下書きを頼む</button><span class="small muted" id="draftMsg"></span></div>
    </div>
    <details class="card curvecard"><summary><b>展開のカーブ（山場）</b><span class="small muted">　点を上下にドラッグで高さ、ダブルクリックで山場（★）の名前</span></summary>
      <div class="row"><span style="flex:1"></span><span class="charchips"></span></div><div class="curve"></div></details>
    ${scenes.map((x, i) => `<div class="card scene" id="sc-${h(x.code)}" data-sc="${h(x.code)}" style="border-left:6px solid ${sceneHue(i)}">
      <div class="row"><h2 style="margin:0">${h(x.code)}</h2>
        <span class="muted">${h(x.place)}・${h(x.time)}　${x.target_seconds}秒</span>
        <span class="badge ${x.status === "approved" ? "sel" : "proposed"}">${x.status === "approved" ? "承認済み" : "確認待ち"}</span>
        <span style="flex:1"></span><a class="small" href="#/ep/${code}/vcon?scene=${h(x.code)}">Vコンで見る</a></div>
      <div class="sgrid">
        ${edBlock("purpose", "① 映像で伝えたいこと", x.purpose, x.human_fields.includes("purpose"))}
        <div class="ed change2" data-field2="change">
          <div class="edl"><b>② 変化</b><span class="small muted">　このシーンの前 → 後（誰の気持ち・状況がどう変わったか）</span></div>
          <div class="chg">${edBlock("change_before", "前", x.change_before, x.human_fields.includes("change_before"), { cls: "mini" })}
            <div class="arrow">➜</div>${edBlock("change_after", "後", x.change_after, x.human_fields.includes("change_after"), { cls: "mini" })}</div>
          ${edBlock("turn", "きっかけ", x.turn, x.human_fields.includes("turn"), { cls: "mini" })}
          ${x.characters.some((c) => c.change) ? `<div class="cchg">${x.characters.filter((c) => c.change).map((c) =>
            `<span class="cc" style="border-color:${ccolor(c.name)}"><b style="color:${ccolor(c.name)}">${h(c.name)}</b> ${h(c.change)}</span>`).join("")}</div>` : ""}
        </div>
        ${edBlock("synopsis", "③ あらすじ", x.synopsis, x.human_fields.includes("synopsis"), { hint: "誰がどうして、どうなったか", cls: "wide" })}
        <div class="ed wide chared">
          <div class="edl"><b>④ キャラ</b><span class="small muted">　このシーンでの したい／する／内心／変化</span>
            <span class="who ${x.human_fields.includes("characters") ? "human" : ""}">${x.human_fields.includes("characters") ? "監督が直した" : "AI の下書き"}</span><button class="charbtn" title="直す">✎</button></div>
          <table class="ctable"><tr><th></th><th>したい</th><th>する（見える芝居）</th><th>内心</th><th>変化</th><th>温度</th></tr>
            ${x.characters.map((c) => `<tr><th style="color:${ccolor(c.name)}">${h(c.name)}</th><td>${h(c.want)}</td><td>${h(c.does)}</td><td class="muted">${h(c.inner)}</td>
              <td>${h(c.change || "")}</td><td>${dots(c.tension)}</td></tr>`).join("")}</table>
        </div>
      </div>
      ${choices.filter((c) => c.scene === x.code && c.status === "open").map(choiceHTML).join("")}
      <details class="detail"><summary>演出の細部（区切り・配置図・脚本）</summary>
        ${x.beats.length ? `<div class="beats">${x.beats.map((b, k) => `<div class="beat ${b.peak ? "peak" : ""}"
          style="flex:${+b.seconds || 1}" title="${h(b.why)}"><span class="sec">${k + 1}｜${h(b.seconds)}s</span>${b.peak ? `<span class="star">★${h(b.peak)}</span>` : ""}<b>${h(b.who)}</b> ${h(b.does)}
          ${b.why ? `<div class="why">${h(b.why)}</div>` : ""}</div>`).join("")}</div>` : ""}
        <details class="plan" data-plan="${h(x.code)}"><summary class="small"><b>配置図</b>　${x.blocking_text.length ? "区切りごとの立ち位置。コマをドラッグして直せます" : "まだ配置がありません"}</summary>
          <div class="planbox"></div></details>
        ${x.blocking ? `<div class="small muted"><b>立ち位置と動線</b>　${h(x.blocking)}</div>` : ""}
        <details data-script="${h(x.code)}"><summary class="small">脚本を見る</summary><div class="script small muted">読み込み中…</div></details>
      </details>
      <div class="reply row">
        <button class="primary" data-ok title="承認すると、字コンテ会議（芝居・演出）→ 480p ドラフト → 映像会議 が自動で進みます">このシーンでいく（→ 字コンテ会議へ）</button>
        <input type="text" class="rtext" placeholder="直してほしいこと・意向を書いて Enter で送る　例：あかねはもっと隠そうとしてほしい">
        <button class="qmic">🎤</button><button data-ng>送る</button>
      </div>
      <div class="small muted" data-msg></div>
    </div>`).join("") || `<p class="muted">まだシーン整理がありません。「AI（演出）に下書きを頼む」を押してください。</p>`}`;

  drawCurve(code, ep, scenes);
  bindChoices(document);
  bindEditors(document.querySelector(".story"), async (field, value) =>
    api(`/api/episodes/${code}/story`, { method: "PATCH", body: { [field]: value } }));
  document.querySelectorAll("[data-jump]").forEach((a) => (a.onclick = () => document.getElementById(`sc-${a.dataset.jump}`)?.scrollIntoView({ behavior: "smooth" })));
  document.getElementById("askDraft").onclick = async () => {
    await api("/api/requests", { method: "POST", body: { episode: code, text:
      `[演出の役] ${code} の脚本（いまの版）から、シーン整理の下書きを作る：この話の芯・物語の流れ（story-set）と、シーンごとの ①映像で伝えたいこと ②変化（前→後・きっかけ・キャラごとの変化）③あらすじ ④キャラ（したい／する／内心／変化／温度）（scene-set / scene-sheet）。監督が直した欄は書き換えない` } });
    document.getElementById("draftMsg").textContent = "頼みました（「いま」の AI が作業中に出ます）";
  };
  document.querySelectorAll(".qmic").forEach((b) => (b.onclick = () => { b.classList.add("on");
    listen((t) => { b.classList.remove("on"); const inp = b.previousElementSibling; inp.value = (inp.value ? inp.value + " " : "") + t; }); }));

  document.querySelectorAll(".scene").forEach((card) => {
    const sc = card.dataset.sc, scene = scenes.find((s) => s.code === sc);
    const msg = (t) => (card.querySelector("[data-msg]").textContent = t);
    bindEditors(card.querySelector(".sgrid"), async (field, value) =>
      api(`/api/episodes/${code}/scenes/${sc}/edit`, { method: "POST", body: { field, value } }));
    // キャラの表は、行ごとにまとめて直す
    card.querySelector(".charbtn").onclick = () => {
      const box = card.querySelector(".chared");
      if (box.querySelector("form")) return;
      const keys = [["want", "したい"], ["does", "する"], ["inner", "内心"], ["change", "変化"]];
      box.querySelector("table").outerHTML = `<form class="cform">${scene.characters.map((c, k) => `<div class="crow" data-k="${k}"><b style="color:${ccolor(c.name)}">${h(c.name)}</b>
        ${keys.map(([f, l]) => `<label>${l}<textarea data-f="${f}" rows="2">${h(c[f] || "")}</textarea></label>`).join("")}
        <label>温度<select data-f="tension">${[1, 2, 3, 4, 5].map((n) => `<option ${+c.tension === n ? "selected" : ""}>${n}</option>`).join("")}</select></label></div>`).join("")}
        <div class="row"><button class="primary" type="submit">保存</button><span class="small muted">保存すると AI に伝わり、キャラの欄は監督の版が正になります</span></div></form>`;
      addMics();
      box.querySelector("form").onsubmit = async (e) => {
        e.preventDefault();
        const chars = scene.characters.map((c, k) => { const row = box.querySelector(`.crow[data-k="${k}"]`); const o = { ...c };
          row.querySelectorAll("[data-f]").forEach((x) => (o[x.dataset.f] = x.dataset.f === "tension" ? +x.value : x.value.trim())); return o; });
        await api(`/api/episodes/${code}/scenes/${sc}/edit`, { method: "POST", body: { field: "characters", value: chars } });
        route();
      };
    };
    card.querySelector("[data-script]").ontoggle = async (e) => {
      const box = card.querySelector(".script");
      if (!e.target.open || box.dataset.loaded) return;
      const r = await api(`/api/episodes/${code}/scenes/${sc}/script`);
      box.dataset.loaded = 1;
      box.innerHTML = r.found ? `<b>${h(r.heading)}</b><br>${r.lines.map(h).join("<br>")}` : "脚本の範囲がまだ指定されていません";
    };
    const planEl = card.querySelector(".plan");
    planEl.ontoggle = () => { if (planEl.open && !planEl.dataset.loaded) { planEl.dataset.loaded = 1; blockingEditor(code, sc, planEl.querySelector(".planbox"), scene); } };
    const text = () => card.querySelector(".rtext").value.trim();
    // 送ったものは、カードの下と画面の下の帯に「送信中 → 順番待ち → 実行中 → 済み」で出す
    const send = async (ok) => {
      const t = text(), input = card.querySelector(".rtext");
      if (!ok && !t) { msg("直してほしいことを書いてください（欄を直接直すなら ✎）"); return; }
      msg("送信中…"); input.disabled = true;
      try {
        if (ok) {
          if (t) await api("/api/reviews", { method: "POST", body: { target_type: "episode", target_id: ep.id, verdict: "良い", tags: ["意図"], comment: `[シーン整理 ${sc}] ${t}` } });
          await api(`/api/episodes/${code}/scenes/${sc}`, { method: "PATCH", body: { status: "approved" } });
          track({ kind: "flow", code, sc, label: `${code} ${sc} を承認 → 字コンテ会議` });
          msg("承認しました。字コンテ会議に回しました（画面の下で進み具合が見えます）");
        } else {
          const r = await api(`/api/episodes/${code}/scenes/${sc}/ask`, { method: "POST", body: { text: t } });
          track({ kind: "request", id: r.request, label: `${code} ${sc} シーン整理の直し：${t.slice(0, 30)}` });
          input.value = "";
          msg("送りました。制作進行が直します。直し方が割れるときは2〜3案を「⑤ 決める」に並べます（画面の下で進み具合が見えます）");
        }
      } catch (e) { msg("送れませんでした：" + e.message); }
      input.disabled = false;
    };
    card.querySelector("[data-ok]").onclick = () => send(true);
    card.querySelector("[data-ng]").onclick = () => send(false);
    card.querySelector(".rtext").onkeydown = (e) => { if (e.key === "Enter" && !e.isComposing) { e.preventDefault(); send(false); } };
  });
  addMics();
  const target = new URLSearchParams(location.hash.split("?")[1] || "").get("scene");
  if (target) document.getElementById(`sc-${target}`)?.scrollIntoView();
}

// ---------- 展開のカーブ ----------
function drawCurve(code, ep, scenes) {
  const box = document.querySelector(".curve");
  const W = 1000, H = 210, top = 26, bottom = 180;
  const total = scenes.reduce((s, x) => s + (x.target_seconds || 0), 0) || 1;
  const X = (sec) => (W * sec) / total, Y = (lv) => bottom - ((lv - 1) / 4) * (bottom - top);
  const pts = [], charLines = {};
  let t0 = 0;
  scenes.forEach((s, si) => {
    const dur = s.target_seconds || 0;
    const bsum = s.beats.reduce((a, b) => a + (+b.seconds || 1), 0) || 1;
    let acc = 0;
    if (dur > 0) s.beats.forEach((b, k) => {
      const w = ((+b.seconds || 1) / bsum) * dur;
      pts.push({ x: X(t0 + acc + w / 2), level: +b.level || 2, peak: b.peak || "", scene: s, si, k });
      acc += w;
    });
    s.characters.forEach((c) => { (charLines[c.name] ||= []).push({ x1: X(t0), x2: X(t0 + dur), y: Y(+c.tension || 1) }); });
    s._x = X(t0); s._w = X(dur); t0 += dur;
  });
  const shown = new Set(JSON.parse(localStorageGet("sheet.chars") || "[]"));
  const chips = document.querySelector(".charchips");
  chips.innerHTML = Object.keys(charLines).map((n) => `<button class="chip ${shown.has(n) ? "on" : ""}" data-ch="${h(n)}" style="border-color:${ccolor(n)}">${h(n)}</button>`).join("");
  const render = () => {
    const path = pts.map((p, i) => `${i ? "L" : "M"}${p.x.toFixed(1)},${Y(p.level).toFixed(1)}`).join(" ");
    box.innerHTML = `<svg viewBox="0 0 ${W} ${H + 24}" class="curvesvg">
      <defs><linearGradient id="cg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f0b45a" stop-opacity=".35"/><stop offset="1" stop-color="#f0b45a" stop-opacity="0"/></linearGradient></defs>
      ${[1, 2, 3, 4, 5].map((l) => `<line x1="0" x2="${W}" y1="${Y(l)}" y2="${Y(l)}" class="grid"/><text x="4" y="${Y(l) - 3}" class="ax">${l}</text>`).join("")}
      ${scenes.map((s, i) => `<g class="scn" data-jump="${h(s.code)}"><rect x="${s._x}" y="${H - 4}" width="${Math.max(0, s._w - 1)}" height="22" fill="${sceneHue(i)}"/>
        ${s._w > 18 ? `<text x="${s._x + s._w / 2}" y="${H + 12}" class="sl">${h(s.code)}</text>` : ""}
        <line x1="${s._x}" x2="${s._x}" y1="${top - 10}" y2="${H - 4}" class="sep"/></g>`).join("")}
      ${[...shown].map((n) => (charLines[n] || []).map((l) => `<line x1="${l.x1}" x2="${l.x2}" y1="${l.y}" y2="${l.y}" stroke="${ccolor(n)}" class="cl"/>`).join("")).join("")}
      ${pts.length ? `<path d="${path} L${pts[pts.length - 1].x},${bottom} L${pts[0].x},${bottom} Z" fill="url(#cg)"/><path d="${path}" class="main"/>` : ""}
      ${pts.map((p, i) => `<g class="pt" data-i="${i}"><circle cx="${p.x}" cy="${Y(p.level)}" r="${p.peak ? 9 : 6}" class="${p.peak ? "pk" : ""}"><title>${h(p.scene.code)} 区切り${p.k + 1}：${h(p.scene.beats[p.k].does)}</title></circle>
        ${p.peak ? `<text x="${p.x}" y="${Y(p.level) - 13}" class="pl">★${h(p.peak)}</text>` : ""}</g>`).join("")}
    </svg>`;
    const svg = box.querySelector("svg");
    const toY = (e) => { const r = svg.getBoundingClientRect(); return ((e.clientY - r.top) / r.height) * (H + 24); };
    svg.querySelectorAll(".pt").forEach((g) => {
      const p = pts[+g.dataset.i];
      g.onpointerdown = (e) => {
        e.preventDefault(); const before = p.level;
        const move = (ev) => { p.level = Math.max(1, Math.min(5, Math.round(1 + ((bottom - toY(ev)) / (bottom - top)) * 4))); render(); };
        const up = async () => {
          window.removeEventListener("pointermove", move); window.removeEventListener("pointerup", up);
          if (p.level !== before) await saveBeat(p, `高さ ${before}→${p.level}`);
        };
        window.addEventListener("pointermove", move); window.addEventListener("pointerup", up);
      };
      g.ondblclick = async () => {
        const name = prompt("山場の名前（空にすると山場を外す）", p.peak || "");
        if (name === null) return;
        const before = p.peak; p.peak = name.trim(); render();
        await saveBeat(p, p.peak ? `山場「${p.peak}」${before ? `（前は「${before}」）` : "にする"}` : `山場「${before}」を外す`);
      };
    });
    svg.querySelectorAll("[data-jump]").forEach((g) => (g.onclick = () => document.getElementById(`sc-${g.dataset.jump}`)?.scrollIntoView({ behavior: "smooth" })));
  };
  const saveBeat = async (p, what) => {
    const beats = p.scene.beats.map((b, k) => (k === p.k ? { ...b, level: p.level, peak: p.peak } : b));
    p.scene.beats = beats;
    await api(`/api/episodes/${code}/scenes/${p.scene.code}`, { method: "PATCH", body: { beats } });
    await api("/api/reviews", { method: "POST", body: { target_type: "episode", target_id: ep.id, verdict: "修正", tags: ["尺・テンポ", "意図"],
      comment: `[展開カーブ ${p.scene.code}・区切り${p.k + 1}] ${what}（${p.scene.beats[p.k].does}）` } });
  };
  chips.querySelectorAll("[data-ch]").forEach((b) => (b.onclick = () => {
    shown.has(b.dataset.ch) ? shown.delete(b.dataset.ch) : shown.add(b.dataset.ch);
    b.classList.toggle("on"); localStorageSet("sheet.chars", JSON.stringify([...shown])); render();
  }));
  render();
}
function localStorageGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
function localStorageSet(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* 保存できなくても動く */ } }

// ---------- 配置図：区切りごとの立ち位置 ----------
async function blockingEditor(code, sc, box, scene) {
  const b = await api(`/api/episodes/${code}/scenes/${sc}/blocking`);
  const plan = b.plan_data || {};
  if (!plan.spots) { box.innerHTML = `<p class="small muted">この場所（${h(scene.place)}）の見取り図がまだありません（月灯_vault/06_設定/舞台/配置図.json に足す）。</p>`; return; }
  const W = 600, H = 400;
  const nBeats = Math.max(1, scene.beats.length, ...b.frames.map((f) => (f.beat || 0) + 1));
  let frames = JSON.parse(JSON.stringify(b.frames)), k = 0, timer = null;
  const names = [...new Set([...scene.characters.map((c) => c.name), ...frames.flatMap((f) => Object.keys(f.pos || {}))])];
  const posAt = (beat) => { const pos = {}; frames.filter((f) => (f.beat || 0) <= beat).sort((a, c) => a.beat - c.beat).forEach((f) => Object.assign(pos, f.pos)); return pos; };
  box.innerHTML = `<div class="planwrap"><div class="beattabs">${Array.from({ length: nBeats }, (_, i) =>
      `<button data-k="${i}" title="${h(scene.beats[i]?.does || "")}">区切り${i + 1}${scene.beats[i] ? `<span class="small muted"> ${h(scene.beats[i].who)}</span>` : ""}</button>`).join("")}
      <button data-play title="区切りを順に動かして見る">▶</button></div>
    <div class="beatnow small"></div>
    <svg viewBox="0 0 ${W} ${H}" class="plansvg"></svg>
    <div class="tray small"></div>
    <ol class="btext small"></ol>
    <div class="row"><input type="text" class="bnote" placeholder="ひとこと（任意）　例：入口に背を向けて立たせて"><button class="primary" data-bsend>動かしたのを送る</button>
      <button data-breset>AI の案に戻す</button><span class="small muted" data-bmsg>${b.by === "human" ? "いまは監督が動かした配置" : "いまは AI の案"}</span></div></div>`;
  const svg = box.querySelector("svg");
  // 場所の名前：扉は扉の下（右端の扉は右寄せ）、ほかは左上の角に小さく（コマや位置の名前と重ならないように）
  const areaLabel = (a) => a.door
    ? `<text x="${(a.x > 0.5 ? (a.x + a.w) * W - 2 : a.x * W + 2)}" y="${(a.y + a.h) * H + 12}" class="al" style="text-anchor:${a.x > 0.5 ? "end" : "start"}">${h(a.name)}</text>`
    : a.w * W > 40 ? `<text x="${a.round ? (a.x + a.w / 2) * W : a.x * W + 4}" y="${a.round ? (a.y + a.h / 2) * H + 4 : a.y * H + 12}" class="al" style="text-anchor:${a.round ? "middle" : "start"}">${h(a.name)}</text>` : "";
  const P = ([x, y]) => [x * W, y * H];
  const draw = () => {
    const now = posAt(k), prev = k ? posAt(k - 1) : {};
    const area = (a) => a.round ? `<ellipse cx="${(a.x + a.w / 2) * W}" cy="${(a.y + a.h / 2) * H}" rx="${(a.w / 2) * W}" ry="${(a.h / 2) * H}" class="ar solid"/>`
      : `<rect x="${a.x * W}" y="${a.y * H}" width="${a.w * W}" height="${a.h * H}" class="ar ${a.solid ? "solid" : ""} ${a.door ? "door" : ""}"/>`;
    svg.innerHTML = `<rect x="0" y="0" width="${W}" height="${H}" class="floor"/>
      ${(plan.areas || []).map((a) => `${area(a)}${areaLabel(a)}`).join("")}
      ${Object.entries(plan.spots).map(([n, xy]) => { const [x, y] = P(xy); return `<circle cx="${x}" cy="${y}" r="2.5" class="sp"/><text x="${x + 4}" y="${y - 4}" class="spl">${h(n)}</text>`; }).join("")}
      ${Object.entries(plan.cameras || {}).map(([n, [x, y]]) => `<text x="${x * W}" y="${y * H}" class="cam">📷${n}</text>`).join("")}
      ${names.filter((n) => prev[n] && now[n] && Math.hypot(prev[n][0] - now[n][0], prev[n][1] - now[n][1]) > 0.02).map((n) => {
        const [x1, y1] = P(prev[n]), [x2, y2] = P(now[n]);
        return `<circle cx="${x1}" cy="${y1}" r="12" class="ghost" stroke="${ccolor(n)}"/><line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${ccolor(n)}" class="mv" marker-end="url(#ah)"/>`; }).join("")}
      <defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#ddd"/></marker></defs>
      ${names.filter((n) => now[n]).map((n) => { const [x, y] = P(now[n]);
        return `<g class="tok" data-n="${h(n)}" style="transform:translate(${x}px,${y}px)"><circle r="14" fill="${ccolor(n)}"/><text y="5" class="tl">${h(n[0])}</text><text y="27" class="tn">${h(n)}</text></g>`; }).join("")}`;
    box.querySelectorAll("[data-k]").forEach((t) => t.classList.toggle("on", +t.dataset.k === k));
    const bt = scene.beats[k];
    box.querySelector(".beatnow").innerHTML = bt ? `<b>区切り${k + 1}</b>（${h(bt.seconds)}秒）${h(bt.who)}：${h(bt.does)}` : "";
    const missing = names.filter((n) => !now[n]);
    box.querySelector(".tray").innerHTML = missing.length ? `まだ置いていない：${missing.map((n) => `<button data-place="${h(n)}" style="border-color:${ccolor(n)}">${h(n)}</button>`).join("")}（押すと中央に置きます）` : "";
    box.querySelectorAll("[data-place]").forEach((bn) => (bn.onclick = () => { setPos(bn.dataset.place, [0.5, 0.55]); draw(); }));
    box.querySelector(".btext").innerHTML = textOf().map((t) => `<li>${h(t)}</li>`).join("");
    svg.querySelectorAll(".tok").forEach((g) => (g.onpointerdown = (e) => {
      e.preventDefault(); stop();
      const n = g.dataset.n;
      const move = (ev) => { const r = svg.getBoundingClientRect();
        const xy = [Math.max(0, Math.min(1, (ev.clientX - r.left) / r.width)), Math.max(0, Math.min(1, (ev.clientY - r.top) / r.height))];
        g.style.transform = `translate(${xy[0] * W}px,${xy[1] * H}px)`; g._xy = xy; };
      const up = () => { window.removeEventListener("pointermove", move); window.removeEventListener("pointerup", up);
        if (g._xy) { setPos(n, g._xy); box.querySelector("[data-bmsg]").textContent = "動かしました（まだ送っていません）"; } draw(); };
      window.addEventListener("pointermove", move); window.addEventListener("pointerup", up);
    }));
  };
  const setPos = (n, xy) => {
    let f = frames.find((f) => (f.beat || 0) === k);
    if (!f) { f = { beat: k, pos: {} }; frames.push(f); }
    f.pos[n] = xy.map((v) => Math.round(v * 1000) / 1000);
  };
  // 言葉にする（サーバーと同じ考え方：近い位置の名前、動いたら「→」）
  const near = (xy) => { const [n, s] = Object.entries(plan.spots).reduce((a, c) => (Math.hypot(c[1][0] - xy[0], c[1][1] - xy[1]) < Math.hypot(a[1][0] - xy[0], a[1][1] - xy[1]) ? c : a));
    return Math.hypot(s[0] - xy[0], s[1] - xy[1]) < 0.07 ? n : `${n}のあたり`; };
  const textOf = () => { const out = []; let prev = {};
    [...frames].sort((a, c) => a.beat - c.beat).forEach((f) => {
      const parts = Object.entries(f.pos || {}).map(([n, xy]) => prev[n] ? (Math.hypot(prev[n][0] - xy[0], prev[n][1] - xy[1]) > 0.04 && near(prev[n]) !== near(xy) ? `${n} ${near(prev[n])}→${near(xy)}` : "") : `${n}＝${near(xy)}`).filter(Boolean);
      if (parts.length) out.push(`区切り${(f.beat || 0) + 1}：${parts.join("、")}`);
      prev = { ...prev, ...f.pos }; });
    return out; };
  const stop = () => { if (timer) { clearInterval(timer); timer = null; box.querySelector("[data-play]").textContent = "▶"; } };
  box.querySelectorAll("[data-k]").forEach((t) => (t.onclick = () => { stop(); k = +t.dataset.k; draw(); }));
  box.querySelector("[data-play]").onclick = (e) => {
    if (timer) return stop();
    k = 0; draw(); e.target.textContent = "■";
    timer = setInterval(() => { if (k >= nBeats - 1) return stop(); k++; draw(); }, 1400);
  };
  box.querySelector("[data-bsend]").onclick = async () => {
    const r = await api(`/api/episodes/${code}/scenes/${sc}/blocking`, { method: "PUT", body: { frames, by: "human", note: box.querySelector(".bnote").value } });
    box.querySelector("[data-bmsg]").textContent = r.diff.length ? `送りました：${r.diff.join(" ／ ")}` : "送りました";
  };
  box.querySelector("[data-breset]").onclick = () => { frames = JSON.parse(JSON.stringify(b.agent_frames || b.frames)); draw();
    box.querySelector("[data-bmsg]").textContent = "AI の案に戻しました（送ると確定）"; };
  draw();
}

// ---------- AI からの2択 ----------
function choiceHTML(c) {
  return `<div class="choice" data-choice="${c.id}">
    <div class="row"><span class="badge proposed">AI からの2択</span><b>${h(c.question)}</b><span class="small muted">${h(c.scene)} ${h(c.about)}</span></div>
    ${c.why ? `<div class="small muted">迷っている理由：${h(c.why)}</div>` : ""}
    <div class="opts">${c.options.map((o) => `<button class="opt" data-pick="${h(o.label)}"><span class="ol">${h(o.label)}</span>${h(o.text)}</button>`).join("")}</div>
    <div class="row"><input type="text" class="cnote" placeholder="自分の案・ひとこと（任意）"><button class="qmic" title="話して入力">🎤</button>
      <button data-pick="other">自分の案で</button>
      ${c.about && c.about !== "演出" ? `<label class="small"><input type="checkbox" class="keep"> ${h(c.about)}の決まりにする（キャラのノートに残す）</label>` : ""}</div>
    <div class="small cdone"></div></div>`;
}
function bindChoices(root) {
  root.querySelectorAll(".choice").forEach((el) => {
    el.querySelector(".qmic").onclick = (e) => { e.target.classList.add("on");
      listen((t) => { e.target.classList.remove("on"); const inp = el.querySelector(".cnote"); inp.value = (inp.value ? inp.value + " " : "") + t; }); };
    el.querySelectorAll("[data-pick]").forEach((b) => (b.onclick = async () => {
      const note = el.querySelector(".cnote").value.trim();
      if (b.dataset.pick === "other" && !note) { el.querySelector(".cdone").textContent = "自分の案を一言書いてください"; return; }
      const r = await api(`/api/choices/${el.dataset.choice}/answer`, { method: "POST",
        body: { pick: b.dataset.pick, note, keep: !!el.querySelector(".keep")?.checked } });
      el.classList.add("answered");
      el.querySelectorAll("button").forEach((x) => (x.disabled = true));
      b.classList.add("on");
      el.querySelector(".cdone").textContent = `覚えました：${r.rule}${r.written ? `（${r.written} に書きました）` : ""}`;
    }));
  });
}
