// ---------- AI 会議：結論が先。話し合いは会話の形で、指摘したコマの絵（なければ字コンテの文字）をつけて見せる ----------
const SEV = { "必須": "open", "提案": "proposed", "好み": "" };
const ROLE_ICON = { "芝居": "芝", "演出": "演", "見る": "見", "まとめ": "ま" };

async function viewStaff(code) {
  const [rounds, st, { scenes }, plist, vs] = await Promise.all([api(`/api/rounds?episode=${code}`), api("/api/staff"),
    api(`/api/episodes/${code}/scenes`), api(`/api/episodes/${code}/playlist`), api(`/api/episodes/${code}/versions?status=open,adopted,kept,other`)]);
  const roles = st.roles || {}, agents = st.agents || {};
  const who = (a) => h(agents[a]?.label || a);
  const byCode = {};
  plist.forEach((p) => (byCode[`${p.cut.cut}${(p.cut.panel || "").replace("―", "")}`] = p));
  // 指摘の「どこ」に出てくるコマの番号を、絵（なければ字コンテの文字）にする
  const shots = (at) => [...new Set((String(at || "").match(/S\d+-\d+[①-⑳]?/g) || []))].slice(0, 3).map((k) => {
    const p = byCode[k] || byCode[k.replace(/[①-⑳]$/, "") + "①"];
    if (!p) return "";
    const t = p.take;
    return `<a class="cshot" href="#/ep/${code}/vcon?cut=${p.cut.id}" title="${h(k)} ${h(p.cut.picture)}">${t && t.file_path
      ? (t.kind === "video" ? `<video src="/media/${encodeURI(t.file_path)}#t=${p.offset || 0}" muted preload="metadata"></video>` : `<img src="/media/${encodeURI(t.file_path)}">`)
      : `<span class="ctext">${h(p.cut.picture)}</span>`}<span class="ccode">${h(k)}</span></a>`;
  }).join("");
  const bubble = (p) => `<div class="bubble" style="--rc:${roles[p.role]?.color || "#888"}">
      <div class="avatar">${ROLE_ICON[p.role] || h(p.role[0])}</div>
      <div class="bbody"><div class="small"><b style="color:var(--rc)">${h(roles[p.role]?.name || p.role)}</b> <span class="muted">${who(p.agent)}</span></div>
        <div class="bsum">${h(p.summary)}</div>
        ${p.items.map((i) => `<div class="bitem">${i.agree ? `<span class="agree ${/反対/.test(i.agree) ? "no" : "yes"}">${h(i.agree)}</span>` : ""}
          <span class="badge ${SEV[i.severity] ?? ""}">${h(i.severity)}</span> <span class="muted small">${h(i.at)}</span>
          <div class="bwhat">${h(i.what)}</div>${i.fix ? `<div class="bfix">→ ${h(i.fix)}</div>` : ""}
          <div class="cshots">${shots(i.at)}</div></div>`).join("")}
      </div></div>`;
  const stage = (r) => {
    const passes = [...new Set(r.slots.filter((s) => s.role !== "まとめ").map((s) => s.pass))];
    const col = (label, list) => `<div class="pstep"><div class="small muted">${label}</div>${list.map((s) =>
      `<span class="pdot ${s.status}" style="--rc:${roles[s.role]?.color || "#888"}" title="${h(roles[s.role]?.name || s.role)}：${s.status === "done" ? "済" : s.status === "claimed" ? "考え中" : "待ち"} ${h(s.agent || "")}">${ROLE_ICON[s.role] || ""}</span>`).join("")}</div>`;
    return `<div class="pflow">${passes.map((p) => col(p === 1 ? "1周目（ひとりで）" : "2周目（読み合う）", r.slots.filter((s) => s.pass === p && s.role !== "まとめ"))).join('<span class="sarrow">›</span>')}
      <span class="sarrow">›</span>${col("まとめ", r.slots.filter((s) => s.role === "まとめ").length ? r.slots.filter((s) => s.role === "まとめ") : [{ role: "まとめ", status: "wait" }])}</div>`;
  };
  $view.innerHTML = `${epTabs(code, "staff")}<h1>AI 会議 <span class="muted small">AI が役を分けて見て、話し合い、案を作ります。結論の案は「④ 決める」で並べて見られます</span></h1>
    <div class="card"><div class="row" style="gap:14px">${Object.entries(st.assign || {}).map(([r, a]) =>
      `<span class="rolechip" style="border-color:${roles[r]?.color};color:${roles[r]?.color}">${ROLE_ICON[r]} ${h(roles[r]?.name || r)}</span><span class="small">${who(a)}</span>`).join("")}</div>
      <div class="row" style="margin-top:8px"><select id="rtarget"><option value="">話数全体</option>${scenes.map((s) => `<option value="${h(s.code)}">${h(s.code)} ${h(s.change_after || s.purpose).slice(0, 24)}</option>`).join("")}</select>
        <input type="text" id="rnote" placeholder="見てほしいこと（任意）　例：S7 の怖さが伝わるか" style="flex:1">
        <button class="primary" id="ropen">AI 会議にかける</button></div></div>
    ${rounds.map((r) => {
      const posts = r.posts.filter((p) => p.kind !== "まとめ"), sum = r.posts.find((p) => p.kind === "まとめ");
      const myVs = vs.filter((v) => v.round_id === r.id);
      return `<div class="card round ${r.status}">
        <div class="row"><b>#${r.id} ${h(r.target || "全体")}</b><span class="badge ${r.status === "closed" ? "sel" : "proposed"}">${r.status === "closed" ? "済み" : "進行中"}</span>
          <span class="small muted">${h(r.note)}</span><span style="flex:1"></span>${stage(r)}</div>
        ${sum ? `<div class="concl"><div class="ctitle">結論</div><div class="csum">${h(sum.summary)}</div>
          <div class="outs">
            ${myVs.map((v) => `<a class="out ver" href="#/ep/${code}/decide"><span class="ok">${v.status === "open" ? "▶ 案を見る" : { adopted: "採用", kept: "今のまま", other: "ちがう" }[v.status]}</span>
              <b>${h(v.title)}</b>${v.choice_id ? `<span class="small">（2択 ${h(v.option)}）</span>` : ""}</a>`).join("")}
            ${sum.items.filter((i) => i.decision === "ask" && !(i.versions || []).length).map((i) => `<a class="out ask" href="#/ep/${code}/decide"><span class="ok">2択</span>${h(i.text)}</a>`).join("")}
            ${sum.items.filter((i) => i.decision === "do" && !i.version).map((i) => `<span class="out do"><span class="ok">直す</span>${h(i.text)}</span>`).join("")}
            ${sum.items.filter((i) => i.decision === "drop").map((i) => `<span class="out drop"><span class="ok">見送り</span>${h(i.text)}<span class="small muted">　${h(i.why || "")}</span></span>`).join("")}
          </div></div>` : ""}
        <details ${sum ? "" : "open"}><summary>話し合い（${posts.length}）</summary>
          ${[1, 2].map((p) => posts.filter((x) => x.pass === p).length ? `<div class="passlabel">${p === 1 ? "1周目：それぞれ、ほかの役を見ずに" : "2周目：ほかの役の意見を読んで"}</div>
            <div class="talk">${posts.filter((x) => x.pass === p).map(bubble).join("")}</div>` : "").join("")}
          ${sum ? `<div class="passlabel">まとめ</div><div class="talk">${bubble({ ...sum, items: [] })}</div>` : ""}
        </details></div>`; }).join("") || `<p class="muted">まだ会議はありません。</p>`}`;
  document.getElementById("ropen").onclick = async () => {
    await api("/api/rounds", { method: "POST", body: { episode: code, target: document.getElementById("rtarget").value, note: document.getElementById("rnote").value } });
    route();
  };
}
