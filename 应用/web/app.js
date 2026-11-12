/* 回声 Echo —— 前端逻辑（原生 JS，无构建） */
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
const esc = s => String(s == null ? "" : s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

const api = {
  async get(u) {
    const r = await fetch(u);
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  },
  async post(u, body) {
    const r = await fetch(u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body || {}) });
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  }
};

const S = {
  boot: null, graph: null, node: null, session: null,
  report: null, samples: [], asked: new Set(),
  timer: null, elapsed: 0, typing: false, lastUtter: 0
};

/* ---------------------------------------------------------------- 路由 */
function go(id) {
  if (location.hash !== "#" + id) { location.hash = id; return; }
  show(id);
}
function show(id) {
  $$(".view").forEach(v => v.classList.toggle("on", v.id === "view-" + id));
  $$(".nv").forEach(n => n.classList.toggle("on", n.dataset.go === id));
  $("#main").scrollTop = 0;
  ({ today: renderToday, explain: renderExplain, report: renderReport,
     map: renderMap, review: renderReview, growth: renderGrowth }[id] || renderToday)();
}
window.addEventListener("hashchange", () => show((location.hash || "#today").slice(1)));
document.addEventListener("click", e => {
  const t = e.target.closest("[data-go]");
  if (t) { e.preventDefault(); go(t.dataset.go); }
});

/* ---------------------------------------------------------------- 首页 */
async function renderToday() {
  try {
    const b = await api.get("/api/bootstrap");
    S.boot = b;
    const d = new Date(b.today + "T00:00:00");
    const wk = "日一二三四五六"[d.getDay()];
    $("#todayDate").textContent = `${d.getFullYear()} 年 ${d.getMonth() + 1} 月 ${d.getDate()} 日 · 星期${wk}`;
    $("#hello").textContent = `${nowGreet()}，${b.student.name || "同学"}`;
    $("#todaySub").textContent = `今天有 1 个推荐讲解、${b.stats.due_cards} 张复述卡在等你。`;
    $("#uname").textContent = b.student.name || "同学";
    $("#uclass").textContent = b.student.cls || "";
    $("#avatar").textContent = (b.student.name || "林").slice(0, 1);

    $("#stStreak").textContent = b.stats.streak;
    $("#stWeek").textContent = b.stats.week_sessions;
    $("#stDue").textContent = b.stats.due_cards;

    const p = b.pick;
    $("#heroTag").textContent = `今日推荐 · ${p.grade} ${p.chapter.split(" ").pop()}`;
    $("#heroTitle").textContent = p.name;
    $("#heroDesc").textContent = `${p.summary} 你上次讲到这里停住了，这次试着把最关键的一句讲清楚。`;
    $("#heroMeta").textContent = `建议 6 分钟 · ${p.n_assertions} 个关键点`;
    $("#btnStartToday").onclick = () => startSession(p.id);
    $("#heroGo").onclick = () => startSession(p.id);

    // 本周目标
    updateGoal(b.stats.week_sessions);

    // 待复述队列
    $("#queue").innerHTML = b.due_cards.map(c => {
      const isDue = c.due <= b.today;
      const cls = isDue ? "r" : (c.due <= addDays(b.today, 1) ? "a" : "g");
      const label = isDue ? "今天" : c.due.slice(5).replace("-", "/");
      return `<div class="row" data-node="${c.node_id}">
        <i class="dot ${cls}"></i>
        <div class="rw"><div class="t">${esc(c.name)}</div>
          <div class="s">${esc(c.grade)} · 下次复述 ${c.due.slice(5)}</div></div>
        <span class="tag ${cls === "r" ? "r" : cls === "a" ? "a" : ""}">${label}</span></div>`;
    }).join("") || `<div class="empty-s">暂时没有待复述的卡片</div>`;
    $$("#queue .row").forEach(r => r.onclick = () => startSession(r.dataset.node));

    // 薄弱链路
    const ch = b.weak_chain || [];
    $("#weakHint").textContent = ch.length
      ? `你的问题来自上游节点，而不是最后那个知识点本身。`
      : "还没有形成明显的薄弱链路。";
    const wn = (b.weak_nodes || []).filter(n => !ch.some(c => c.id === n.id)).slice(0, 3);
    $("#weakBody").innerHTML = `
      <div class="chain">${ch.map((n, i) => `${i ? '<span class="arw">›</span>' : ""}
        <div class="nd ${n.mastery >= 0.75 ? "" : n.mastery >= 0.45 ? "a" : "r"}" data-node="${n.id}">
          <b>${esc(n.name)}</b>${n.mastery.toFixed(2)}</div>`).join("")}</div>
      ${wn.length ? `<div class="grp" style="font-size:9.5px;color:var(--ink3);margin:16px 0 4px">其他值得补的</div>` +
        wn.map(n => `<div class="row" data-node="${n.id}" style="padding:8px 0;cursor:pointer">
          <div class="rw"><div class="t" style="font-size:11px">${esc(n.name)}</div></div>
          <div class="bar"><i style="width:${Math.round(n.mastery * 100)}%;background:${n.mastery >= 0.45 ? "#BE8320" : "#C9502B"}"></i></div>
          <span class="tag">${n.mastery.toFixed(2)}</span></div>`).join("") : ""}`;
    $$("#weakBody [data-node]").forEach(el => el.onclick = () => startSession(el.dataset.node));
    const first = ch[0];
    $("#weakAdvice").innerHTML = first
      ? `<b>建议路径</b>　先用 90 秒重讲「${esc(first.name)}」，再回到「${esc(ch[ch.length - 1].name)}」。`
      : `<b>建议路径</b>　从今日推荐开始讲起。`;
    $$("#weakChain .nd").forEach((el, i) => el.onclick = () => startSession(ch[i].id));
  } catch (e) {
    $("#todaySub").textContent = "加载失败：" + e.message;
  }
}
const nowGreet = () => { const h = new Date().getHours(); return h < 11 ? "早上好" : h < 14 ? "中午好" : h < 18 ? "下午好" : "晚上好"; };
function updateGoal(n) {
  const pct = Math.min(100, Math.round(n / 5 * 100));
  $("#goalText").textContent = n >= 5 ? `本周已讲 ${n} 次 · 达标` : `讲解 ${n} / 5 次`;
  $("#goalPct").textContent = pct + "%";
  $("#goalBar").style.width = pct + "%";
}
const addDays = (iso, n) => {
  const d = new Date(iso + "T00:00:00");
  d.setDate(d.getDate() + n);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
};

