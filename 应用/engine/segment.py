# -*- coding: utf-8 -*-
"""中文分词（jieba 可选）。

装了 jieba 就用词级切分，没装则退回字符二元组——
保证在裸环境下同样能跑，这是「轻量化」的底线。
"""
try:
    import jieba
    jieba.setLogLevel(60)
    _HAS_JIEBA = True
except Exception:  # pragma: no cover
    _HAS_JIEBA = False

from .text import norm_key

STOP = set("""的 了 是 我 你 他 她 它 在 就 也 和 与 这 那 个 把 被 会 要 说 讲
一个 一种 然后 所以 因为 但是 但 如果 那么 就是 等于 有 没有 不 很 都 又 还
可以 能 对 从 到 时 中 上 下 里 呢 吧 啊 吗 哦 嗯 这个 那个 我们 他 什么 怎么
时候 应该 就是 一个 一下 这样 那样 得 地 着 过 之 其 而 且 或 才 再 更 最""".split())


def words(text):
    """返回有意义的中文词列表。"""
    if _HAS_JIEBA:
        ws = jieba.lcut(text)
    else:
        s = norm_key(text)
        ws = [s[i:i + 2] for i in range(len(s) - 1)]
    out = []
    for w in ws:
        w = w.strip()
        if not w or w in STOP:
            continue
        if len(w) == 1 and not ("\u4e00" <= w <= "\u9fff"):
            continue
        out.append(w)
    return out


def overlap(a_words, b_words):
    if not a_words or not b_words:
        return 0.0
    sa, sb = set(a_words), set(b_words)
    return len(sa & sb) / float(min(len(sa), len(sb)))
