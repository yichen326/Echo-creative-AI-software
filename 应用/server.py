# -*- coding: utf-8 -*-
"""回声 Echo —— 零依赖 + FastAPI 本地服务。

启动： python server.py
访问： http://127.0.0.1:8771
"""
import os
import sys
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "vendor"))
sys.path.insert(0, HERE)

from fastapi import FastAPI, HTTPException          # noqa: E402
from fastapi.responses import FileResponse, JSONResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles          # noqa: E402
from pydantic import BaseModel                       # noqa: E402

from engine import diagnose, srs                     # noqa: E402
from engine.bkt import Mastery                       # noqa: E402
from engine.kb import KnowledgeBase                  # noqa: E402
from engine import store                             # noqa: E402

KB = KnowledgeBase()
store.init()
store.seed_demo(KB)

WEB = os.path.join(HERE, "web")
app = FastAPI(title="Echo", docs_url="/api/docs")

SESSIONS = {}   # session_id -> {"node":..., "started":..., "asked":[...], "last_utter":0}


class StartReq(BaseModel):
    node_id: str
    student_id: str = store.DEMO_STUDENT


class UtterReq(BaseModel):
    session_id: str
    text: str
    student_id: str = store.DEMO_STUDENT


class FinishReq(BaseModel):
    session_id: str
    text: str
    student_id: str = store.DEMO_STUDENT


class GradeReq(BaseModel):
    quality: int
    student_id: str = store.DEMO_STUDENT


# ------------------------------------------------------------------ 工具
def mastery_of(sid):
    return Mastery(KB.nodes.keys(), prior=store.get_mastery(sid))


def node_public(nid, mastery):
    n = KB.nodes[nid]
    return {
        "id": nid, "name": n["name"], "grade": n["grade"],
        "chapter": n["chapter"], "summary": n["summary"],
        "mastery": round(mastery.get(nid), 2),
        "n_assertions": len(KB.assertions_of(nid)),
        "prereqs": [{"id": p, "name": KB.node_name(p), "w": w,
                     "mastery": round(mastery.get(p), 2)} for p, w in KB.graph.inn[nid]],
        "successors": [{"id": s, "name": KB.node_name(s), "w": w}
                       for s, w in KB.graph.out[nid]],
    }


def graph_payload(mastery):
    return {
        "nodes": [node_public(n, mastery) for n in KB.graph.topo_order()],
        "edges": [{"from": e["from"], "to": e["to"], "w": e["w"]} for e in KB.edges],
    }


def status_of(p):
    if p >= 0.75:
        return "mastered"
    if p >= 0.45:
        return "fuzzy"
    if p > 0.12:
        return "weak"
    return "empty"


def streak_of(sid):
    days = {s["started_at"][:10] for s in store.recent_sessions(sid, 400)}
    if not days:
        return 0
    cur = datetime.now().date()
    if cur.isoformat() not in days:      # 今天还没讲，从昨天起算也不算断
        cur -= timedelta(days=1)
    n = 0
    while cur.isoformat() in days:
        n += 1
        cur -= timedelta(days=1)
    return n


# ------------------------------------------------------------------ 页面
@app.get("/")
def index():
    return FileResponse(os.path.join(WEB, "index.html"))


# ------------------------------------------------------------------ API
@app.get("/api/bootstrap")
def bootstrap(student_id: str = store.DEMO_STUDENT):
    m = mastery_of(student_id)
    stu = store.get_student(student_id) or {}
    cards = store.list_cards(student_id)
    due = [c for c in cards if (c["due_at"] or "")[:10] <= datetime.now().strftime("%Y-%m-%d")]
    recent = store.recent_sessions(student_id, 6)

    # 今日推荐：已接触过、掌握度最低、且前驱至少学过一个
    cand = []
    for nid in KB.nodes:
        p = m.get(nid)
        if p <= 0.12:
            continue
        if any(m.get(u) > 0.12 for u in KB.graph.prereqs(nid)) or not KB.graph.prereqs(nid):
            cand.append((p, nid))
    cand.sort()
    pick = cand[0][1] if cand else "archimedes"

    week_start = datetime.now() - timedelta(days=7)
    week = [s for s in store.recent_sessions(student_id, 50)
            if datetime.fromisoformat(s["started_at"]) >= week_start]

    return {
        "student": stu,
        "today": datetime.now().strftime("%Y-%m-%d"),
        "pick": node_public(pick, m),
        "stats": {
            "streak": streak_of(student_id),
            "week_sessions": len(week),
            "due_cards": len(due),
            "total_sessions": len(store.recent_sessions(student_id, 400)),
        },
        "due_cards": [{"card_id": c["id"], "node_id": c["node_id"],
                       "name": KB.node_name(c["node_id"]),
                       "grade": KB.nodes[c["node_id"]]["grade"],
                       "due": c["due_at"][:10], "interval": c["interval"]}
                      for c in cards[:6]],
        "recent": [{"id": s["id"], "node": KB.node_name(s["node_id"]),
                    "date": s["ended_at"][:10], "total": s["total"]} for s in recent],
        "weak_chain": weak_chain(m),
    }


