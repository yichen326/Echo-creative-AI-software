# -*- coding: utf-8 -*-
"""贝叶斯知识追踪（BKT）。

每个知识点维护一个「已掌握」概率 P(L)，每次观察按贝叶斯规则更新：
  P(L|o) ∝ P(o|L)·P(L)，再叠加一次学习转移 P(T)。
"""


class BKT:
    def __init__(self, p_l0=0.35, p_t=0.18, p_g=0.20, p_s=0.10):
        self.p_l0 = p_l0
        self.p_t = p_t
        self.p_g = p_g
        self.p_s = p_s

    def posterior(self, p_l, correct):
        if correct:
            num = p_l * (1 - self.p_s)
            den = num + (1 - p_l) * self.p_g
        else:
            num = p_l * self.p_s
            den = num + (1 - p_l) * (1 - self.p_g)
        return num / den if den > 1e-9 else p_l

    def step(self, p_l, correct):
        post = self.posterior(p_l, correct)
        return post + (1 - post) * self.p_t

    def evidence_to_correct(self, quality):
        """把 0~1 的讲解质量映射为一次正确/错误观察。"""
        return quality >= 0.6


class Mastery:
    """一组学生的掌握度。prior 为冷启动画像。"""

    def __init__(self, node_ids, prior=None, bkt=None):
        self.bkt = bkt or BKT()
        self.p = {}
        for nid in node_ids:
            self.p[nid] = float((prior or {}).get(nid, self.bkt.p_l0))

    def get(self, nid):
        return self.p.get(nid, self.bkt.p_l0)

    def observe(self, nid, quality):
        correct = self.bkt.evidence_to_correct(quality)
        self.p[nid] = self.bkt.step(self.get(nid), correct)
        return self.p[nid]

    def as_dict(self):
        return dict(self.p)