/* ---------------------------------------------------------------- 讲解台 */
async function startSession(nodeId) {
  try {
    const s = await api.post("/api/session/start", { node_id: nodeId });
    S.session = s; S.asked = new Set(); S.seen = new Set(); S.report = null;
    S.node = await api.get("/api/node/" + nodeId);
    S.samples = await api.get("/api/samples");
    if (location.hash === "#explain") renderExplain(); else go("explain");
  } catch (e) { alert("无法开始讲解：" + e.message); }
}

function renderExplain() {
  if (!S.session) {
    const id = S.boot?.pick?.id || "archimedes";
    startSession(id); return;
  }
  const n = S.session.node;
  $("#exEyebrow").textContent = `${n.grade} · ${n.chapter.replace(/^第.+?章\s*/, "")} · 本次讲解`;
  $("#exTitle").textContent = n.name;
  $("#assertCount").textContent = n.n_assertions;
  $("#hintText").textContent = `例如：${S.node?.example || n.summary}`;
  $("#hintText").classList.remove("on");
  $("#btnHint").onclick = () => $("#hintText").classList.toggle("on");

  const ta = $("#transcript");
  ta.value = "";
  ta.oninput = debounce(liveTick, 900);

  // 断言 chips
  $("#assertChips").innerHTML = (S.node?.assertions || []).map(a =>
    `<span data-a="${a.id}" title="${esc(a.text)}">${esc(short(a.text, 14))}</span>`).join("");

  // 声波
  const w = $("#wave"); w.innerHTML = "";
  for (let i = 0; i < 18; i++) {
    const b = document.createElement("i");
    b.style.height = (6 + Math.abs(Math.sin(i * 0.9)) * 18) + "px";
    b.style.animationDelay = (i * 0.06) + "s";
    w.appendChild(b);
  }

  // 示例按钮
  const sample = S.samples.find(s => s.node === n.id);
  const btn = $("#btnSample");
  btn.disabled = !sample;
  btn.textContent = sample ? `播放示例：${sample.title}` : "该知识点暂无示例";
  btn.onclick = () => sample && playSample(sample);

  resetLive();
  $("#btnFinish").onclick = finishSession;
  $("#btnBackPick").onclick = () => { stopTimer(); go("map"); };
}

function resetLive() {
  stopTimer(); S.elapsed = 0; $("#timer").textContent = "00:00";
  $("#progText").textContent = `已覆盖 0 / ${S.session?.assertion_count || 0} 点`;
  $("#progBar").style.width = "0%";
  $("#probes").innerHTML = `<div class="empty-s">讲述过程中，小回会在你讲得含糊的地方举手。</div>`;
  $("#probeCount").textContent = "0";
  $$("#assertChips span").forEach(s => s.className = "");
  $("#recBtn").classList.remove("on");
  $("#recText").textContent = "未开始 · 点左侧按钮计时";
}

function debounce(fn, ms) { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; }
const sleep = ms => new Promise(r => setTimeout(r, ms));
const short = (s, n) => (s.length > n ? s.slice(0, n) + "…" : s);

async function liveTick() {
  const text = $("#transcript").value.trim();
  if (!text || !S.session) return;
  try {
    const r = await api.post("/api/session/utter", { session_id: S.session.session_id, text });
    $("#progText").textContent = `已覆盖 ${r.covered} / ${r.total} 点`;
    $("#progBar").style.width = Math.round(r.coverage) + "%";
    const cov = new Set(r.covered_ids || []), par = new Set(r.partial_ids || []), bad = new Set(r.contradicted_ids || []);
    $$("#assertChips span").forEach(el => {
      const id = el.dataset.a;
      el.className = bad.has(id) ? "miss" : cov.has(id) ? "on" : par.has(id) ? "pt" : "";
    });
    (r.misconceptions || []).forEach(m => addProbe(m.sentence, `讲反了：${m.title}`, "r", "mis:" + m.id));
    if (r.probe) addProbe(r.probe.text, "追问", "a", "probe:" + r.probe.id);
  } catch (e) { /* 实时请求失败不打断讲述 */ }
}

