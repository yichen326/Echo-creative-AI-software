# -*- coding: utf-8 -*-
"""诊断主流程：切分 → 覆盖 → 迷思 → 六维评分 → 根因溯源 → 追问。"""
import math

from . import matcher, probe as probe_mod, srs
from .segment import words, overlap
from .text import (connective_density, example_density, filler_ratio,
                   key_hit, norm_key, split_sentences)

GAMMA = 0.75          # 路径衰减因子
ROOT_MIN = 0.10       # 根因得分下限
LEVEL_P = {"covered": 0.85, "partial": 0.50, "missed": 0.30}

# 每个知识点配一个具体例子，用于「缺少举例」时的建议
NODE_EXAMPLE = {
    "mass_density": "同一块铁切成两半，质量减半，密度不变",
    "density_measure": "一块不规则的小石块，怎么用量筒测出它的体积",
    "solid_pressure": "同样的力，用针尖和用掌心，效果完全不同",
    "liquid_pressure": "潜水员越往下潜，耳朵越疼",
    "atmo_pressure": "用吸管喝饮料，其实是大气压把饮料压上来",
    "force_balance": "推桌子没推动时，推力与静摩擦力相等",
    "force_synthesis": "两个人一个推一个拉，合力等于两力之差",
    "spring_scale": "吊着石块慢慢浸入水中，弹簧秤示数变小",
    "buoyancy_concept": "桥墩立在水里却不浮起来",
    "archimedes": "石块挂在弹簧秤下慢慢浸入水中，示数减小",
    "float_sink": "同一个鸡蛋放进清水和盐水，浮沉不同",
    "buoyancy_calc": "先用弹簧秤称出重力，再浸入水中读示数",
}

FILLERS = [
    "把这条再讲一遍，尝试不看提示，用 90 秒说完。",
    "换一种说法再讲一遍，这次先说结论再说理由。",
    "试着用一句话概括这个知识点，再把这句话展开讲。",
]


# ---------------------------------------------------------------- 迷思检测
def detect_misconceptions(kb, sentences, node_id, depth=2):
    """在本文与上游节点的迷思库中检索命中。"""
    allowed = {node_id}
    for a, d in kb.graph.ancestors(node_id, depth).items():
        allowed.add(a)
    hits = []
    seen = set()
    for s_raw, s_norm in sentences:
        for m in kb.misconceptions:
            if m["node"] not in allowed:
                continue
            if any(blk and blk in s_norm for blk in m.get("blocks", [])):
                continue
            ok = True
            for group in m["triggers"]:
                if not any(norm_key(t) in s_norm for t in group):
                    ok = False
                    break
            if not ok:
                continue
            key = (m["id"], s_raw)
            if key in seen:
                continue
            seen.add(key)
            hits.append({
                "id": m["id"],
                "title": m["title"],
                "type": m["type"],
                "node": m["node"],
                "node_name": kb.node_name(m["node"]),
                "sentence": s_raw,
                "correction": m["correction"],
            })
    return hits


