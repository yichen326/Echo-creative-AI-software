# -*- coding: utf-8 -*-
"""文本规范化、分句、同义词归一。

设计取舍：不引入分词库（环境无 jieba），中文按字符 n-gram 处理，
配合领域同义词表与关键词组，足以覆盖口语讲解的匹配需求。
"""
import re
import unicodedata

# 全角转半角 + 去空白 + 小写
_WS = re.compile(r"\s+")
_PUNCT_CHARS = set(
    " \t\r\n\u3000"
    "，。！？、；：（）《》〈〉【】…—·"
    ",“”‘’"
    ",.!?;:()[]{}<>\"'`~|/\\-_+*=#@$%^&"
)

# 句末标点：用于分句
_SENT_END = re.compile(r"[。！？!?；;\n]+")

# 领域同义词：变体 -> 归一后的写法（用于关键词组匹配）
SYNONYMS = {
    "排开": ["排出", "溢出", "挤出去", "挤出的", "排出的", "被挤出", "溢出来的"],
    "浸入": ["浸没", "放进", "泡在", "没入", "放入", "浸在", "泡进"],
    "体积": ["容积", "多少立方"],
    "密度": ["疏密"],
    "重力": ["重量", "物重", "自重"],
    "浮力": ["向上的托力", "托力"],
    "压强": ["压力作用效果", "压力效果"],
    "深度": ["深浅", "液面到", "水面到"],
    "液体密度": ["ρ液", "液体密度", "液体的密度"],
    "压强公式": ["p=ρgh", "ρgh", "p等于ρgh"],
    "等于": ["=", "就是", "相等于"],
    "成正比": ["正比例", "正比", "越大也越大"],
    "上浮": ["浮起来", "浮上去", "往上升"],
    "下沉": ["沉下去", "往下沉", "沉底"],
    "悬浮": ["停在中间", "悬着"],
    "漂浮": ["浮在水面", "浮在液面", "露在外面"],
    "匀速": ["匀速直线", "速度不变"],
    "静止": ["不动", "停着"],
    "质量": ["m"],
    "体积符号": ["v"],
}

# 反向索引：某个变体 -> 它所属的标准词（在 norm_key 定义之后构建）
_VARIANT_TO_STD = {}


def norm_key(s: str) -> str:
    """用于关键词匹配的归一化：去空白、去标点、转小写。"""
    s = unicodedata.normalize("NFKC", s or "")
    s = s.lower()
    s = _WS.sub("", s)
    s = "".join(ch for ch in s if ch not in _PUNCT_CHARS)
    return s


for _std, _variants in SYNONYMS.items():
    for _v in _variants:
        _k = norm_key(_v)
        if _k:
            _VARIANT_TO_STD[_k] = _std


def split_sentences(text: str):
    """按句末标点切分，返回 [(原文, 归一化)]。空句丢弃。"""
    raw = (text or "").replace("\r", "\n")
    parts = []
    buf = []
    for ch in raw:
        buf.append(ch)
        if ch in "。！？!?；;\n":
            s = "".join(buf).strip()
            if s:
                parts.append(s)
            buf = []
    tail = "".join(buf).strip()
    if tail:
        parts.append(tail)
    out = []
    for s in parts:
        n = norm_key(s)
        if n:
            out.append((s, n))
    return out


def expand(text: str):
    """把同义变体替换成标准写法，便于关键词命中。

    只做「变体 -> 标准词」的方向，避免把标准词拆开。
    """
    t = norm_key(text)
    for variant, std in _VARIANT_TO_STD.items():
        if variant and variant in t and std not in t:
            t = t.replace(variant, std)
    return t


def split_units(sentences):
    """把长句再按逗号切成子句，用于匹配。

    口语里一句话常常连着说完两条断言，只按句号切会漏判。
    返回 [(子句原文, 归一化, 所属整句原文)]。
    """
    units = []
    for raw, norm in sentences:
        if len(norm) > 26 and ("，" in raw or "," in raw):
            # 整句先作为一个匹配单元（跨子句的断言靠它命中）
            units.append((raw, norm, raw))
            for part in re.split(r"[，,]", raw):
                p = part.strip()
                n = norm_key(p)
                if len(n) >= 4:
                    units.append((p, n, raw))
        else:
            units.append((raw, norm, raw))
    return units


def bigrams(s: str):
    s = norm_key(s)
    if len(s) < 2:
        return {s} if s else set()
    return {s[i:i + 2] for i in range(len(s) - 1)}


def dice(a: str, b: str) -> float:
    """字符二元组 Dice 相似度，取值 [0,1]。"""
    A, B = bigrams(a), bigrams(b)
    if not A or not B:
        return 0.0
    inter = len(A & B)
    return 2.0 * inter / (len(A) + len(B))


def key_stats(groups, sentence):
    """关键词组命中情况：返回 (命中率 0~1, 完全未命中的组数)。"""
    if not groups:
        return 0.0, 0
    text = expand(sentence)
    hit = 0.0
    missing = 0
    for group in groups:
        best = 0.0
        for alt in group:
            a = expand(alt)
            if not a:
                continue
            if a in text:
                best = 1.0
                break
            # 长词允许部分命中（口语常常只说半句）
            if len(a) >= 3 and a[:3] in text:
                best = max(best, 0.5)
        if best == 0.0:
            missing += 1
        hit += best
    return hit / len(groups), missing


def key_hit(groups, sentence):
    return key_stats(groups, sentence)[0]


def connective_density(texts):
    """因果/顺序连词密度，用于逻辑性评分。"""
    words = ["因为", "所以", "因此", "由于", "也就是说", "这说明", "如果", "那么",
             "首先", "然后", "接着", "最后", "因此", "从而", "可见"]
    joined = "".join(norm_key(t) for t in texts)
    if not joined:
        return 0.0
    cnt = sum(joined.count(w) for w in words)
    return cnt / max(1.0, len(joined) / 30.0)  # 每 30 字一个连词记 1.0


def example_density(texts):
    """举例标记密度。只用多字标记，避免「所以」里的「以」被误判。"""
    words = ["例如", "比如", "举个例子", "举例", "比如说", "例如说", "打个比方", "假如", "假设"]
    joined = "".join(norm_key(t) for t in texts)
    if not joined:
        return 0, False
    cnt = sum(joined.count(w) for w in words)
    # 「拿……来说」「以……为例」这类结构
    cnt += len(re.findall(r"拿.{1,10}来说", joined))
    cnt += len(re.findall(r"以.{1,10}为例", joined))
    has_num = bool(re.search(r"\d|[一二三四五六七八九十][个块次种倍度米]", joined))
    return cnt, has_num


def filler_ratio(texts):
    """口头禅与重复词比例。"""
    joined = "".join(norm_key(t) for t in texts)
    if not joined:
        return 1.0
    fillers = ["嗯", "呃", "那个", "这个", "然后就是", "反正", "对吧", "怎么说"]
    cnt = sum(joined.count(w) for w in fillers)
    return cnt * 8.0 / max(1.0, len(joined))