function addProbe(text, label, kind, key) {
  if (!S.seen) S.seen = new Set();
  const k = key || String(text).replace(/[？?。！!\s]+/g, "");
  if (S.seen.has(k)) return;
  S.seen.add(k);
  const box = $("#probes");
  if (box.querySelector(".empty-s")) box.innerHTML = "";
  const d = document.createElement("div");
  d.className = "bub";
  d.innerHTML = `${esc(text)}<div class="bst"><span class="tag ${kind}">${esc(label)}</span>${new Date().toTimeString().slice(0, 5)}</div>`;
  box.appendChild(d);
  while (box.children.length > 5) box.removeChild(box.firstChild);
  $("#probeCount").textContent = box.children.length;
  box.scrollTop = box.scrollHeight;
}

async function playSample(sample) {
  if (S.typing) return;
  S.typing = true;
  const btn = $("#btnSample"); btn.disabled = true;
  const ta = $("#transcript");
  ta.value = "";
  startTimer();
  const text = sample.text;
  let i = 0;
  while (i < text.length) {
    i += 2 + Math.floor(Math.random() * 3);
    ta.value = text.slice(0, i);
    ta.scrollTop = ta.scrollHeight;
    if (i % 30 < 3) await liveTick();
    await sleep(70);
  }
  await liveTick();
  S.typing = false; btn.disabled = false;
}

function startTimer() {
  if (S.timer) return;
  $("#recBtn").classList.add("on");
  $("#recText").textContent = "正在记录 · 说完一句可以停一下";
  S.timer = setInterval(() => {
    S.elapsed++;
    const m = String(Math.floor(S.elapsed / 60)).padStart(2, "0");
    const s = String(S.elapsed % 60).padStart(2, "0");
    $("#timer").textContent = `${m}:${s}`;
  }, 1000);
}
function stopTimer() { clearInterval(S.timer); S.timer = null; }

async function finishSession() {
  const text = $("#transcript").value.trim();
  if (!text) { alert("还没有讲内容，先说两句吧。"); return; }
  stopTimer();
  $("#btnFinish").disabled = true;
  try {
    const r = await api.post("/api/session/finish", { session_id: S.session.session_id, text });
    S.report = r;
    S.session = null;
    go("report");
  } catch (e) { alert("生成报告失败：" + e.message); }
  $("#btnFinish").disabled = false;
}