# ---------------------------------------------------------------- 六维评分
def score_dimensions(sentences, cov, mis, node_id, kb):
    texts = [s for s, _ in sentences]
    assertions = kb.assertions_of(node_id)

    # 覆盖
    coverage = round(cov["rate"] * 100)

    # 准确
    accuracy = max(0, 100 - 22 * len(mis))

    # 逻辑：连词密度 + 相邻句的术语承接 + 循环论证惩罚
    cd = connective_density(texts)
    chain = 0
    ws = [words(t) for t in texts]
    for i in range(len(ws) - 1):
        if overlap(ws[i], ws[i + 1]) >= 0.3:
            chain += 1
    tautology = 0
    for t in texts:
        n = norm_key(t)
        if n.count("因为") and n.count("所以"):
            a = n.split("因为")[-1].split("所以")[0]
            b = n.split("所以")[-1]
            if a and a[:6] in b:
                tautology += 1
    logic = 55 + min(20, cd * 10) + min(15, chain * 5) - 10 * tautology
    logic = int(max(0, min(100, logic)))

    # 术语：领域词汇的使用覆盖率（用了几成规范术语）
    joined = "".join(norm_key(t) for t in texts)
    vocab, used = set(), set()
    for a in assertions:
        for group in a.get("keys", []):
            std = group[0]
            vocab.add(std)
            if key_hit([group], joined) >= 0.5:
                used.add(std)
    terms = int(round(100.0 * len(used) / len(vocab))) if vocab else 50

    # 举例
    cnt, has_num = example_density(texts)
    if cnt == 0:
        examples = 15
    elif cnt == 1:
        examples = 55 if has_num else 40
    else:
        examples = 85 if has_num else 65
    examples = int(examples)

    # 流畅：平均句长与口头禅
    avg_len = sum(len(norm_key(t)) for t in texts) / max(1, len(texts))
    fluency = 92 - 8 * abs(avg_len - 20) / 10.0 - filler_ratio(texts) * 60
    if avg_len < 6:
        fluency -= 10
    fluency = int(max(0, min(100, fluency)))

    total = (0.30 * coverage + 0.25 * accuracy + 0.15 * logic
             + 0.10 * terms + 0.10 * examples + 0.10 * fluency)
    return {
        "coverage": coverage, "accuracy": accuracy, "logic": logic,
        "terms": terms, "examples": examples, "fluency": fluency,
        "total": int(round(total)),
        "meta": {"connective": round(cd, 2), "chain": chain,
                 "tautology": tautology, "avg_len": round(avg_len, 1),
                 "example_hits": cnt, "has_number": has_num},
    }


# ---------------------------------------------------------------- 根因溯源
def root_causes(kb, node_id, mastery, mis, top=3):
    anc = kb.graph.ancestors(node_id, max_depth=4)
    cand = []
    for u, depth in anc.items():
        paths = kb.graph.paths(u, node_id, max_len=5)
        if not paths:
            continue
        influence = 0.0
        best_path = None
        for path, wprod in paths:
            v = (GAMMA ** (len(path) - 1)) * wprod
            if v > influence:
                influence = v
                best_path = path
        weakness = 1.0 - mastery.get(u)
        score = weakness * influence
        # 如果在上游节点上还命中了迷思，加权
        if any(m["node"] == u for m in mis):
            score *= 1.35
        cand.append({
            "node": u,
            "name": kb.node_name(u),
            "grade": kb.nodes[u]["grade"],
            "score": round(score, 3),
            "mastery": round(mastery.get(u), 2),
            "path": [kb.node_name(x) for x in best_path] if best_path else [],
            "depth": depth,
        })
    cand.sort(key=lambda x: -x["score"])
    out = [c for c in cand if c["score"] >= ROOT_MIN][:top]
    # 保证链路连通：按得分降序，后一个必须是前一个的祖先或可达
    return out


# ---------------------------------------------------------------- 讲反了
def apply_contradictions(kb, cov, mis, assertions):
    """命中的迷思会把它对应的断言直接判为「讲反了」，不再计入覆盖。"""
    bad = set()
    for m in mis:
        for aid in kb.mis_by_id.get(m["id"], {}).get("conflicts", []):
            bad.add(aid)
        m["conflicts"] = kb.mis_by_id.get(m["id"], {}).get("conflicts", [])
    if not bad:
        return cov
    detail = cov["detail"]
    for aid in bad:
        if aid in detail:
            detail[aid]["level"] = "missed"
            detail[aid]["contradicted"] = True
    total_w = sum(a["w"] for a in assertions) or 1.0
    got = 0.0
    covered, partial, missed = [], [], []
    for a in assertions:
        info = detail[a["id"]]
        lv = info["level"]
        if lv == "covered":
            covered.append(a["id"])
            got += a["w"]
        elif lv == "partial":
            partial.append(a["id"])
            got += a["w"] * 0.5
        else:
            missed.append(a["id"])
    return {"rate": got / total_w, "covered": covered, "partial": partial,
            "missed": missed, "detail": detail}


