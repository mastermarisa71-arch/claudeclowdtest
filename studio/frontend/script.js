// ---------- 脚本：読む・直す・行に注をつける ----------
// 行を押すと注をつけられる（監督のメモ。AI は脚本と一緒に読む）。「脚本を直す」で全文を手で直せる（前の版は残る）。
async function viewScript(code) {
  const s = await api(`/api/episodes/${code}/script`);
  if (!s.exists) { $view.innerHTML = `${epTabs(code, "script")}<p class="muted">この話数の脚本はまだありません。「話数」の画面から脚本のファイルを落としてください。</p>`; return; }
  const body = s.text.replace(/^---[\s\S]*?---\n/, "");
  const notesOf = (line) => s.notes.filter((n) => n.anchor === line);
  let sc = 0;
  const lineHTML = (l, i) => {
    const t = l.trim();
    if (!t) return `<div class="sl blank"></div>`;
    const isHead = /^(#+\s*)?[○〇◯]/.test(t);
    if (isHead) sc++;
    const isDia = /「/.test(t) && !/^\s/.test(l) && !isHead;
    return `<div class="sl ${isHead ? "head" : isDia ? "dia" : "act"}" data-i="${i}">${isHead ? `<span class="scn">S${sc}</span>` : ""}${h(t.replace(/^#+\s*/, ""))}
      ${notesOf(l).map((n) => `<div class="snote">注：${h(n.note)} <button class="ndel" data-n="${n.id}" title="消す">×</button></div>`).join("")}</div>`;
  };
  const lines = body.split("\n");
  $view.innerHTML = `${epTabs(code, "script")}
    <div class="row"><h1 style="margin:0">脚本</h1><span class="small muted">${h(s.path)}</span><span style="flex:1"></span>
      <button id="edit" class="primary">✎ 脚本を直す</button></div>
    <p class="small muted">行を押すと、その行に注（監督のメモ）をつけられます。「○場所（時間）」の行ごとに、シーン（S1・S2 …）に分けています。</p>
    <div class="card scriptview">${lines.map(lineHTML).join("")}</div>`;
  document.querySelectorAll(".sl[data-i]").forEach((el) => (el.onclick = (e) => {
    if (e.target.closest(".snote") || el.querySelector(".nform2")) return;
    el.insertAdjacentHTML("beforeend", `<div class="nform2 row"><input type="text" placeholder="注（例：ここは間をたっぷり）"><button class="primary">つける</button><button class="ncancel">やめる</button></div>`);
    const f = el.querySelector(".nform2"), inp = f.querySelector("input");
    inp.focus();
    f.querySelector(".ncancel").onclick = (ev) => { ev.stopPropagation(); f.remove(); };
    const go = async (ev) => { ev && ev.stopPropagation(); if (!inp.value.trim()) return;
      await api(`/api/episodes/${code}/script/notes`, { method: "POST", body: { anchor: lines[+el.dataset.i], note: inp.value.trim() } }); route(); };
    f.querySelector(".primary").onclick = go;
    inp.onkeydown = (ev) => { if (ev.key === "Enter" && !ev.isComposing) go(ev); };
  }));
  document.querySelectorAll(".ndel").forEach((b) => (b.onclick = async (e) => { e.stopPropagation(); await api(`/api/script/notes/${b.dataset.n}`, { method: "DELETE" }); route(); }));
  document.getElementById("edit").onclick = () => {
    $view.querySelector(".scriptview").outerHTML = `<div class="card"><textarea id="stext" data-mic="1" class="sedit">${h(s.text)}</textarea>
      <div class="row"><button class="primary" id="ssave">保存</button><button id="scancel">やめる</button>
        <span class="small muted">保存すると前の版は「03_脚本/前の版」に残り、制作進行がシーン整理の見直しをします</span></div></div>`;
    document.getElementById("scancel").onclick = () => route();
    document.getElementById("ssave").onclick = async () => {
      const r = await api(`/api/episodes/${code}/script`, { method: "PUT", body: { text: document.getElementById("stext").value } });
      route();
      if (r.new_scenes) setTimeout(() => alert(`脚本から ${r.new_scenes} シーンに分けました`), 300);
    };
  };
}