/* ---------------------------------------------------------------- 报告 */
function renderReport() {
  const r = S.report;
  if (!r) { $("#reportBody").innerHTML = `<div class="empty">还没有报告。先去讲解台讲一段吧。</div>`; return; }
  const sc = r.scores;
  $("#rpEyebrow").textContent = `讲解报告 · ${new Date().toLocaleString("zh-CN", { hour12: false }).slice(0, 16)} · 掌握度 ${r.mastery_after}`;
  $("#rpTitle").textContent = "这次讲得怎么样";
  $("#btnAgain").onclick = () => startSession(r.node);
  $("#btnToReview").onclick = () => go("review");

  const C = 2 * Math.PI * 42;
  const first = r.misconceptions[0];
  const covered = r.coverage.covered, partial = r.coverage.partial, missed = r.coverage.missed;
  const chip = (a, cls) => `<span class="${cls}" title="${esc(a.text)}${a.contradicted ? "（讲反了）" : ""}">${a.contradicted ? "✕ " : ""}${esc(short(a.text, 16))}</span>`;

  $("#reportBody").innerHTML = `
  <div class="rp">
    <div class="r3">
      <div class="c">
        <div class="ct">综合得分</div>
        <div class="score">
          <div class="ring">
            <svg width="96" height="96"><circle cx="48" cy="48" r="42" fill="none" stroke="#EEE8DC" stroke-width="9"/>
              <circle cx="48" cy="48" r="42" fill="none" stroke="#2E5D4E" stroke-width="9" stroke-linecap="round"
                stroke-dasharray="${C.toFixed(1)}" stroke-dashoffset="${(C * (1 - sc.total / 100)).toFixed(1)}"/></svg>
            <div class="val"><b>${sc.total}</b><span>综合得分</span></div>
          </div>
          <div class="dims">
            ${dim("覆盖", sc.coverage)}${dim("准确", sc.accuracy)}${dim("逻辑", sc.logic)}
            ${dim("术语", sc.terms)}${dim("举例", sc.examples)}${dim("流畅", sc.fluency)}
          </div>
        </div>
        <div class="divider"></div>
        <div class="kv"><span>覆盖率</span><b>${Math.round(r.coverage.rate * 100)}%</b></div>
        <div class="kv"><span>讲反了</span><b style="color:${r.misconceptions.length ? "var(--red)" : "var(--green)"}">${r.misconceptions.length} 处</b></div>
        <div class="kv"><span>下次复述</span><b>${r.next_due.slice(5)}（${r.interval} 天后）</b></div>
      </div>

      <div class="c" style="display:flex;flex-direction:column;align-items:center">
        <div class="ct" style="align-self:flex-start">六维雷达</div>
        ${radar(sc)}
      </div>

      <div class="c">
        <div class="ct">讲了什么<span class="more">${covered.length + partial.length + missed.length} 个断言单元</span></div>
        <div class="grp">讲到位 · ${covered.length}</div>
        <div class="ck">${covered.map(a => chip(a, "ok")).join("") || '<span>—</span>'}</div>
        <div class="grp">一带而过 · ${partial.length}</div>
        <div class="ck">${partial.map(a => chip(a, "pt")).join("") || '<span>—</span>'}</div>
        <div class="grp">没提到 · ${missed.length}</div>
        <div class="ck">${missed.map(a => chip(a, "no")).join("") || '<span>—</span>'}</div>
        ${first ? `<div class="divider"></div><span class="tag r">讲反了</span>
          <div style="font-size:11px;color:var(--ink2);margin-top:8px;line-height:1.7">
          <b>「${esc(short(first.sentence, 30))}」</b> —— 命中迷思 ${first.id}，${esc(first.correction)}</div>` : ""}
      </div>
    </div>

    <div class="c" style="display:grid;grid-template-columns:1fr 300px;gap:18px">
      <div style="display:flex;flex-direction:column">
        <div class="ct">根因链：他卡住的不是${esc(r.node_name)}<span class="more">沿依赖关系反推</span></div>
        <div class="chain" style="margin-top:12px">${chainHTML(r)}</div>
        ${r.root_causes.length > 1 ? `<div style="font-size:10px;color:var(--ink3);margin-top:9px">
          另外还有 ${r.root_causes.slice(1).map(x => `「${esc(x.name)}」${x.mastery.toFixed(2)}`).join("、")} 也在拖后腿。</div>` : ""}
        <div style="display:flex;gap:14px;margin-top:14px;font-size:10.5px;color:var(--ink2);line-height:1.75">
          ${r.root_causes[0] ? `<div style="flex:1;border-left:2px solid var(--red);padding-left:10px">
            你在「${esc(r.root_causes[0].name)}」这一环上没讲透，它沿着依赖关系直接拖住了本次内容。</div>` : ""}
          ${r.misconceptions[0] ? `<div style="flex:1;border-left:2px solid var(--amber);padding-left:10px">
            同时命中迷思「${esc(r.misconceptions[0].title)}」，属于${esc(r.misconceptions[0].type)}。</div>` : ""}
        </div>
        <div class="nextday" style="margin-top:auto">
          <div class="t">明天复述时，只要把这一句讲清楚</div>
          <div class="x">「${esc(r.tomorrow)}」</div>
        </div>
      </div>
      <div style="border-left:1px solid var(--line2);padding-left:16px;display:flex;flex-direction:column">
        <div class="ct">三句人话</div>
        ${r.suggestions.map((s, i) => `<div class="sug"><b>${i + 1}</b><span>${esc(s)}</span></div>`).join("")}
        ${first ? `<div class="quote" style="margin-top:auto">
          <div class="qt">原话摘录</div>
          <div class="qx">「${esc(first.sentence)}」</div>
          <div class="qn">↳ 命中的迷思：${esc(first.title)}</div></div>` : ""}
      </div>
    </div>
  </div>`;
}
const dim = (k, v) => `<div class="dm"><em>${k}</em><div class="db"><i style="width:${v}%"></i></div><b>${v}</b></div>`;

function chainHTML(r) {
  const rc0 = r.root_causes[0];
  const names = rc0 && rc0.path && rc0.path.length ? rc0.path : [r.node_name];
  const find = nm => r.root_causes.find(x => x.name === nm);
  return names.map((nm, i) => {
    const isTarget = nm === r.node_name && i === names.length - 1;
    const rc = find(nm);
    const m = rc ? rc.mastery : null;
    const cls = isTarget ? "r" : m == null ? "" : m >= 0.75 ? "" : m >= 0.45 ? "a" : "r";
    const sub = isTarget
      ? `${Math.round(r.coverage.rate * 100)}% 覆盖<br><span style="font-size:9px;opacity:.75">本次</span>`
      : `${m == null ? "—" : m.toFixed(2)} 掌握<br><span style="font-size:9px;color:var(--ink3)">${esc(rc ? rc.grade : "")}</span>`;
    const gap = i ? '<span class="arw">›</span>' : "";
    return `${gap}<div class="nd ${cls}"><b>${esc(nm)}</b>${sub}</div>`;
  }).join("");
}

