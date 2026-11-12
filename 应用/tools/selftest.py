# -*- coding: utf-8 -*-
"""引擎自检：对样例讲解跑完整诊断，打印可读结果。

用法： python tools/selftest.py [sample_id]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "vendor"))
sys.path.insert(0, ROOT)

import engine  # noqa: E402
from engine import diagnose  # noqa: E402
from engine.bkt import Mastery  # noqa: E402
from engine.kb import KnowledgeBase  # noqa: E402

# 演示学生「林一」的冷启动画像：八年级的两个概念本来就模糊
PRIOR = {
    "mass_density": 0.86,
    "density_measure": 0.55,
    "solid_pressure": 0.72,
    "liquid_pressure": 0.79,
    "atmo_pressure": 0.60,
    "force_balance": 0.61,
    "force_synthesis": 0.66,
    "spring_scale": 0.82,
    "buoyancy_concept": 0.58,
    "archimedes": 0.34,
    "float_sink": 0.08,
    "buoyancy_calc": 0.05,
}


def main():
    kb = KnowledgeBase()
    samples = json.load(open(os.path.join(ROOT, "data", "samples.json"), encoding="utf-8"))["samples"]
    sid = sys.argv[1] if len(sys.argv) > 1 else "arch_bad"
    s = next((x for x in samples if x["id"] == sid), samples[0])

    m = Mastery(kb.nodes.keys(), prior=PRIOR)
    r = diagnose.analyze(kb, s["text"], s["node"], m)

    print("=" * 62)
    print("样例:", s["title"], "|", s["brief"])
    print("知识点:", r["node_name"], "| 句子数:", len(r["sentences"]))
    print("-" * 62)
    sc = r["scores"]
    print("六维:  覆盖 %d | 准确 %d | 逻辑 %d | 术语 %d | 举例 %d | 流畅 %d"
          % (sc["coverage"], sc["accuracy"], sc["logic"], sc["terms"], sc["examples"], sc["fluency"]))
    print("综合:", sc["total"], "| 复习等级:", r["grade"])
    print("-" * 62)
    print("覆盖率: %.0f%%" % (r["coverage"]["rate"] * 100))
    for k, label in (("covered", "讲到位"), ("partial", "一带而过"), ("missed", "没提到")):
        items = r["coverage"][k]
        print("  [%s %d]" % (label, len(items)))
        for it in items:
            print("     %-6s w=%.1f %s" % (it["id"], it["w"], it["text"]))
    print("-" * 62)
    if r["misconceptions"]:
        print("迷思命中:")
        for msc in r["misconceptions"]:
            print("  [%s] %s（%s）" % (msc["id"], msc["title"], msc["type"]))
            print("     原话: %s" % msc["sentence"])
            print("     纠正: %s" % msc["correction"])
    else:
        print("迷思命中: 无")
    print("-" * 62)
    print("根因链:")
    for rc in r["root_causes"]:
        print("  %-10s 得分 %.2f  掌握度 %.2f  %s" % (rc["name"], rc["score"], rc["mastery"], " > ".join(rc["path"])))
    print("-" * 62)
    print("追问:")
    for p in r["probes"]:
        print("  %s  %s" % (p["id"], p["text"]))
    print("-" * 62)
    print("建议:")
    for i, s2 in enumerate(r["suggestions"], 1):
        print("  %d. %s" % (i, s2))
    print("明天讲这一句:", r["tomorrow"])
    print("=" * 62)


if __name__ == "__main__":
    main()
