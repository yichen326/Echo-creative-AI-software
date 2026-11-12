# -*- coding: utf-8 -*-
"""概念覆盖：句子 × 断言 的最大权二分匹配。

相似度 = 0.6 × 关键词组命中率 + 0.4 × 字符二元组 Dice。
用匈牙利算法求全局最优指派，避免「一句话覆盖多条断言」造成的覆盖率虚高。
"""
from .text import dice, key_stats, split_units

INF = float("inf")
COVERED = 0.60     # 判为「讲到位」的阈值
PARTIAL = 0.40     # 判为「一带而过」的阈值
CAP_MISSING = 0.55  # 有要素没提到时，最多只能判「一带而过」


def _hungarian_min(a):
    """标准匈牙利算法（最小代价），返回 [(row, col)]。"""
    n = len(a)
    m = len(a[0]) if n else 0
    transposed = False
    if n > m:
        a = [list(r) for r in zip(*a)]
        n, m = m, n
        transposed = True
    u = [0.0] * (n + 1)
    v = [0.0] * (m + 1)
    p = [0] * (m + 1)
    way = [0] * (m + 1)
    for i in range(1, n + 1):
        p[0] = i
        j0 = 0
        minv = [INF] * (m + 1)
        used = [False] * (m + 1)
        while True:
            used[j0] = True
            i0 = p[j0]
            delta = INF
            j1 = 0
            for j in range(1, m + 1):
                if not used[j]:
                    cur = a[i0 - 1][j - 1] - u[i0] - v[j]
                    if cur < minv[j]:
                        minv[j] = cur
                        way[j] = j0
                    if minv[j] < delta:
                        delta = minv[j]
                        j1 = j
            for j in range(m + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while True:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
            if j0 == 0:
                break
    res = []
    for j in range(1, m + 1):
        if p[j] != 0:
            res.append((p[j] - 1, j - 1))
    if transposed:
        res = [(c, r) for (r, c) in res]
    return res


def pair_score(sentence, assertion):
    """句子与断言的匹配分。关键要素（关键词组）缺一不可判「讲到位」。"""
    k, missing = key_stats(assertion.get("keys", []), sentence)
    d = dice(sentence, assertion["text"])
    score = 0.60 * k + 0.40 * d
    if missing:
        score = min(score, CAP_MISSING)
    return score, k, d


def match_coverage(sentences, assertions):
    """返回每条断言的匹配结果与整体覆盖率。

    sentences: [(原文, 归一化)]
    assertions: [{id,text,w,keys}]
    """
    units = split_units(sentences)
    n_s, n_a = len(units), len(assertions)
    result = {a["id"]: {"id": a["id"], "level": "missed", "score": 0.0,
                        "evidence": "", "support": 0, "key_hit": 0.0}
              for a in assertions}
    if n_s and n_a:
        score = [[0.0] * n_a for _ in range(n_s)]
        for i, (_, un, _parent) in enumerate(units):
            for j, a in enumerate(assertions):
                s, k, d = pair_score(un, a)
                score[i][j] = s
        cost = [[-score[i][j] for j in range(n_a)] for i in range(n_s)]
        for i, j in _hungarian_min(cost):
            if i < n_s and j < n_a and score[i][j] >= PARTIAL:
                cur = result[assertions[j]["id"]]
                if score[i][j] > cur["score"]:
                    cur["score"] = score[i][j]
                    cur["evidence"] = units[i][2]
                    cur["u"] = i          # 命中的匹配单元序号，用于判断「是否刚说过」
                    cur["key_hit"] = key_stats(assertions[j].get("keys", []), units[i][1])[0]
                    cur["level"] = "covered" if score[i][j] >= COVERED else "partial"
        # 支撑子句计数：判断「讲透了没有」
        for j, a in enumerate(assertions):
            cnt = sum(1 for i in range(n_s) if score[i][j] >= PARTIAL)
            result[a["id"]]["support"] = cnt

    total_w = sum(a["w"] for a in assertions) or 1.0
    got = 0.0
    for a in assertions:
        lv = result[a["id"]]["level"]
        if lv == "covered":
            got += a["w"]
        elif lv == "partial":
            got += a["w"] * 0.5
    rate = got / total_w
    covered = [a["id"] for a in assertions if result[a["id"]]["level"] == "covered"]
    partial = [a["id"] for a in assertions if result[a["id"]]["level"] == "partial"]
    missed = [a["id"] for a in assertions if result[a["id"]]["level"] == "missed"]
    return {
        "rate": rate,
        "covered": covered,
        "partial": partial,
        "missed": missed,
        "n_units": n_s,
        "detail": result,
    }