function radar(sc) {
  const items = [["覆盖", sc.coverage], ["准确", sc.accuracy], ["逻辑", sc.logic],
                 ["术语", sc.terms], ["举例", sc.examples], ["流畅", sc.fluency]];
  const cx = 110, cy = 108, R = 76;
  const pt = (i, v) => {
    const a = -Math.PI / 2 + i * Math.PI / 3;
    return [cx + Math.cos(a) * R * v / 100, cy + Math.sin(a) * R * v / 100];
  };
  const ring = k => items.map((_, i) => pt(i, k).map(n => n.toFixed(1)).join(",")).join(" ");
  const poly = items.map((it, i) => pt(i, it[1]).map(n => n.toFixed(1)).join(",")).join(" ");
  return `<svg width="230" height="216" viewBox="0 0 230 216">
    <g fill="none" stroke="#E9E3D7">
      <polygon points="${ring(100)}"/><polygon points="${ring(66)}"/><polygon points="${ring(33)}"/>
      ${items.map((_, i) => { const [x, y] = pt(i, 100); return `<line x1="${cx}" y1="${cy}" x2="${x.toFixed(1)}" y2="${y.toFixed(1)}"/>`; }).join("")}
    </g>
    <polygon points="${poly}" fill="rgba(46,93,78,.16)" stroke="#2E5D4E" stroke-width="1.8"/>
    ${items.map((it, i) => { const [x, y] = pt(i, it[1]); return `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="2.6" fill="#2E5D4E"/>`; }).join("")}
    ${items.map((it, i) => {
      const [x, y] = pt(i, 118);
      const anchor = Math.abs(x - cx) < 6 ? "middle" : x > cx ? "start" : "end";
      return `<text x="${x.toFixed(1)}" y="${(y + 3).toFixed(1)}" text-anchor="${anchor}" font-size="9" fill="#918A7F">${it[0]}</text>`;
    }).join("")}
  </svg>`;
}

/* ---------------------------------------------------------------- 地图 */
let MAPCACHE = null;
async function renderMap() {
  try {
    const g = await api.get("/api/graph");
    MAPCACHE = g;
    const byId = Object.fromEntries(g.nodes.map(n => [n.id, n]));
    const layer = {};
    const depth = id => {
      if (layer[id] != null) return layer[id];
      const pre = g.edges.filter(e => e.to === id).map(e => e.from);
      layer[id] = pre.length ? Math.max(...pre.map(depth)) + 1 : 0;
      return layer[id];
    };
    g.nodes.forEach(n => depth(n.id));
    const cols = {};
    g.nodes.forEach(n => (cols[layer[n.id]] = cols[layer[n.id]] || []).push(n));

    const W = 740, H = 540;
    const pos = {};
    const maxL = Math.max(...Object.keys(cols).map(Number));
    Object.entries(cols).forEach(([L, arr]) => {
      const x = 72 + (maxL ? L / maxL : 0) * (W - 150);
      arr.forEach((n, i) => {
        const y = H / 2 + (i - (arr.length - 1) / 2) * Math.min(120, 420 / Math.max(1, arr.length - 1 || 1));
        pos[n.id] = [x, arr.length === 1 ? H / 2 : y];
      });
    });

    const color = st => st === "mastered" ? { f: "#fff", s: "#417D68", t: "#1F1D1A" }
      : st === "fuzzy" ? { f: "#FAF0DA", s: "#BE8320", t: "#1F1D1A" }
      : st === "weak" ? { f: "#FBEAE4", s: "#C9502B", t: "#C9502B" }
      : { f: "#fff", s: "#C0B8A8", t: "#8E877C" };

    const edges = g.edges.map(e => {
      const [x1, y1] = pos[e.from], [x2, y2] = pos[e.to];
      const mx = (x1 + x2) / 2;
      return `<path d="M${x1},${y1} C${mx},${y1} ${mx},${y2} ${x2},${y2}" fill="none" stroke="#CFC7B8" stroke-width="1.4" marker-end="url(#arw)"/>`;
    }).join("");

    const nodes = g.nodes.map(n => {
      const [x, y] = pos[n.id], c = color(n.status);
      const dash = n.status === "empty" ? ' stroke-dasharray="4 3"' : "";
      const nm = n.short || n.name;
      const inner = `<text x="${x}" y="${y + 3}" text-anchor="middle" font-size="10" fill="${c.t}">${esc(nm)}</text>`;
      return `<g class="mapnode" data-id="${n.id}" style="cursor:pointer">
        <circle cx="${x}" cy="${y}" r="31" fill="${c.f}" stroke="${c.s}" stroke-width="2"${dash}/>
        ${inner}
        <text x="${x}" y="${y + 47}" text-anchor="middle" font-size="8.5" fill="${c.t}" opacity=".85">${n.mastery.toFixed(2)}</text>
        <text x="${x}" y="${y + 59}" text-anchor="middle" font-size="7.5" fill="#B0A897">${esc(n.grade)}</text>
      </g>`;
    }).join("");

    $("#mapSvg").setAttribute("viewBox", `0 0 ${W} ${H}`);
    $("#mapSvg").innerHTML = `<defs><marker id="arw" viewBox="0 0 10 10" refX="9" refY="5"
      markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="#C9C1B2"/></marker></defs>${edges}${nodes}`;
    $$(".mapnode").forEach(el => el.onclick = () => showNode(el.dataset.id));
    $("#mapEyebrow").textContent = `初中物理 · ${g.nodes.length} 个知识点 · ` +
      `已掌握 ${g.nodes.filter(n => n.status === "mastered").length} 个`;
    if (S.boot) showNode(S.boot.pick.id);
  } catch (e) { $("#mapSide").innerHTML = `<div class="empty-s">加载失败：${esc(e.message)}</div>`; }
}

