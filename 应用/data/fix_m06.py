# -*- coding: utf-8 -*-
"""一次性数据修补：放宽 M-06 的第二组触发词（「压强应该越大」这类说法）。"""
import json
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "curriculum.json")
kb = json.load(open(P, encoding="utf-8"))
for m in kb["misconceptions"]:
    if m["id"] == "M-06":
        m["triggers"] = [["液体越重", "液体越多", "装的液体越多", "水越多", "液体多"],
                         ["压强越大", "压强应该越大", "压强也大", "压强大", "越大"]]
        # 第一组已经限定了语境，第二组可以放宽
json.dump(kb, open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("M-06 已放宽")
