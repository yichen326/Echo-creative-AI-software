# -*- coding: utf-8 -*-
"""知识库校验：结构完整性、引用一致性、统计信息。"""
import json, sys, os

P = os.path.join(os.path.dirname(__file__), "curriculum.json")
kb = json.load(open(P, encoding="utf-8"))

nodes = {n["id"]: n for n in kb["nodes"]}
errors = []

# 1. 边端点
for e in kb["edges"]:
    if e["from"] not in nodes:
        errors.append("边起点不存在: " + e["from"])
    if e["to"] not in nodes:
        errors.append("边终点不存在: " + e["to"])

# 2. 每个节点都要有断言
for nid in nodes:
    if nid not in kb["assertions"] or not kb["assertions"][nid]:
        errors.append("节点缺少断言: " + nid)

# 3. 断言 id 唯一
seen = set()
for nid, arr in kb["assertions"].items():
    if nid not in nodes:
        errors.append("断言挂在未知节点: " + nid)
    for a in arr:
        if a["id"] in seen:
            errors.append("断言 id 重复: " + a["id"])
        seen.add(a["id"])
        if not a.get("keys"):
            errors.append("断言缺少关键词: " + a["id"])

# 4. 探针 binds 必须存在
for p in kb["probes"]:
    for b in p["binds"]:
        if b not in seen:
            errors.append("探针 %s 绑定了不存在的断言 %s" % (p["id"], b))
    if p["node"] not in nodes:
        errors.append("探针挂在未知节点: " + p["id"])

# 5. 迷思节点存在
for m in kb["misconceptions"]:
    if m["node"] not in nodes:
        errors.append("迷思挂在未知节点: " + m["id"])

# 6. 环检测（必须是有向无环图）
adj = {n: [] for n in nodes}
for e in kb["edges"]:
    adj[e["from"]].append(e["to"])
color = {}


def dfs(u):
    color[u] = 1
    for v in adj[u]:
        if color.get(v) == 1:
            errors.append("检测到环: %s -> %s" % (u, v))
        elif color.get(v) is None:
            dfs(v)
    color[u] = 2


for n in nodes:
    if n not in color:
        dfs(n)

# 7. 可达性：每个节点都应能追溯到至少一个无前驱节点
indeg = {n: 0 for n in nodes}
for e in kb["edges"]:
    indeg[e["to"]] += 1
roots = [n for n, d in indeg.items() if d == 0]

n_assert = sum(len(v) for v in kb["assertions"].values())
print("节点:", len(nodes), "| 边:", len(kb["edges"]), "| 断言:", n_assert)
print("迷思:", len(kb["misconceptions"]), "| 探针:", len(kb["probes"]))
print("根节点:", [nodes[r]["name"] for r in roots])
print("平均断言/节点: %.1f" % (n_assert / len(nodes)))

if errors:
    print("\n发现问题:")
    for e in errors:
        print("  -", e)
    sys.exit(1)
print("\n校验通过")