async function showNode(id) {
  try {
    const n = await api.get("/api/node/" + id);
    const st = { mastered: ["已掌握", ""], fuzzy: ["模糊", "a"], weak: ["未掌握", "r"], empty: ["未学习", "n"] }[n.status] || ["—", ""];
    $("#mapSide").innerHTML = `
      <div style="display:flex;align-items:center;gap:8px">
        <div style="width:10px;height:10px;border-radius:50%;background:${n.status === "mastered" ? "#417D68" : n.status === "fuzzy" ? "#BE8320" : n.status === "weak" ? "#C9502B" : "#C0B8A8"}"></div>
        <h3>${esc(n.name)}</h3></div>
      <div class="muted">${esc(n.grade)} · ${esc(n.chapter)}</div>
      <div style="display:flex;gap:6px;margin-top:10px">
        <span class="tag ${st[1]}">掌握度 ${n.mastery.toFixed(2)}</span>
        <span class="tag">${n.n_assertions} 条断言</span></div>
      <div class="divider"></div>
      <div class="muted">前驱 · ${n.prereqs.length}</div>
      ${n.prereqs.map(p => `<div class="kv"><span>● ${esc(p.name)}</span><b>${p.mastery.toFixed(2)}</b></div>`).join("") || '<div class="empty-s">无（起始节点）</div>'}
      <div class="muted" style="margin-top:10px">后继 · ${n.successors.length}</div>
      ${n.successors.map(p => `<div class="kv"><span>○ ${esc(p.name)}</span></div>`).join("") || '<div class="empty-s">无</div>'}
      <div class="divider"></div>
      <div style="font-size:10.5px;color:var(--ink2);line-height:1.75">${esc(n.summary)}</div>
      <button class="bt p" style="margin-top:auto;justify-content:center" id="sideStart">开始讲解</button>`;
    $("#sideStart").onclick = () => startSession(n.id);
  } catch (e) { $("#mapSide").innerHTML = `<div class="empty-s">${esc(e.message)}</div>`; }
}

/* ---------------------------------------------------------------- 复述 */
async function renderReview() {
  try {
    const r = await api.get("/api/review");
    const today = r.today;
    const due = r.cards.filter(c => c.due <= today).sort((a, b) => b.overdue - a.overdue);
    const upcoming = r.cards.filter(c => c.due > today);
    $("#rvEyebrow").textContent = `遗忘曲线 · 共 ${r.cards.length} 张卡片 · 今天到期 ${due.length} 张`;

    const card = (c) => {
      const cls = c.due < today ? "urgent" : c.due === today ? "soon" : "";
      const tag = c.due < today ? `<span class="tag r">逾期 ${c.overdue} 天</span>`
        : c.due === today ? `<span class="tag a">今天</span>` : `<span class="tag">${c.due.slice(5)}</span>`;
      return `<div class="c rv-card ${cls}" style="display:flex;flex-direction:column">
        <div style="display:flex;justify-content:space-between;align-items:flex-start">
          <div><div style="font-size:12.5px;font-weight:700">${esc(c.name)}</div>
            <div style="font-size:9.5px;color:var(--ink3);margin-top:3px">${esc(c.grade)} · 间隔 ${c.interval} 天</div></div>
          ${tag}</div>
        <div style="font-size:10px;color:var(--ink2);margin-top:10px;line-height:1.7">
          复述目标：${esc(c.example || "把这个知识点讲清楚")}。</div>
        <button class="bt p" style="margin-top:auto;align-self:flex-start;font-size:11px;padding:6px 12px" data-node="${c.node_id}">开始复述</button>
      </div>`;
    };

    // 未来七天
    const days = [];
    for (let i = 0; i < 7; i++) days.push(addDays(today, i));
    const wk = ["日", "一", "二", "三", "四", "五", "六"];
    const grid = days.map((d, i) => {
      const list = r.cards.filter(c => c.due === d);
      const dd = new Date(d + "T00:00:00");
      return `<div class="day ${i === 0 ? "on" : ""}">
        <div class="dn2">${i === 0 ? "今天" : "周" + wk[dd.getDay()]}</div>
        <div class="dd">${dd.getDate()}</div>
        ${list.map(c => `<div class="it ${c.due < today ? "r" : c.overdue ? "a" : "n"}">${esc(c.name)}</div>`).join("") || '<div class="it n">—</div>'}
      </div>`;
    }).join("");

    $("#reviewBody").innerHTML = `
      <div class="rv-cards">${due.slice(0, 3).map(card).join("") || '<div class="c"><div class="empty-s">今天没有到期的卡片，去讲一个新的吧。</div></div>'}</div>
      <div class="c">
        <div class="ct">未来七天<span class="more">按 FSRS 排期</span></div>
        <div class="days" style="margin-top:12px">${grid}</div>
      </div>
      <div class="c" style="margin-top:12px;display:flex;gap:20px;align-items:center">
        <div style="flex:1;font-size:10.5px;color:var(--ink2);line-height:1.8">
          <b style="color:var(--green)">为什么讲出来更记得住？</b><br>
          讲述比再认要求更高的提取强度。同样的三分钟，复述的保持率约为重读的两倍，因此间隔可以拉得更长。</div>
        <div style="font-size:10px;color:var(--ink3);line-height:1.9;text-align:right">
          已排期 ${r.cards.length} 张<br>逾期 ${r.cards.filter(c => c.due < today).length} 张</div>
      </div>
      <div class="c" style="margin-top:12px">
        <div class="ct">全部卡片<span class="more">共 ${r.cards.length} 张 · 按到期排序</span></div>
        <div style="margin-top:6px">
          ${r.cards.map(c => {
            const st = c.due < today ? ["逾期 " + c.overdue + " 天", "r"]
              : c.due === today ? ["今天", "a"] : [c.due.slice(5), ""];
            return `<div class="row"><i class="dot ${st[1] === "r" ? "r" : st[1] === "a" ? "a" : "g"}"></i>
              <div class="rw"><div class="t">${esc(c.name)}</div>
                <div class="s">${esc(c.grade)} · 当前间隔 ${c.interval} 天 · ${esc(c.example)}</div></div>
              <span class="tag ${st[1]}">${st[0]}</span></div>`;
          }).join("")}
        </div>
      </div>`;
    $$("#reviewBody [data-node]").forEach(b => b.onclick = () => startSession(b.dataset.node));
    $("#btnReviewStart").onclick = () => due[0] ? startSession(due[0].node_id) : go("map");
  } catch (e) { $("#reviewBody").innerHTML = `<div class="empty">加载失败：${esc(e.message)}</div>`; }
}

