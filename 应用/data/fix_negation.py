# -*- coding: utf-8 -*-
"""修补：某些迷思的触发词是「就是 / 等于」，学生说「**不是**总体积」时会误判。

给这几条加上否定词作为排除项。
"""
import json
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "curriculum.json")
kb = json.load(open(P, encoding="utf-8"))

NEG = ["不是", "而不是", "并不是", "不等于", "并非"]
targets = {"M-18", "M-19", "M-05", "M-03"}
n = 0
for m in kb["misconceptions"]:
    if m["id"] in targets:
        for w in NEG:
            if w not in m["blocks"]:
                m["blocks"].append(w)
                n += 1
        print(m["id"], "blocks ->", "、".join(m["blocks"]))

json.dump(kb, open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("新增排除词", n, "条")
