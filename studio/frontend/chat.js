// ---------- 制作進行とのチャット（どのページでも右下から）。話しかける相手は制作進行ひとり ----------
// 返事は、この PC の Claude（Claude Code）が裏で書く。直しや頼みごとは「積む」ボタンで、その話数の修正項目や仕事になる。
const CHAT = { open: false, last: 0, timer: null, msgs: [] };
const curEpisode = () => (location.hash.match(/#\/ep\/([^/?]+)/) || [])[1] || "";

function chatInit() {
  const box = document.createElement("div");
  box.id = "chat";
  box.innerHTML = `<button id="chatBtn" title="制作進行に話しかける">💬 制作進行</button>
    <div id="chatPanel" hidden>
      <div class="chead"><b>制作進行</b><span class="small muted" id="chatAgents"></span><span style="flex:1"></span><button id="chatClose">×</button></div>
      <div id="chatLog"></div>
      <div class="cinput"><textarea id="chatText" data-mic="1" rows="2" placeholder="話しかける（Enter で送る、Shift+Enter で改行）　例：9話の S3、ノートを戻すところをもっと分かりやすく"></textarea>
        <div class="row"><button id="chatMic" title="話して入力">🎤</button><span class="small muted" id="chatEp"></span><span style="flex:1"></span><button class="primary" id="chatSend">送る</button></div></div>
    </div>`;
  document.body.appendChild(box);
  const panel = box.querySelector("#chatPanel"), text = box.querySelector("#chatText");
  const toggle = (on) => { CHAT.open = on; panel.hidden = !on; box.querySelector("#chatBtn").hidden = on; if (on) { poll(); text.focus(); } };
  box.querySelector("#chatBtn").onclick = () => toggle(true);
  box.querySelector("#chatClose").onclick = () => toggle(false);
  const send = async () => {
    const t = text.value.trim();
    if (!t) return;
    text.value = "";
    await api("/api/chat", { method: "POST", body: { text: t, episode: curEpisode() } });
    poll();
  };
  box.querySelector("#chatSend").onclick = send;
  text.onkeydown = (e) => { if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); send(); } };
  box.querySelector("#chatMic").onclick = (e) => { e.target.classList.add("on");
    listen((t) => { e.target.classList.remove("on"); if (t) text.value = (text.value ? text.value + " " : "") + t; text.focus(); }); };
  window.addEventListener("hashchange", () => (box.querySelector("#chatEp").textContent = curEpisode() ? `いま見ている話数：${curEpisode()}` : ""));
  box.querySelector("#chatEp").textContent = curEpisode() ? `いま見ている話数：${curEpisode()}` : "";
}

async function poll() {
  clearTimeout(CHAT.timer);
  const r = await api(`/api/chat?after=${CHAT.last}`).catch(() => null);
  if (r) {
    r.messages.forEach((m) => { CHAT.msgs.push(m); CHAT.last = Math.max(CHAT.last, m.id); });
    render(r);
  }
  // 返事を待つ間と、開いている間は見に行く
  if (CHAT.open || (r && r.busy)) CHAT.timer = setTimeout(poll, r && r.busy ? 1200 : 4000);
}

// 返事の太字（**…**）と改行だけ見やすくする
const md = (t) => h(t).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>").replace(/`([^`]+)`/g, "<code>$1</code>").replace(/\n/g, "<br>");
function render(r) {
  const log = document.getElementById("chatLog");
  const working = Object.values(r.agents || {}).filter((a) => a.running).map((a) => a.label);
  document.getElementById("chatAgents").textContent = working.length ? `　裏で作業中：${working.join("・")}` : "";
  log.innerHTML = (r.ready ? "" : `<div class="cmsg sys">この PC で Claude（Claude Code）が見つかりません。Claude のデスクトップアプリの「コード」を一度開くか、claude コマンドを入れてから、start.bat を開き直してください。</div>`)
    + (CHAT.msgs.length ? "" : `<div class="cmsg sys">制作進行です。直したいこと・頼みたいこと・分からないことを、そのまま話しかけてください。直しは「積む」で、その話数の修正項目に入ります。</div>`)
    + CHAT.msgs.map((m) => `<div class="cmsg ${m.role}">${m.episode && m.role === "user" ? `<span class="cep">${h(m.episode)}</span>` : ""}${md(m.text)}
      ${(m.actions || []).map((a, i) => `<div class="cact"><span>${h({ fix: "修正項目に", request: "制作進行の仕事に", flow: "工程を始める" }[a.type] || a.type)}：${h(a.episode || "")} ${h(a.scene || "")} ${h(a.text || "")}</span>
        ${a.done ? `<span class="small ok">✓ ${h(a.done)}</span>` : `<button data-act="${m.id}:${i}">積む</button>`}</div>`).join("")}</div>`).join("")
    + (r.busy ? `<div class="cmsg assistant thinking">${r.partial ? h(r.partial).replace(/\n/g, "<br>") : "考え中…"}</div>` : "");
  log.scrollTop = log.scrollHeight;
  log.querySelectorAll("[data-act]").forEach((b) => (b.onclick = async () => {
    const [m, i] = b.dataset.act.split(":").map(Number);
    const res = await api("/api/chat/act", { method: "POST", body: { message: m, index: i } });
    const msg = CHAT.msgs.find((x) => x.id === m); msg.actions[i].done = res.message;
    render(r);
    if (typeof route === "function") route();
  }));
}

chatInit();