/* ---------------------------------------------------------------- 成长 */
async function renderGrowth() {
  try {
    const g = await api.get("/api/growth");
    const tr = g.trend;
    $("#grEyebrow").textContent = `累计 ${g.total_sessions} 次讲解 · 约 ${g.total_sessions * 3} 分钟`;
    const W = 620, H = 180, pad = 24;
    const maxV = 100, minV = 30;
    const xs = i => tr.length === 1 ? W / 2 : pad + i * (W - 2 * pad) / (tr.length - 1);
    const ys = v => H - pad - (v - minV) / (maxV - minV) * (H - 2 * pad);
    const pts = tr.map((t, i) => [xs(i), ys(t.total)]);
    const path = pts.map((p, i) => (i ? "L" : "M") + p[0].toFixed(1) + "," + p[1].toFixed(1)).join(" ");
    const area = path + ` L${pts.length ? pts[pts.length - 1][0].toFixed(1) : pad},${H - pad} L${pts.length ? pts[0][0].toFixed(1) : pad},${H - pad} Z`;

    const dist = g.distribution;
    const total = Object.values(dist).reduce((a, b) => a + b, 0) || 1;
    const segs = [["已掌握", dist.mastered, "#417D68"], ["模糊", dist.fuzzy, "#BE8320"],
                  ["未掌握", dist.weak, "#C9502B"], ["未学习", dist.empty, "#DAD3C5"]];
    const C = 2 * Math.PI * 52;
    let off = 0;
    const donut = segs.map(([n, v, c]) => {
      const len = C * v / total;
      const el = `<circle cx="70" cy="70" r="52" fill="none" stroke="${c}" stroke-width="18"
        stroke-dasharray="${len.toFixed(1)} ${(C - len).toFixed(1)}" stroke-dashoffset="${(-off).toFixed(1)}"/>`;
      off += len; return el;
    }).join("");

    $("#growthBody").innerHTML = `
      <div class="gr-grid">
        <div style="display:flex;flex-direction:column;gap:12px">
          <div class="c">
            <div class="ct">讲解质量趋势<span class="more">最近 ${tr.length} 次 · 综合分</span></div>
            ${tr.length ? `<svg class="chart" viewBox="0 0 ${W} ${H}" style="margin-top:10px">
              ${[0, 1, 2, 3].map(i => `<line x1="0" x2="${W}" y1="${pad + i * (H - 2 * pad) / 3}" y2="${pad + i * (H - 2 * pad) / 3}" stroke="#F0EBE1"/>`).join("")}
              <path d="${area}" fill="rgba(46,93,78,.08)"/>
              <path d="${path}" fill="none" stroke="#2E5D4E" stroke-width="2.2" stroke-linejoin="round"/>
              ${pts.map(p => `<circle cx="${p[0].toFixed(1)}" cy="${p[1].toFixed(1)}" r="3.5" fill="#fff" stroke="#2E5D4E" stroke-width="2"/>`).join("")}
              ${pts.map((p, i) => `<text x="${p[0].toFixed(1)}" y="${H - 6}" font-size="8" fill="#B0A897" text-anchor="middle">${tr[i].date.slice(5)}</text>`).join("")}
              ${pts.map((p, i) => `<text x="${p[0].toFixed(1)}" y="${(p[1] - 8).toFixed(1)}" font-size="9" fill="#2E5D4E" text-anchor="middle">${tr[i].total}</text>`).join("")}
            </svg>` : '<div class="empty-s">还没有讲解记录</div>'}
          </div>
          <div class="c">
            <div class="ct">最近讲解<span class="more">全部存在本地</span></div>
            <div style="margin-top:6px">
              ${g.recent.map(s => `<div class="rec" data-node="${s.node_id}">
                <div class="ply" style="width:22px;height:22px;border-radius:50%;border:1px solid #D9D2C4;display:flex;align-items:center;justify-content:center">
                  <i style="width:0;height:0;border-left:5px solid #8D8676;border-top:3.5px solid transparent;border-bottom:3.5px solid transparent;margin-left:1px"></i></div>
                <div style="flex:1"><div class="rt">${esc(s.node)}</div>
                  <div class="rs">${s.date.replace("T", " ").slice(5, 16)} · ${s.total} 分</div></div>
                <span class="tag ${s.total >= 80 ? "" : s.total >= 60 ? "a" : "r"}">${s.total >= 80 ? "讲透了" : s.total >= 60 ? "待加强" : "有缺口"}</span>
              </div>`).join("") || '<div class="empty-s">还没有记录</div>'}
            </div>
          </div>
        </div>
        <div style="display:flex;flex-direction:column;gap:12px">
          <div class="c">
            <div class="ct">能力标签<span class="more">${g.total_sessions} 次</span></div>
            <div class="tags">${g.tags.map(t => `<span class="tg ${t.kind}">${esc(t.text)}</span>`).join("")}</div>
            <div style="margin-top:12px;font-size:10px;color:var(--ink2);line-height:1.8;border-top:1px dashed var(--line2);padding-top:10px">
              平均：覆盖 ${g.avg.coverage ?? "—"} · 准确 ${g.avg.accuracy ?? "—"} · 逻辑 ${g.avg.logic ?? "—"} · 举例 ${g.avg.examples ?? "—"}
            </div>
          </div>
          <div class="c" style="flex:1;display:flex;flex-direction:column">
            <div class="ct">掌握分布</div>
            <div style="display:flex;align-items:center;gap:10px;margin-top:12px">
              <svg width="140" height="140" viewBox="0 0 140 140">
                <g transform="rotate(-90 70 70)">${donut}</g>
                <text x="70" y="68" text-anchor="middle" font-size="22" font-family="Songti SC,serif" fill="#1F1D1A">${total}</text>
                <text x="70" y="85" text-anchor="middle" font-size="8.5" fill="#918A7F">个知识点</text>
              </svg>
              <div style="flex:1;font-size:9.5px;color:var(--ink2);line-height:2.2">
                ${segs.map(([n, v, c]) => `<div><i style="display:inline-block;width:7px;height:7px;border-radius:2px;background:${c};margin-right:6px"></i>${n}<span style="float:right;color:var(--ink3)">${v}</span></div>`).join("")}
              </div>
            </div>
            <div class="divider"></div>
            <div class="ct" style="font-size:11px">平均能力</div>
            <div style="margin-top:8px">
              ${[["覆盖", g.avg.coverage], ["准确", g.avg.accuracy], ["逻辑", g.avg.logic], ["举例", g.avg.examples]]
                .map(([k, v]) => `<div class="dm" style="margin-bottom:7px"><em>${k}</em>
                  <div class="db"><i style="width:${v || 0}%"></i></div><b>${v ?? "—"}</b></div>`).join("")}
            </div>
          </div>
        </div>
      </div>`;
    $$("#growthBody [data-node]").forEach(el => el.onclick = () => startSession(el.dataset.node));
  } catch (e) { $("#growthBody").innerHTML = `<div class="empty">加载失败：${esc(e.message)}</div>`; }
}

