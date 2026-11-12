# -*- coding: utf-8 -*-
"""苏格拉底追问：只对「讲到了但没讲透」的地方提问。

提问策略（v2）：
  1. 太早不问——讲不满 30 字不打扰；
  2. 只对「一带而过」的断言提问（学生自己提到了，但说不清）；
  3. 完全没提到的断言不问，改成「提醒」——告诉他漏了哪一点；
  4. 已经讲透的不问。

这样避免「学生还没讲到，就被追问一个他没接触的概念」的突兀感。
"""
import math

LEVEL_P = {"covered": 0.85, "partial": 0.50, "missed": 0.30}
MIN_CHARS = 30      # 讲不满这么多字，不追问
MIN_CHARS_HINT = 80  # 提醒要更晚一些，别一开口就挑毛病


def entropy(p):
    p = min(max(p, 1e-6), 1 - 1e-6)
    return -(p * math.log2(p) + (1 - p) * math.log2(1 - p))


def choose(kb, node_id, coverage_detail, asked_ids=None, limit=1,
           min_gain=0.30, char_count=0, n_units=0):
    """返回 [{probe, kind: ask|hint, gain, binds}]。

    追问只针对「学生刚说过的、但说得含糊」的断言：
    命中的句子必须落在最近三个匹配单元里，问起来才像顺着话头接的。
    """
    if char_count < MIN_CHARS:
        return []
    asked = set(asked_ids or [])
    recent_from = max(0, n_units - 3)
    asks, hints = [], []

    for pr in kb.probes_by_node.get(node_id, []):
        binds = [a for a in pr.get("binds", []) if a in coverage_detail]
        if not binds:
            continue
        levels = [coverage_detail[a]["level"] for a in binds]
        gain = 0.0
        for a in binds:
            info = coverage_detail[a]
            w = kb.assertions_by_id[a]["w"] if a in kb.assertions_by_id else 0.8
            g = entropy(LEVEL_P.get(info["level"], 0.3)) * w
            if info["level"] == "partial" and info.get("support", 0) >= 1:
                g *= 1.3          # 有原话支撑却说不清，最值得追问
            gain += g
        gain /= len(binds)

        item = {"probe": pr, "gain": round(gain, 3), "binds": binds}
        if pr["id"] in asked:
            item["gain"] = round(gain * 0.3, 3)

        if "partial" in levels:
            # 只有在「刚说过」的时候才追问
            fresh = any(coverage_detail[a].get("u", -1) >= recent_from for a in binds
                        if coverage_detail[a]["level"] == "partial")
            if not fresh:
                continue
            item["kind"] = "ask"
            asks.append(item)
        elif all(l == "missed" for l in levels):
            item["kind"] = "hint"
            hints.append(item)
        # 只有 covered：已经讲透，不必问

    asks.sort(key=lambda x: -x["gain"])
    hints.sort(key=lambda x: -x["gain"])
    if asks:
        return [x for x in asks if x["gain"] >= min_gain][:limit] or asks[:1]
    if char_count < MIN_CHARS_HINT:
        return []
    return [x for x in hints if x["gain"] >= min_gain][:limit]


def render(kb, node_id, item):
    """包装成界面可用的追问，并附上「标准说法」用于讲解。"""
    pr = item["probe"]
    kind = item.get("kind", "ask")
    lead = ""
    for a in item.get("binds", []):
        info = kb.assertions_by_id.get(a)
        if not info:
            continue
        if kind == "ask" and a and a in item["binds"]:
            lead = info["text"].rstrip("。")
            break
        if kind == "hint":
            lead = info["text"].rstrip("。")
            break
    return {
        "id": pr["id"],
        "text": pr["q"] if kind == "ask" else lead,
        "lead": lead,
        "kind": kind,
        "why": pr.get("why", ""),
        "binds": item["binds"],
        "gain": item["gain"],
    }