def weak_chain(m):
    """首页右上角的薄弱链路：从「学过但没学透」的节点往上追两层前驱。"""
    low = sorted([(m.get(n), n) for n in KB.nodes], key=lambda x: x[0])
    for p, nid in low:
        if p > 0.65 or p <= 0.15:     # 未接触过的节点不作为链路起点
            continue
        chain = [nid]
        cur = nid
        for _ in range(2):
            pre = [(m.get(u), u) for u in KB.graph.prereqs(cur)]
            if not pre:
                break
            pre.sort()
            if pre[0][0] > 0.8:
                break
            cur = pre[0][1]
            chain.append(cur)
        if len(chain) >= 2:
            chain = list(reversed(chain))
            return [{"id": x, "name": KB.node_name(x),
                     "mastery": round(m.get(x), 2),
                     "status": status_of(m.get(x))} for x in chain]
    return []


@app.get("/api/graph")
def graph(student_id: str = store.DEMO_STUDENT):
    m = mastery_of(student_id)
    data = graph_payload(m)
    for n in data["nodes"]:
        n["status"] = status_of(n["mastery"])
    return data


@app.get("/api/node/{nid}")
def node(nid: str, student_id: str = store.DEMO_STUDENT):
    if nid not in KB.nodes:
        raise HTTPException(404, "no such node")
    m = mastery_of(student_id)
    d = node_public(nid, m)
    d["status"] = status_of(d["mastery"])
    d["assertions"] = [{"id": a["id"], "text": a["text"], "w": a["w"]}
                       for a in KB.assertions_of(nid)]
    d["misconceptions"] = [{"id": x["id"], "title": x["title"]} for x in KB.mis_by_node.get(nid, [])]
    d["example"] = diagnose.NODE_EXAMPLE.get(nid, "")
    return d


@app.get("/api/samples")
def samples():
    import json
    p = os.path.join(HERE, "data", "samples.json")
    data = json.load(open(p, encoding="utf-8"))["samples"]
    return [{"id": s["id"], "node": s["node"], "title": s["title"],
             "brief": s["brief"], "text": s["text"]} for s in data]


@app.post("/api/session/start")
def session_start(req: StartReq):
    if req.node_id not in KB.nodes:
        raise HTTPException(404, "no such node")
    sid = store.create_session(req.student_id, req.node_id)
    SESSIONS[sid] = {"node": req.node_id, "started": datetime.now(),
                     "asked": [], "utter": 0}
    m = mastery_of(req.student_id)
    return {
        "session_id": sid,
        "node": node_public(req.node_id, m),
        "assertion_count": len(KB.assertions_of(req.node_id)),
        "hint": diagnose.NODE_EXAMPLE.get(req.node_id, ""),
    }


def _live(sid, text, student_id, want_probe=True):
    st = SESSIONS.get(sid)
    if not st:
        raise HTTPException(404, "session not found")
    st["utter"] += 1
    m = mastery_of(student_id)
    r = diagnose.analyze(KB, text, st["node"], m, asked_ids=st["asked"])
    hint = None
    if want_probe and r["probes"] and st["utter"] % 2 == 1:
        p = r["probes"][0]
        if p["id"] not in st["asked"]:
            st["asked"].append(p["id"])
            store.add_asked(sid, p["id"])
            hint = p
    return r, hint


@app.post("/api/session/utter")
def session_utter(req: UtterReq):
    r, hint = _live(req.session_id, req.text, req.student_id)
    cov = r["coverage"]
    return {
        "coverage": r["scores"]["coverage"],
        "covered": len(cov["covered"]),
        "partial": len(cov["partial"]),
        "total": len(cov["covered"]) + len(cov["partial"]) + len(cov["missed"]),
        "misconceptions": r["misconceptions"],
        "probe": hint,
    }


@app.post("/api/session/finish")
def session_finish(req: FinishReq):
    st = SESSIONS.get(req.session_id)
    if not st:
        raise HTTPException(404, "session not found")
    m = mastery_of(req.student_id)
    r = diagnose.analyze(KB, req.text, st["node"], m, asked_ids=st["asked"])

    # 更新掌握度：按本次覆盖率做一次贝叶斯更新
    q = max(0.0, min(1.0, r["coverage"]["rate"] - 0.15 * len(r["misconceptions"])))
    new_p = m.observe(st["node"], q)
    store.set_mastery(req.student_id, st["node"], new_p)
    for rc in r["root_causes"]:
        if rc["mastery"] < 0.6:
            store.set_mastery(req.student_id, rc["node"],
                              max(0.05, rc["mastery"] - 0.02))

    # 复述卡：按综合分定复习等级
    card, interval = srs.schedule({}, r["grade"])
    due = (datetime.now() + timedelta(days=interval)).strftime("%Y-%m-%d")
    cur = {c["node_id"]: c for c in store.list_cards(req.student_id)}.get(st["node"])
    if cur:
        card, interval = srs.schedule({"stability": cur["stability"],
                                       "difficulty": cur["difficulty"]}, r["grade"], 0)
        due = (datetime.now() + timedelta(days=interval)).strftime("%Y-%m-%d")
    store.upsert_card(req.student_id, st["node"], card["stability"], card["difficulty"],
                      interval, due, reps=1, lapses=cur["lapses"] if cur else 0)

    r["mastery_after"] = round(new_p, 2)
    r["next_due"] = due
    r["interval"] = interval
    store.finish_session(req.session_id, req.text, r)
    SESSIONS.pop(req.session_id, None)
    return r


