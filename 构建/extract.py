# -*- coding: utf-8 -*-
"""Extract structured content from the already-built DOCX so the prose is preserved
exactly, then dump it as JSON for the fixed builder."""
import json, os, sys
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH

SRC = r"E:\人工智能作业\大作业\回声Echo-创意设计说明书.docx"
OUT = r"E:\人工智能作业\大作业\构建\content.json"
IMGS = ["f2.png", "f3.png", "f4.png", "w1.png", "w2.png", "w3.png", "w4.png", "w5.png", "w6.png"]

doc = Document(SRC)
body = doc.element.body
items = []
started = False
ii = 0

for child in body.iterchildren():
    if child.tag == qn("w:p"):
        p = Paragraph(child, doc)
        txt = p.text.strip()
        if not started:
            if txt.startswith("回声 Echo："):
                started = True
            continue
        if txt.startswith("—— 面向"):
            continue
        if child.findall(".//" + qn("w:drawing")):
            if ii >= len(IMGS):
                raise SystemExit("more images than expected")
            items.append({"k": "img", "v": [IMGS[ii], None, 14.6]})
            ii += 1
            continue
        if not txt:
            continue
        al = p.paragraph_format.alignment
        if al == WD_ALIGN_PARAGRAPH.CENTER and (txt.startswith("图 ") or txt.startswith("表 ")):
            continue
        st = p.style.name
        if st == "Heading 1":
            items.append({"k": "h1", "v": txt})
        elif st == "Heading 2":
            items.append({"k": "h2", "v": txt})
        else:
            fi = p.paragraph_format.first_line_indent
            if fi is not None and fi < 0:
                items.append({"k": "b", "v": txt})
            else:
                items.append({"k": "p", "v": txt})
    elif child.tag == qn("w:tbl"):
        if not started:
            continue
        t = Table(child, doc)
        rows = [[c.text.strip() for c in r.cells] for r in t.rows]
        items.append({"k": "tbl", "v": {"headers": rows[0], "rows": rows[1:]}})

json.dump(items, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
from collections import Counter
print("items:", Counter(i["k"] for i in items))
print("images used:", ii)
