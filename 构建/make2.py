# -*- coding: utf-8 -*-
import os, re, subprocess, json
from pypdf import PdfReader
import build2 as B

NODE = r"E:\dsh\resources\runtime\primary-runtime\dependencies\node\bin\node.exe"
CLI = r"E:\dsh\resources\app.asar.unpacked\dsh\node_modules\@deepseek-ai\libreoffice-kit\lib\cli.js"
BASE = B.BASE


def to_pdf(docx_path, pdf_path):
    if os.path.exists(pdf_path):
        os.remove(pdf_path)
    subprocess.run([NODE, CLI, "convert", "--input", docx_path, "--output", pdf_path],
                   capture_output=True, text=True)
    if not os.path.exists(pdf_path):
        raise SystemExit("convert failed: " + docx_path)


def norm(s):
    return re.sub(r"\s+", "", s)


def texts_of(pdf_path):
    return [norm(p.extract_text() or "") for p in PdfReader(pdf_path).pages]


def locate(pdf_path, headings):
    texts = texts_of(pdf_path)
    start = 2
    for i, t in enumerate(texts):
        if "轻量化认知诊断系统创意设计" in t and "目录" not in t:
            start = i
            break
    res, pos = {}, start
    for kind, txt in headings:
        key = norm(txt)
        found = None
        for i in range(pos, len(texts)):
            if key in texts[i]:
                found = i
                break
        if found is None:
            key2 = re.sub(r"^[一二三四五六七八九十]+、|^\d+\.\d+", "", key)
            for i in range(pos, len(texts)):
                if key2 and key2 in texts[i]:
                    found = i
                    break
        res[txt] = found if found is not None else ""
        if found is not None:
            pos = found
    return res, texts


if __name__ == "__main__":
    p1 = os.path.join(BASE, "构建", "_p1.docx")
    pdf1 = os.path.join(BASE, "构建", "_p1.pdf")
    hs = B.build(p1)
    to_pdf(p1, pdf1)
    pages, texts = locate(pdf1, hs)
    print("pages:", len(texts))
    print("missing:", [k for k, v in pages.items() if v == ""])
    B.build(B.OUT, pages)
    pdf2 = os.path.join(BASE, "构建", "_p2.pdf")
    to_pdf(B.OUT, pdf2)
    pages2, texts2 = locate(pdf2, hs)
    print("final pages:", len(texts2))
    print("drift:", {k: (pages[k], pages2[k]) for k in pages if pages[k] != pages2[k]})
    print(json.dumps(pages2, ensure_ascii=False))