# ---------------------------------------------------------------- 建议
def build_suggestions(kb, node_id, cov, mis, scores):
    out = []
    assertions = kb.assertions_of(node_id)
    tot_w = sum(a["w"] for a in assertions) or 1.0
    if mis:
        m = mis[0]
        out.append("你说「%s」，其实%s" % (_short(m["sentence"]), m["correction"]))
    missed = [a for a in assertions if cov["detail"][a["id"]]["level"] == "missed"]
    missed.sort(key=lambda a: -a["w"])
    if missed:
        out.append("这一段里完全没提到「%s」，它占这个知识点约 %d%% 的权重。"
                   % (missed[0]["text"].rstrip("。"), int(round(missed[0]["w"] / tot_w * 100))))
    if scores["examples"] < 55:
        ex = NODE_EXAMPLE.get(node_id, "一个你熟悉的日常现象")
        out.append("全程几乎没有例子，试着用「%s」讲一遍。" % ex)
    if scores["logic"] < 60:
        out.append("因果链是断的：说了「是什么」，没说「为什么」，补一句「因为……所以……」。")
    i = 0
    while len(out) < 3 and i < len(FILLERS):
        if FILLERS[i] not in out:
            out.append(FILLERS[i])
        i += 1
    return out[:3]


def _short(s, n=28):
    s = (s or "").strip().rstrip("。！？")
    return s if len(s) <= n else s[:n] + "……"


def tomorrow_sentence(kb, node_id, cov):
    """明天复述时只要讲清的那一句 = 权重最高且未讲透的断言。"""
    assertions = kb.assertions_of(node_id)
    cand = [a for a in assertions if cov["detail"][a["id"]]["level"] != "covered"]
    if not cand:
        cand = assertions
    cand.sort(key=lambda a: -a["w"])
    return cand[0]["text"] if cand else ""


# ---------------------------------------------------------------- 主入口
def analyze(kb, text, node_id, mastery, asked_ids=None):
    sentences = split_sentences(text)
    assertions = kb.assertions_of(node_id)
    cov = matcher.match_coverage(sentences, assertions)
    mis = detect_misconceptions(kb, sentences, node_id)
    cov = apply_contradictions(kb, cov, mis, assertions)
    scores = score_dimensions(sentences, cov, mis, node_id, kb)
    roots = root_causes(kb, node_id, mastery, mis)

    picked = probe_mod.choose(kb, node_id, cov["detail"], asked_ids=asked_ids,
                              limit=2, char_count=len(text or ""),
                              n_units=cov.get("n_units", 0))
    probes = [probe_mod.render(kb, node_id, it) for it in picked]

    by_id = {a["id"]: a for a in assertions}

    def pack(ids, level):
        out = []
        for i in ids:
            info = cov["detail"][i]
            out.append({"id": i, "text": by_id[i]["text"], "w": by_id[i]["w"],
                        "level": level,
                        "contradicted": bool(info.get("contradicted")),
                        "evidence": info.get("evidence", ""),
                        "support": info.get("support", 0)})
        return out

    return {
        "node": node_id,
        "node_name": kb.node_name(node_id),
        "sentences": [s for s, _ in sentences],
        "coverage": {
            "rate": round(cov["rate"], 3),
            "covered": pack(cov["covered"], "covered"),
            "partial": pack(cov["partial"], "partial"),
            "missed": pack(cov["missed"], "missed"),
        },
        "misconceptions": mis,
        "scores": scores,
        "root_causes": roots,
        "suggestions": build_suggestions(kb, node_id, cov, mis, scores),
        "tomorrow": tomorrow_sentence(kb, node_id, cov),
        "probes": probes,
        "grade": srs.quality_to_grade(scores["total"]),
    }
