# -*- coding: utf-8 -*-
"""记忆调度：FSRS-4.5 简化实现。

每张复述卡维护 稳定度 S（天）与 难度 D（1~10）；
复习等级 g∈{1,2,3,4} 由本次讲解质量映射而来。
"""
import math

# FSRS-4.5 默认权重（17 个参数）
W = [0.4872, 1.4003, 3.7145, 13.8206, 5.1618, 1.2298, 0.8975, 0.0310,
     1.6474, 0.1367, 1.0461, 2.1072, 0.0793, 0.3246, 1.5870, 0.2272, 2.8755]

TARGET_R = 0.90
MAX_I = 180


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def init_stability(g):
    return max(W[g - 1], 0.1)


def init_difficulty(g):
    return clamp(W[4] - (g - 3) * W[5], 1.0, 10.0)


def next_difficulty(d, g):
    nd = W[7] * init_difficulty(4) + (1 - W[7]) * (d - W[6] * (g - 3))
    return clamp(nd, 1.0, 10.0)


def retrievability(t, s):
    if s <= 0:
        return 0.0
    return (1 + t / (9.0 * s)) ** -1


def next_stability(d, s, r, g):
    hard = W[15] if g == 2 else 1.0
    easy = W[16] if g == 4 else 1.0
    s2 = s * (1 + math.exp(W[8]) * (11 - d) * (s ** -W[9])
              * (math.exp((1 - r) * W[10]) - 1) * hard * easy)
    return max(s2, 0.1)


def interval(s):
    """下次复习间隔（天）。"""
    i = 9.0 * s * (1.0 / TARGET_R - 1.0)
    return int(clamp(round(i), 1, MAX_I))


def quality_to_grade(total_score):
    """综合分 -> 复习等级。"""
    if total_score >= 85:
        return 4
    if total_score >= 70:
        return 3
    if total_score >= 55:
        return 2
    return 1


def schedule(card, grade, elapsed_days=0):
    """更新卡片，返回 (新卡, 间隔天数)。"""
    s0 = card.get("stability") or 0.0
    d0 = card.get("difficulty") or 0.0
    if not s0 or not d0:
        s = init_stability(grade)
        d = init_difficulty(grade)
    else:
        r = retrievability(elapsed_days, s0)
        s = next_stability(d0, s0, r, grade)
        d = next_difficulty(d0, grade)
    i = interval(s)
    return {"stability": round(s, 3), "difficulty": round(d, 3), "interval": i}, i
