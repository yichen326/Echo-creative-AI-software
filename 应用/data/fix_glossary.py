# -*- coding: utf-8 -*-
"""补一份术语表：朗读过程中学生随时会问「X 是什么意思」，答案必须短、准、能读出来。"""
import json
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "curriculum.json")
kb = json.load(open(P, encoding="utf-8"))

GLOSSARY = [
    {"term": "浮力", "alias": ["浮力是"], "node": "buoyancy_concept",
     "def": "浮力是液体或气体对浸在里面的物体向上的托力，方向竖直向上。它不是重力，也不是重力的反作用力。"},
    {"term": "排开", "alias": ["排开的液体", "排开水"], "node": "archimedes",
     "def": "排开，指的是物体浸进液体以后，被它挤走的那部分液体。物体浸进去多少体积，就挤走多少液体，所以排开液体的体积就等于物体浸入部分的体积。"},
    {"term": "V排", "alias": ["v排", "排开体积", "排开液体的体积"], "node": "archimedes",
     "def": "V排 是排开液体的体积，也就是物体浸在液体里的那部分体积。完全浸没时它等于物体的体积；漂浮时它小于物体的体积。"},
    {"term": "G排", "alias": ["g排", "排开液体的重力"], "node": "archimedes",
     "def": "G排 是排开的那部分液体受到的重力，等于排开液体的质量乘 g。阿基米德原理说的就是浮力等于 G排。"},
    {"term": "密度", "alias": ["物质的密度"], "node": "mass_density",
     "def": "密度是单位体积某种物质的质量，公式是 ρ=m/V。它是物质的一种特性，同种物质密度一般不变，跟物体大小无关。"},
    {"term": "重力", "alias": ["物重"], "node": "force_balance",
     "def": "重力是物体由于地球吸引而受到的力，大小 G=mg，方向竖直向下。"},
    {"term": "质量", "alias": [], "node": "mass_density",
     "def": "质量是物体所含物质的多少，用 m 表示，单位是千克。它不随位置、形状、状态改变。"},
    {"term": "压强", "alias": [], "node": "solid_pressure",
     "def": "压强是物体单位面积上受到的压力，p=F/S。它描述的是压力的作用效果，压力越大、受力面积越小，压强越大。"},
    {"term": "深度", "alias": ["h是", "液面到"], "node": "liquid_pressure",
     "def": "深度 h 是从液面竖直往下量到某一点的距离，不是容器的高度。容器没装满时，h 要比容器高度小。"},
    {"term": "浸没", "alias": ["完全浸入", "全部浸入"], "node": "archimedes",
     "def": "浸没就是物体完全进入液体里，此时排开液体的体积等于物体自身的体积。"},
    {"term": "浸入", "alias": ["浸在"], "node": "buoyancy_concept",
     "def": "浸入指物体进入液体，可以是全部进去，也可以只进去一部分。只进去一部分时，排开的体积只算浸进去的那部分。"},
    {"term": "漂浮", "alias": ["浮在水面"], "node": "float_sink",
     "def": "漂浮是物体静止在液面上、有一部分露出液面的状态。此时物体处于平衡，浮力等于重力，排开液体的体积小于物体体积。"},
    {"term": "悬浮", "alias": ["停在水中"], "node": "float_sink",
     "def": "悬浮是物体全部浸在液体里、可以停在任意深度的状态。此时浮力等于重力，排开液体的体积等于物体体积。"},
    {"term": "上浮", "alias": ["浮起来"], "node": "float_sink",
     "def": "上浮是物体受到的浮力大于重力，于是往上升。上浮的最终结果是漂浮在液面上，那之后浮力就等于重力了。"},
    {"term": "下沉", "alias": ["沉底", "沉下去"], "node": "float_sink",
     "def": "下沉是浮力小于重力，物体往下沉。沉到底部以后，如果底部托着它，浮力仍然存在，只是比重力小。"},
    {"term": "二力平衡", "alias": ["平衡力"], "node": "force_balance",
     "def": "二力平衡要同时满足四条：作用在同一物体上、大小相等、方向相反、作用在同一直线上。缺一条就不平衡。"},
    {"term": "弹簧测力计", "alias": ["测力计"], "node": "spring_scale",
     "def": "弹簧测力计利用「弹性限度内弹簧伸长量与拉力成正比」来测力。用之前要校零，读数时视线要正对刻度。"},
    {"term": "称重法", "alias": [], "node": "buoyancy_calc",
     "def": "称重法测浮力：先用测力计在空气里称出物体重力 G，再把物体浸入液体读出此时示数 F示，两个数相减就是浮力。"},
    {"term": "大气压", "alias": ["大气压强"], "node": "atmo_pressure",
     "def": "大气压是大气对浸在其中的物体产生的压强，海平面附近约 1.013×10⁵ 帕，相当于 760 毫米水银柱。"},
    {"term": "受力面积", "alias": ["接触面积"], "node": "solid_pressure",
     "def": "受力面积是两个物体实际接触的那一部分面积，不是物体的总面积。算压强时用的是接触面积。"},
    {"term": "阿基米德原理", "alias": [], "node": "archimedes",
     "def": "阿基米德原理说：浸在液体中的物体受到向上的浮力，浮力的大小等于它排开的液体所受的重力，也就是 F浮 = G排 = ρ液 g V排。"},
    {"term": "压力", "alias": [], "node": "solid_pressure",
     "def": "压力是垂直作用在物体表面上的力。它不一定等于重力，只有放在水平面上、又没有别的竖直方向的力时，压力大小才等于重力。"},
]

kb["glossary"] = GLOSSARY
json.dump(kb, open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("术语表", len(GLOSSARY), "条，平均", round(sum(len(g["def"]) for g in GLOSSARY) / len(GLOSSARY)), "字")
