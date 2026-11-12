# -*- coding: utf-8 -*-
"""为每个知识点补一个不超过 4 字的短名，供知识地图的圆圈内显示。"""
import json
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "curriculum.json")
kb = json.load(open(P, encoding="utf-8"))

SHORT = {
    "mass_density": "密度",
    "density_measure": "排水法",
    "solid_pressure": "固体压强",
    "liquid_pressure": "液体压强",
    "atmo_pressure": "大气压强",
    "force_balance": "二力平衡",
    "force_synthesis": "力的合成",
    "spring_scale": "测力计",
    "buoyancy_concept": "浮力产生",
    "archimedes": "阿基米德",
    "float_sink": "浮沉条件",
    "buoyancy_calc": "浮力计算",
}
for n in kb["nodes"]:
    n["short"] = SHORT.get(n["id"], n["name"][:4])
json.dump(kb, open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("已补充短名：", ", ".join(n["short"] for n in kb["nodes"]))
for n in kb["nodes"]:
    if len(n["short"]) > 4:
        print("  警告：短名超过 4 字", n["id"])
