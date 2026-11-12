# -*- coding: utf-8 -*-
"""把「知识点参考页」写进说明书的 6.3：正文提到它，图放在本节末尾（图 17），不打乱已有图号。"""
import json
import os

BASE = r"E:\人工智能作业\大作业"
P = os.path.join(BASE, "构建", "content.json")
items = json.load(open(P, encoding="utf-8"))

anchor = "讲解台右侧是和「小回」的对话。"
idx = next(i for i, it in enumerate(items)
           if it["k"] == "p" and anchor in it["v"])
j = idx + 1
while j < len(items) and items[j]["k"] != "p":
    j += 1

note = {"k": "p", "v": "另外补了一页「知识点参考」（图 17）。学生随时可以翻看这个知识点的标准讲解、必须讲到的九条断言，以及三条常见错误和对应纠正。它解决的是一个很实际的问题：被追问住之后，学生需要立刻有一个地方把正确说法读一遍，而不是继续在对话里被问。页面上的标准讲解可以直接朗读，也能一键「按这个讲一遍」回到讲解台。"}
items = items[:j] + [note] + items[j:]

tail = "成长档案的折线记录的是讲解质量而非考试分数"
k = next(i for i, it in enumerate(items) if it["k"] == "p" and tail in it["v"])
k += 1
fig = [
    {"k": "p", "v": "参考页把「教什么」摆在了明处：标准讲解给示范，必讲要点给清单，常见错误给对照。学生可以把它当成考前速览，也可以在讲完之后回来核对。"},
    {"k": "img", "v": ["shot-ref.png", None, 14.6]},
]
items = items[:k] + fig + items[k:]

json.dump(items, open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("插入完成，图片总数", sum(1 for i in items if i["k"] == "img"))
