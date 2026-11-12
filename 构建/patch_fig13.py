# -*- coding: utf-8 -*-
"""图 13 重拍后：正文数字与图对齐（0.47 -> 0.55），并补一句「追问回顾」。"""
import json
import os

P = os.path.join(r"E:\人工智能作业\大作业", "构建", "content.json")
items = json.load(open(P, encoding="utf-8"))

n_num = 0
for it in items:
    if it["k"] == "p" and "0.47" in it["v"]:
        it["v"] = it["v"].replace("0.47", "0.55")
        n_num += 1

# 图 13 的配文：补一句追问回顾
n_cap = 0
for it in items:
    if it["k"] == "p" and "原话摘录" in it["v"] and "追问" not in it["v"]:
        it["v"] = it["v"].rstrip() + "最下方是追问回顾：小回问的那一句、学生怎么答的、判定结果，逐轮留痕。"
        n_cap += 1

json.dump(items, open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("改数字 %d 处，改配文 %d 处" % (n_num, n_cap))
