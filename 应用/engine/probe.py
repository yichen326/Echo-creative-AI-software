# -*- coding: utf-8 -*-
"""苏格拉底追问：从探针池中按信息增益挑选。

对每条候选探针，估计它所验证的断言当前处于「不确定」的程度，
用二元熵衡量，再乘以断言权重与重复惩罚，取最大者。
"""
import math

LEVEL_P = {"covered": 0.85, "partial": 0.50, "missed": 0.30}


def entropy(p):
    p = min(max(p, 1e-6), 1 - 1e-6)
    return -(p * math.log2(p) + (1 - p) * math.log2(1 - p))


def choose(kb, node_id, coverage_detail, asked_ids=None, limit=1, min_gain=0.35):
    """返回按信息增益排序的候选探针列表。"""
    asked_ids = set(asked_ids or [])
    scored = []
    for pr in kb.probes_by_node.get(node_id, []):
        gain = 0.0
        binds = []
        for aid in pr["binds"]:
            a = kb.assertions_by_id.get(aid)
            info = coverage_detail.get(aid)
            if not a or not info:
                continue
            p = LEVEL_P.get(info["level"], 0.3)
            # 已讲透的断言信息量低；漏讲的与带过的都值得追问
            g = entropy(p) * a["w"]
            # 有原话支撑但仍判为带过的，最值得追问
            if info["level"] == "partial" and info["support"] >= 1:
                g *= 1.25
            gain += g
            binds.append(aid)
        if not binds:
            continue
        gain /= len(binds)
        if pr["id"] in asked_ids:
            gain *= 0.35
        scored.append({"probe": pr, "gain": round(gain, 3), "binds": binds})
    scored.sort(key=lambda x: -x["gain"])
    out = [s for s in scored if s["gain"] >= min_gain]
    return out[:limit]


def render(kb, node_id, item, student_sentence=None):
    """把探针包装成界面可用的追问文本。"""
    pr = item["probe"]
    q = pr["q"]
    if student_sentence:
        q = q + ""
    return {
        "id": pr["id"],
        "text": q,
        "why": pr.get("why", ""),
        "binds": item["binds"],
        "gain": item["gain"],
    }
