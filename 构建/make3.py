# -*- coding: utf-8 -*-
"""docx 被 Word 占用时的构建方案：先产出到临时文件，再尝试替换正式文件。"""
import os
import shutil
import sys

import build2 as B
import make2 as M

BASE = B.BASE
TMP_DOCX = os.path.join(BASE, "构建", "_final.docx")
TMP_PDF = os.path.join(BASE, "构建", "_final.pdf")


def main():
    hs = B.build(TMP_DOCX)
    M.to_pdf(TMP_DOCX, TMP_PDF)
    pages, texts = M.locate(TMP_PDF, hs)
    print("pages:", len(texts), "| missing:", [k for k, v in pages.items() if v == ""])
    B.build(TMP_DOCX, pages)
    M.to_pdf(TMP_DOCX, TMP_PDF)
    pages2, texts2 = M.locate(TMP_PDF, hs)
    print("final pages:", len(texts2), "| drift:", {k: (pages[k], pages2[k]) for k in pages if pages[k] != pages2[k]})

    # 替换正式文件（被占用则保留临时文件）
    ok_docx = ok_pdf = False
    try:
        shutil.copyfile(TMP_DOCX, B.OUT)
        ok_docx = True
    except PermissionError:
        print("DOCX 被占用，未替换：", B.OUT)
    try:
        shutil.copyfile(TMP_PDF, os.path.join(BASE, "回声Echo-创意设计说明书.pdf"))
        ok_pdf = True
    except PermissionError:
        print("PDF 被占用，未替换")

    print("替换结果 docx=%s pdf=%s" % (ok_docx, ok_pdf))
    return 0 if (ok_docx and ok_pdf) else 2


if __name__ == "__main__":
    sys.exit(main())
