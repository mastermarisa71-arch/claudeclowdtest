// ---------- AI スタッフ会議：AI どうしが役を分けてレビューし合ったのを、監督が上から眺める ----------
// 監督がやることは「開く（見てほしいことを一言）」と、結論のうち2択に答えることだけ。所見は読まなくてもよい。
const SEV = { "必須": "open", "提案": "proposed", "好み": "" };

async function viewStaff(code) {
  const [rounds, st, { scenes }] = await Promise.all([api(`/api/rounds?episode=${code}`), api("/api/staff"),
    api(`/api/episodes/${code}/scenes`)]);
  const roles = st.roles || {}, agents = st.agents || {};
  const roleChip = (r) => `<span class="rolechip" style="border-color:${roles[r]?.color || "#888"};color:${roles[r]?.color || "#ccc"}">${h(roles[r]?.name || r)}</span>`;
  const who = (a) => h(agents[a]?.label || a);
  $view.innerHTML = `${epTabs(code, "staff")}<h1>AI スタッフ会議 <span class="muted small">AI が役を分けてレビューし合い、合意したものは作り直し、割れたものだけ「AIからの質問」に2択で届きます</span></h1>
    <div class="card"><div class="row" style="gap:14px">${Object.entries(st.assign || {}).map(([r, a]) => `<span>${roleChip(r)} ${who(a)}</span>`).join("")}</div>
      <div class="row" style="margin-top:8px"><select id="rtarget"><option value="">話数全体</option>${scenes.map((s) => `<option value="${h(s.code)}">${h(s.code)} ${h(s.change_after || s.purpose).slice(0, 24)}</option>`).join("")}</select>
        <input type="text" id="rnote" placeholder="見てほしいこと（任意）　例：S7 の怖さが伝わるか" style="flex:1">
        <button class="primary" id="ropen">AI スタッフで検討して</button></div>
      <p class="small muted">開くと、各 AI が自分の役の枠を取ります（見張り番 <code>staff_watch.bat</code> を動かしていれば自動。なければ各 AI に「staff-claim して」と頼む）。</p></div>
    ${rounds.map((r) => {
      const posts = r.posts.filter((p) => p.kind !== "まとめ"), sum = r.posts.find((p) => p.kind === "まとめ");
      const passes = [...new Set(r.slots.map((s) => s.pass))];
      return `<div class="card round ${r.status}">
        <div class="row"><b>#${r.id} ${h(r.target || "全体")}</b><span class="badge ${r.status === "closed" ? "sel" : "proposed"}">${h(r.stage)}</span>
          <span class="small muted">${h(r.note)}</span><span style="flex:1"></span>
          ${r.slots.map((s) => `<span class="slot ${s.status}" title="${h(s.agent)}">${h(roles[s.role]?.name || s.role)}${s.pass > 1 && s.role !== "まとめ" ? "②" : ""}：${s.status === "done" ? "済" : s.status === "claimed" ? "考え中" : "待ち"}</span>`).join("")}</div>
        ${sum ? `<div class="summary"><b>結論</b>　${h(sum.summary)}
          <ul>${sum.items.map((i) => `<li><span class="badge ${i.decision === "do" ? "sel" : i.decision === "ask" ? "proposed" : ""}">${{ do: "直す", ask: "監督へ", drop: "見送り" }[i.decision] || h(i.decision)}</span> ${h(i.text)}
            ${i.options ? `<span class="small muted">（${i.options.map(h).join(" ／ ")}）</span>` : ""}${i.why ? `<div class="small muted">${h(i.why)}</div>` : ""}</li>`).join("")}</ul>
          ${r.result?.choices?.length ? `<a href="#/ep/${code}/questions">2択に答える（${r.result.choices.length}件）</a>` : ""}</div>` : ""}
        <details ${sum ? "" : "open"}><summary class="small">各役の所見（${posts.length}）</summary>
          <div class="rolecols">${Object.keys(roles).filter((k) => k !== "まとめ").map((k) => `<div class="rolecol" style="border-top:3px solid ${roles[k].color}">
            <div class="row">${roleChip(k)}</div>
            ${posts.filter((p) => p.role === k).map((p) => `<div class="post"><div class="small muted">${p.pass}周目・${who(p.agent)}</div><div>${h(p.summary)}</div>
              ${p.items.map((i) => `<div class="pitem"><span class="badge ${SEV[i.severity] ?? ""}">${h(i.severity)}</span> <span class="small muted">${h(i.at)}</span> ${h(i.what)}
                ${i.fix ? `<div class="small">→ ${h(i.fix)}</div>` : ""}${i.agree ? `<div class="small muted">［${h(i.agree)}］</div>` : ""}</div>`).join("")}</div>`).join("") || `<p class="small muted">まだ</p>`}
          </div>`).join("")}</div></details>
      </div>`; }).join("") || `<p class="muted">まだ会議はありません。</p>`}`;
  document.getElementById("ropen").onclick = async () => {
    await api("/api/rounds", { method: "POST", body: { episode: code, target: document.getElementById("rtarget").value, note: document.getElementById("rnote").value } });
    route();
  };
}
