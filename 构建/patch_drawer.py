# -*- coding: utf-8 -*-
"""给讲解台加「参考答案抽屉」：点按钮从右侧滑出，不离开当前讲解会话。"""
import io
import os

P = r"E:\人工智能作业\大作业\应用\web\app.js"
s = io.open(P, encoding="utf-8").read()

# 1) 头部按钮改为打开抽屉
old = '  $("#btnRef").onclick = () => { S.ref = n.id; go("ref"); };'
new = '''  $("#btnRef").onclick = openRefDrawer;
  $("#btnDocRef").onclick = openRefDrawer;
  $("#drClose").onclick = closeRefDrawer;
  $("#drSpeak").onclick = () => { if (S.drawerNode) speakParagraph(S.drawerNode.reference); };'''
assert old in s, "btnRef binding not found"
s = s.replace(old, new)

# 2) 抽屉函数
anchor = "function pushChatTo(box, who, text, extra) {"
drawer = '''/* ---------------- 参考答案抽屉：不离开讲解台 ---------------- */
async function openRefDrawer() {
  const id = (S.session && S.session.node.id) || (S.refNode && S.refNode.id) || (S.boot && S.boot.pick && S.boot.pick.id);
  if (!id) return;
  try {
    const n = await api.get("/api/node/" + id);
    S.drawerNode = n;
    $("#drEyebrow").textContent = n.grade + " · " + n.chapter;
    $("#drTitle").textContent = n.name + " · 参考答案";
    $("#drBody").innerHTML =
      '<div class="dsec"><h4>标准讲解</h4><div class="dref">' + esc(n.reference) + '</div>' +
      '<div class="refex" style="margin-top:10px">' + esc(n.example) + '</div></div>' +
      '<div class="dsec"><h4>必须讲到的点 · ' + n.assertions.length + ' 条</h4><ul class="dlist">' +
      n.assertions.map(a => '<li>' + esc(a.text) + '<b>' + a.w.toFixed(1) + '</b></li>').join("") +
      '</ul></div>' +
      '<div class="dsec"><h4>常见错误 · ' + n.misconceptions.length + ' 条</h4>' +
      n.misconceptions.map(m => '<div class="dmis"><div class="t">✕ ' + esc(m.title) +
        '</div><div class="c">' + esc(m.correction) + '</div></div>').join("") +
      '</div>';
    $("#refDrawer").classList.add("on");
    S.drawerOpen = true;
  } catch (e) { alert("加载失败：" + e.message); }
}
function closeRefDrawer() {
  const d = $("#refDrawer");
  if (d) d.classList.remove("on");
  S.drawerOpen = false;
}

'''
assert anchor in s, "pushChatTo not found"
s = s.replace(anchor, drawer + anchor, 1)

# 3) 演示参数 drawer=1
old2 = '  if (demo) { await runDemo(demo, q.get("hold") === "1", q.get("answer") === "1"); return; }'
new2 = '''  if (demo) {
    await runDemo(demo, q.get("hold") === "1", q.get("answer") === "1");
    if (q.get("drawer") === "1") await openRefDrawer();
    return;
  }'''
assert old2 in s, "demo branch not found"
s = s.replace(old2, new2)

# 4) Esc 与点击外部关闭
old3 = 'window.addEventListener("hashchange", () => show((location.hash || "#today").slice(1)));'
new3 = '''window.addEventListener("hashchange", () => show((location.hash || "#today").slice(1)));
document.addEventListener("keydown", e => { if (e.key === "Escape") closeRefDrawer(); });
document.addEventListener("click", e => {
  if (!S.drawerOpen) return;
  if (e.target.closest("#refDrawer") || e.target.closest("#btnRef") || e.target.closest("#btnDocRef")) return;
  closeRefDrawer();
}, true);'''
assert old3 in s, "hashchange not found"
s = s.replace(old3, new3)

io.open(P, "w", encoding="utf-8", newline="").write(s)
print("app patched")