@app.get("/api/session/{sid}")
def session_get(sid: str):
    s = store.get_session(sid)
    if not s:
        raise HTTPException(404, "session not found")
    return s


@app.get("/api/review")
def review(student_id: str = store.DEMO_STUDENT):
    cards = store.list_cards(student_id)
    today = datetime.now().strftime("%Y-%m-%d")
    out = []
    for c in cards:
        d = (c["due_at"] or "")[:10]
        try:
            overdue = (datetime.strptime(today, "%Y-%m-%d") - datetime.strptime(d, "%Y-%m-%d")).days
        except Exception:
            overdue = 0
        out.append({
            "card_id": c["id"], "node_id": c["node_id"],
            "name": KB.node_name(c["node_id"]),
            "grade": KB.nodes[c["node_id"]]["grade"],
            "due": d, "overdue": max(0, overdue), "interval": c["interval"],
            "example": diagnose.NODE_EXAMPLE.get(c["node_id"], ""),
        })
    out.sort(key=lambda x: x["due"])
    return {"today": today, "cards": out}


@app.post("/api/review/{card_id}/grade")
def review_grade(card_id: str, req: GradeReq):
    con = store.connect()
    row = con.execute("SELECT * FROM cards WHERE id=?", (card_id,)).fetchone()
    con.close()
    if not row:
        raise HTTPException(404, "card not found")
    c = dict(row)
    card, interval = srs.schedule({"stability": c["stability"],
                                   "difficulty": c["difficulty"]},
                                  max(1, min(4, req.quality)), c["interval"])
    due = (datetime.now() + timedelta(days=interval)).strftime("%Y-%m-%d")
    store.upsert_card(c["student_id"], c["node_id"], card["stability"],
                      card["difficulty"], interval, due,
                      reps=1, lapses=c["lapses"])
    return {"ok": True, "interval": interval, "due": due}


@app.get("/api/growth")
def growth(student_id: str = store.DEMO_STUDENT):
    recent = store.recent_sessions(student_id, 12)
    recent = list(reversed(recent))
    sessions = store.recent_sessions(student_id, 400)
    m = store.get_mastery(student_id)
    dist = {"mastered": 0, "fuzzy": 0, "weak": 0, "empty": 0}
    for nid in KB.nodes:
        dist[status_of(m.get(nid))] += 1

    # 能力标签：按维度平均分
    dims = {"coverage": [], "accuracy": [], "logic": [], "examples": []}
    for s in sessions:
        rep = s.get("report") or {}
        sc = rep.get("scores") or {}
        for k in dims:
            if isinstance(sc.get(k), int):
                dims[k].append(sc[k])
    avg = {k: (sum(v) / len(v) if v else None) for k, v in dims.items()}
    tags = []
    if avg["coverage"] and avg["coverage"] >= 70:
        tags.append({"text": "讲得全", "kind": "good"})
    if avg["accuracy"] and avg["accuracy"] >= 80:
        tags.append({"text": "表述准确", "kind": "good"})
    if avg["examples"] is not None and avg["examples"] < 60:
        tags.append({"text": "缺少例子", "kind": "warn"})
    if avg["logic"] and avg["logic"] < 65:
        tags.append({"text": "因果链偏弱", "kind": "bad"})
    if not tags:
        tags.append({"text": "刚开始建立画像", "kind": "warn"})

    return {
        "trend": [{"date": s["ended_at"][:10], "total": s["total"],
                   "node": KB.node_name(s["node_id"])} for s in recent],
        "recent": [{"id": s["id"], "node_id": s["node_id"],
                    "node": KB.node_name(s["node_id"]),
                    "date": s["ended_at"], "total": s["total"]} for s in reversed(recent)],
        "distribution": dist,
        "tags": tags,
        "total_sessions": len(sessions),
        "avg": {k: (round(v) if v else None) for k, v in avg.items()},
    }


@app.post("/api/demo/reset")
def demo_reset():
    store.reset()
    store.seed_demo(KB)
    SESSIONS.clear()
    return {"ok": True}


@app.get("/api/health")
def health():
    return {"ok": True, "nodes": len(KB.nodes), "assertions": len(KB.assertions_by_id),
            "misconceptions": len(KB.misconceptions), "probes": len(KB.probes)}


app.mount("/", StaticFiles(directory=WEB, html=True), name="web")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("ECHO_PORT", "8771"))
    print("\n  回声 Echo  ->  http://127.0.0.1:%d\n" % port)
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
