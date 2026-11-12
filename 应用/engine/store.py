# -*- coding: utf-8 -*-
"""SQLite 存储层：学生、掌握度、讲解会话、复述卡。"""
import json
import os
import sqlite3
import uuid
from datetime import datetime, timedelta

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DB_PATH = os.path.join(DB_DIR, "echo.db")

DEMO_STUDENT = "linyi"
DEMO_PRIOR = {
    "mass_density": 0.86, "density_measure": 0.55, "solid_pressure": 0.72,
    "liquid_pressure": 0.79, "atmo_pressure": 0.60, "force_balance": 0.61,
    "force_synthesis": 0.66, "spring_scale": 0.82, "buoyancy_concept": 0.58,
    "archimedes": 0.34, "float_sink": 0.08, "buoyancy_calc": 0.05,
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS students(
  id TEXT PRIMARY KEY, name TEXT, cls TEXT, created_at TEXT);
CREATE TABLE IF NOT EXISTS mastery(
  student_id TEXT, node_id TEXT, p REAL, updated_at TEXT,
  PRIMARY KEY(student_id, node_id));
CREATE TABLE IF NOT EXISTS sessions(
  id TEXT PRIMARY KEY, student_id TEXT, node_id TEXT,
  started_at TEXT, ended_at TEXT, transcript TEXT, report TEXT, total INTEGER);
CREATE TABLE IF NOT EXISTS cards(
  id TEXT PRIMARY KEY, student_id TEXT, node_id TEXT,
  stability REAL, difficulty REAL, interval INTEGER,
  due_at TEXT, last_review TEXT, reps INTEGER, lapses INTEGER);
CREATE TABLE IF NOT EXISTS probes_asked(
  session_id TEXT, probe_id TEXT, ts TEXT);
"""


def now():
    return datetime.now().replace(microsecond=0)


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def connect():
    os.makedirs(DB_DIR, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init():
    con = connect()
    con.executescript(SCHEMA)
    con.commit()
    con.close()


def reset():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init()


# ---------------------------------------------------------------- 学生
def ensure_student(sid=DEMO_STUDENT, name="林一", cls="初二（3）班"):
    con = connect()
    row = con.execute("SELECT * FROM students WHERE id=?", (sid,)).fetchone()
    if not row:
        con.execute("INSERT INTO students VALUES(?,?,?,?)", (sid, name, cls, iso(now())))
        for nid, p in DEMO_PRIOR.items():
            con.execute("INSERT INTO mastery VALUES(?,?,?,?)", (sid, nid, p, iso(now())))
        con.commit()
    con.close()


def get_student(sid=DEMO_STUDENT):
    con = connect()
    r = con.execute("SELECT * FROM students WHERE id=?", (sid,)).fetchone()
    con.close()
    return dict(r) if r else None


def get_mastery(sid=DEMO_STUDENT):
    con = connect()
    rows = con.execute("SELECT node_id,p FROM mastery WHERE student_id=?", (sid,)).fetchall()
    con.close()
    return {r["node_id"]: r["p"] for r in rows}


def set_mastery(sid, node_id, p):
    con = connect()
    con.execute("INSERT INTO mastery VALUES(?,?,?,?) ON CONFLICT(student_id,node_id) "
                "DO UPDATE SET p=excluded.p, updated_at=excluded.updated_at",
                (sid, node_id, p, iso(now())))
    con.commit()
    con.close()


# ---------------------------------------------------------------- 会话
def create_session(sid, node_id):
    con = connect()
    s = uuid.uuid4().hex[:12]
    con.execute("INSERT INTO sessions(id,student_id,node_id,started_at,total) VALUES(?,?,?,?,0)",
                (s, sid, node_id, iso(now())))
    con.commit()
    con.close()
    return s


def finish_session(session_id, transcript, report):
    con = connect()
    con.execute("UPDATE sessions SET ended_at=?, transcript=?, report=?, total=? WHERE id=?",
                (iso(now()), transcript, json.dumps(report, ensure_ascii=False),
                 report.get("scores", {}).get("total", 0), session_id))
    con.commit()
    con.close()


def get_session(session_id):
    con = connect()
    r = con.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
    con.close()
    if not r:
        return None
    d = dict(r)
    if d.get("report"):
        d["report"] = json.loads(d["report"])
    return d


def recent_sessions(sid=DEMO_STUDENT, limit=8):
    con = connect()
    rows = con.execute(
        "SELECT s.*, COALESCE(NULLIF(s.total,0),0) AS total FROM sessions s "
        "WHERE s.student_id=? AND s.ended_at IS NOT NULL ORDER BY s.ended_at DESC LIMIT ?",
        (sid, limit)).fetchall()
    con.close()
    out = []
    for r in rows:
        d = dict(r)
        d["report"] = json.loads(d["report"]) if d["report"] else None
        out.append(d)
    return out


# ---------------------------------------------------------------- 复述卡
def upsert_card(sid, node_id, stability, difficulty, interval, due_at, reps=1, lapses=0):
    con = connect()
    r = con.execute("SELECT * FROM cards WHERE student_id=? AND node_id=?", (sid, node_id)).fetchone()
    if r:
        con.execute("UPDATE cards SET stability=?,difficulty=?,interval=?,due_at=?,last_review=?,reps=?,lapses=? WHERE id=?",
                    (stability, difficulty, interval, due_at, iso(now()),
                     r["reps"] + 1, lapses, r["id"]))
        cid = r["id"]
    else:
        cid = uuid.uuid4().hex[:12]
        con.execute("INSERT INTO cards VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (cid, sid, node_id, stability, difficulty, interval, due_at, iso(now()), reps, lapses))
    con.commit()
    con.close()
    return cid


def list_cards(sid=DEMO_STUDENT):
    con = connect()
    rows = con.execute("SELECT * FROM cards WHERE student_id=? ORDER BY due_at", (sid,)).fetchall()
    con.close()
    return [dict(r) for r in rows]


def due_cards(sid=DEMO_STUDENT):
    today = iso(now())[:10]
    return [c for c in list_cards(sid) if (c["due_at"] or "")[:10] <= today]


# ---------------------------------------------------------------- 演示数据
def seed_demo(kb):
    """为演示学生造一段历史：让成长曲线与复述队列看起来是「用过的」。"""
    ensure_student()
    con = connect()
    n = con.execute("SELECT COUNT(*) c FROM sessions WHERE student_id=?", (DEMO_STUDENT,)).fetchone()["c"]
    con.close()
    if n > 0:
        return

    history = [
        (-9, "mass_density", 58), (-7, "density_measure", 61), (-5, "liquid_pressure", 55),
        (-4, "force_balance", 67), (-3, "spring_scale", 64), (-2, "buoyancy_concept", 69),
        (-1, "archimedes", 62),
    ]
    con = connect()
    for days, nid, total in history:
        d = now() + timedelta(days=days)
        con.execute("INSERT INTO sessions(id,student_id,node_id,started_at,ended_at,transcript,report,total) "
                    "VALUES(?,?,?,?,?,?,?,?)",
                    (uuid.uuid4().hex[:12], DEMO_STUDENT, nid, iso(d), iso(d + timedelta(minutes=3)),
                     "", json.dumps({"scores": {"total": total}}, ensure_ascii=False), total))
    con.commit()
    con.close()

    # 复述卡：两张今天到期，其余分散在未来
    plan = [("archimedes", -3, 0), ("liquid_pressure", 0, 0), ("density_measure", 1, 0),
            ("force_balance", 3, 0), ("spring_scale", 7, 0), ("mass_density", 12, 0),
            ("buoyancy_concept", 2, 0)]
    for nid, offset, lapses in plan:
        due = iso(now() + timedelta(days=offset))[:10]
        upsert_card(DEMO_STUDENT, nid, 3.2, 5.0, max(1, offset), due, reps=1, lapses=lapses)


def add_asked(session_id, probe_id):
    con = connect()
    con.execute("INSERT INTO probes_asked VALUES(?,?,?)", (session_id, probe_id, iso(now())))
    con.commit()
    con.close()


def asked_of(session_id):
    con = connect()
    rows = con.execute("SELECT probe_id FROM probes_asked WHERE session_id=?", (session_id,)).fetchall()
    con.close()
    return [r["probe_id"] for r in rows]