/* ---------------------------------------------------------------- 启动 */
async function runDemo(sampleId, hold) {
  try {
    const list = await api.get("/api/samples");
    const s = list.find(x => x.id === sampleId) || list[0];
    await startSession(s.node);
    await sleep(300);
    await playSample(s);
    if (!hold) await finishSession();
  } catch (e) { console.error("demo failed", e); }
}

(async function init() {
  try {
    S.boot = await api.get("/api/bootstrap");
    updateGoal(S.boot.stats.week_sessions);
  } catch (e) { }
  $("#recBtn").onclick = () => { if (S.timer) { stopTimer(); $("#recBtn").classList.remove("on"); $("#recText").textContent = "已暂停 · 再点继续计时"; } else { startTimer(); } };
  $("#btnPickOther").onclick = () => go("map");
  $("#btnReset").onclick = async () => {
    if (!confirm("把演示数据恢复到初始状态？")) return;
    await api.post("/api/demo/reset", {});
    S.report = null; S.session = null; MAPCACHE = null;
    S.boot = await api.get("/api/bootstrap");
    show((location.hash || "#today").slice(1));
  };
  const q = new URLSearchParams(location.search);
  const demo = q.get("demo");
  if (demo) { await runDemo(demo, q.get("hold") === "1"); return; }
  show((location.hash || "#today").slice(1));
})();
