# -*- coding: utf-8 -*-
"""朗读中的答疑：把学生的提问分流到术语表、范文、断言、迷思上。

没有联网大模型，所以不"自由发挥"——每种意图都从知识库里取现成的内容，
答不上来就直说，并把标准说法再讲一遍。
"""
from .text import bigrams, dice, norm_key

INTENT_WORDS = {
    "stop": ["停", "别读", "安静", "暂停", "不读了", "安静点"],
    "resume": ["继续", "接着读", "接着讲"],
    "example": ["举个例子", "举例", "比如", "例子", "打个比方"],
    "elaborate": ["再讲", "详细", "没听懂", "听不懂", "不懂", "展开", "多讲", "讲全", "讲完整", "说清楚"],
    "why": ["为什么", "凭什么", "怎么来的", "怎么会"],
    "define": ["是什么意思", "什么意思", "是什么", "啥意思", "怎么理解", "解释", "定义", "指的是"],
}
LABELS = {
    "stop": "暂停", "resume": "继续", "example": "举例",
    "elaborate": "展开讲", "why": "讲原因", "define": "解释名词",
    "unknown": "答疑",
}


def _find_term(kb, text):
    """在问题里找术语，优先最长匹配。"""
    t = norm_key(text)
    best = None
    for g in kb.glossary:
        cands = [g["term"]] + list(g.get("alias", []))
        for c in cands:
            n = norm_key(c)
            if n and n in t and (best is None or len(n) > best[0]):
                best = (len(n), g)
    return best[1] if best else None


def _sentences(text):
    return [s for s in (text or "").replace("\n", "").split("。") if s.strip()]


def best_assertion(kb, node_id, sentence):
    arr = kb.assertions_of(node_id)
    if not arr:
        return None
    scored = sorted(((dice(sentence, a["text"]), a) for a in arr), key=lambda x: -x[0])
    return scored[0][1] if scored and scored[0][0] >= 0.15 else None


def answer(kb, node_id, text, last_said=""):
    t = norm_key(text or "")
    node = kb.nodes.get(node_id, {})
    ref = node.get("reference", "")
    example = None
    try:
        from .diagnose import NODE_EXAMPLE
        example = NODE_EXAMPLE.get(node_id)
    except Exception:
        pass

    # 1. 控制类
    for w in INTENT_WORDS["stop"]:
        if w in t:
            return {"intent": "stop", "label": LABELS["stop"],
                    "answer": "好，我先停下来。有想问的随时说。", "speak": ["好，我先停下来。"]}
    for w in INTENT_WORDS["resume"]:
        if w in t:
            return {"intent": "resume", "label": LABELS["resume"],
                    "answer": "那我们接着讲。", "speak": ["那我们接着讲。"]}

    term = _find_term(kb, t)

    # 2. 「刚才那句」「这句」——针对刚读过的句子解释
    if any(w in t for w in ("刚才", "这句", "这一句", "那句", "上一句")) and last_said:
        a = best_assertion(kb, node_id, last_said)
        if a:
            sub = _find_term(kb, last_said)
            say = "刚才那句说的是：%s。" % a["text"].rstrip("。")
            if sub:
                say += "%s" % sub["def"]
            return {"intent": "elaborate", "label": "讲这一句",
                    "answer": say, "speak": _sentences(say),
                    "term": sub["term"] if sub else None}
        return {"intent": "elaborate", "label": "讲这一句",
                "answer": "刚才那句是：%s" % last_said,
                "speak": _sentences(last_said), "term": None}

    # 3. 举例
    if any(w in t for w in INTENT_WORDS["example"]) and example:
        say = "举个例子：%s。" % example
        return {"intent": "example", "label": LABELS["example"],
                "answer": say, "speak": _sentences(say), "term": term["term"] if term else None}

    # 4. 问术语
    if term and (any(w in t for w in INTENT_WORDS["define"]) or len(t) <= len(norm_key(term["term"])) + 2):
        return {"intent": "define", "label": LABELS["define"],
                "answer": term["def"], "speak": _sentences(term["def"]),
                "term": term["term"]}

    # 5. 问原因：优先找这个知识点里最相关的那条迷思纠正
    if any(w in t for w in INTENT_WORDS["why"]):
        qb = bigrams(text)
        best, best_sc = None, 0
        for m in kb.mis_by_node.get(node_id, []):
            sc = len(qb & bigrams(m["title"] + m["correction"]))
            if sc > best_sc:
                best, best_sc = m, sc
        cause = [s for s in _sentences(ref) if any(k in s for k in ("因为", "所以", "由于", "关键是"))]
        if best and best_sc >= 2:
            say = best["correction"]
        elif cause:
            say = "原因是这样的。" + "。".join(cause[:2]) + "。"
        elif term:
            say = "关键在于：%s" % term["def"]
        else:
            say = "。".join(_sentences(ref)[:2]) + "。"
        return {"intent": "why", "label": LABELS["why"],
                "answer": say, "speak": _sentences(say),
                "term": term["term"] if term else None}

    # 6. 展开讲（带上术语就讲那一段）
    if any(w in t for w in INTENT_WORDS["elaborate"]):
        if term:
            hits = [s for s in _sentences(ref) if norm_key(term["term"]) in norm_key(s)]
            body = "。".join(hits[:2]) if hits else ref
            say = "我把「%s」这一段完整讲一遍。%s" % (term["term"], body)
        else:
            say = "%s" % ref
        return {"intent": "elaborate", "label": LABELS["elaborate"],
                "answer": say, "speak": _sentences(say),
                "term": term["term"] if term else None}

    # 7. 只说了个术语
    if term:
        return {"intent": "define", "label": LABELS["define"],
                "answer": term["def"], "speak": _sentences(term["def"]),
                "term": term["term"]}

    # 8. 兜底：不装作懂，把标准说法再讲一遍
    first = _sentences(ref)[:2]
    say = "这个我暂时答不上来，先把标准说法再讲一遍。%s" % "。".join(first)
    return {"intent": "unknown", "label": LABELS["unknown"],
            "answer": say, "speak": _sentences(say), "term": None}
