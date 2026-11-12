# -*- coding: utf-8 -*-
import os, json
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

BASE = r"E:\人工智能作业\大作业"
IMG = os.path.join(BASE, "构建", "img")
OUT = os.path.join(BASE, "回声Echo-创意设计说明书.docx")
DATA = os.path.join(BASE, "构建", "content.json")

SONG, HEI, LATIN = "宋体", "黑体", "Times New Roman"
INK = RGBColor(0x1F, 0x1D, 0x1A)
GRAY = RGBColor(0x59, 0x55, 0x4F)

TITLE = "回声 Echo：“会追问的 AI 小先生”"
SUBTITLE = "面向“讲述式学习”的轻量化认知诊断系统创意设计"

FIG_CAP = {
    1: "图 2　讲述式认知诊断流水线",
    2: "图 3　根因链示意：他卡住的不是浮力",
    3: "图 4　系统功能架构",
    4: "图 5　今日首页",
    5: "图 6　讲解台",
    6: "图 7　讲解体检报告",
    7: "图 8　知识地图",
    8: "图 9　复述计划",
    9: "图 10　成长档案",
    10: "图 11　首页实现效果",
    11: "图 12　讲解台实现效果",
    12: "图 13　体检报告实现效果",
    13: "图 14　知识地图实现效果",
    14: "图 15　复述计划实现效果",
    15: "图 16　成长档案实现效果",
    16: "图 17　知识点参考页",
}
TBLW = [
    ([2.2, 3.0, 3.0, 3.0, 3.2], "表 1　四类产品的对比"),
    ([2.4, 4.3, 2.4, 2.7, 2.2], "表 2　各环节实现方式与耗时"),
    ([2.4, 6.4, 5.6], "表 3　技术选型"),
    ([2.4, 4.9, 3.2, 3.9], "表 4　数据资产清单"),
    ([2.2, 5.4, 6.8], "表 5　五周开发计划"),
    ([2.6, 4.3, 7.5], "表 6　视觉规范"),
]


def set_font(run, east=SONG, latin=LATIN, size=10.5, bold=False, color=None):
    run.font.size = Pt(size)
    run.bold = bold
    if color is not None:
        run.font.color.rgb = color
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    rFonts.set(qn("w:ascii"), latin)
    rFonts.set(qn("w:hAnsi"), latin)
    rFonts.set(qn("w:eastAsia"), east)
    rFonts.set(qn("w:cs"), latin)


def para_fmt(p, first_indent=True, space_before=0, space_after=0, line=20, align=None):
    pf = p.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    pf.line_spacing = Pt(line)
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    pf.first_line_indent = Pt(21) if first_indent else Pt(0)
    if align is not None:
        pf.alignment = align


def caption(doc, text, above=False):
    p = doc.add_paragraph()
    para_fmt(p, first_indent=False, space_before=(12 if above else 4),
             space_after=(4 if above else 10), line=16, align=WD_ALIGN_PARAGRAPH.CENTER)
    if above:
        p.paragraph_format.keep_with_next = True
    set_font(p.add_run(text), size=9, color=GRAY)


def fix_grid(t, widths):
    tbl, tblPr = t._tbl, t._tbl.tblPr
    tw = OxmlElement("w:tblW")
    tw.set(qn("w:w"), str(int(sum(widths) * 567)))
    tw.set(qn("w:type"), "dxa")
    tblPr.append(tw)
    lay = OxmlElement("w:tblLayout")
    lay.set(qn("w:type"), "fixed")
    tblPr.append(lay)
    for i, gc in enumerate(tbl.tblGrid.findall(qn("w:gridCol"))):
        if i < len(widths):
            gc.set(qn("w:w"), str(int(widths[i] * 567)))


def table_borders(table, color="D8D2C6"):
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement("w:" + edge)
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color)
        borders.append(el)
    table._tbl.tblPr.append(borders)


def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tcPr.append(shd)


def page_field(p):
    run = p.add_run()
    a = OxmlElement("w:fldChar"); a.set(qn("w:fldCharType"), "begin")
    b = OxmlElement("w:instrText"); b.set(qn("xml:space"), "preserve"); b.text = " PAGE "
    c = OxmlElement("w:fldChar"); c.set(qn("w:fldCharType"), "end")
    run._r.append(a); run._r.append(b); run._r.append(c)
    set_font(run, size=9, color=GRAY)


def data_table(doc, headers, rows, widths, size=9, header_fill="EDE8DD"):
    t = doc.add_table(rows=1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    table_borders(t)
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]
        c.text = ""
        p = c.paragraphs[0]
        para_fmt(p, first_indent=False, line=14, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_font(p.add_run(h), size=size, bold=True, color=INK)
        shade(c, header_fill)
    t.rows[0]._tr.get_or_add_trPr().append(OxmlElement("w:tblHeader"))
    for row in rows:
        cells = t.add_row().cells
        t.rows[-1]._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        for i, v in enumerate(row):
            cells[i].text = ""
            p = cells[i].paragraphs[0]
            al = WD_ALIGN_PARAGRAPH.LEFT if i == 0 else WD_ALIGN_PARAGRAPH.CENTER
            para_fmt(p, first_indent=False, line=14, align=al)
            set_font(p.add_run(v), size=size, color=INK)
    for row in t.rows:
        for i, w in enumerate(widths):
            row.cells[i].width = Cm(w)
    for i, w in enumerate(widths):
        t.columns[i].width = Cm(w)
    fix_grid(t, widths)
    for ri, row in enumerate(t.rows):
        for c in row.cells:
            tcPr = c._tc.get_or_add_tcPr()
            va = OxmlElement("w:vAlign")
            va.set(qn("w:val"), "center")
            tcPr.append(va)
            if ri < len(t.rows) - 1:
                for p in c.paragraphs:
                    p.paragraph_format.keep_with_next = True
    sp = doc.add_paragraph()
    para_fmt(sp, first_indent=False, line=12, space_after=0)
    return t


def build(path, pages=None):
    pages = pages or {}
    items = json.load(open(DATA, encoding="utf-8"))
    headings = [(it["k"], it["v"]) for it in items if it["k"] in ("h1", "h2")]

    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
    sec.top_margin = sec.bottom_margin = Cm(2.54)
    sec.left_margin = sec.right_margin = Cm(3.17)

    st = doc.styles["Normal"]
    st.font.name = LATIN
    st.font.size = Pt(10.5)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), SONG)

    # ---------------- cover
    for _ in range(5):
        para_fmt(doc.add_paragraph(), first_indent=False, line=20)
    p = doc.add_paragraph()
    para_fmt(p, first_indent=False, line=34, align=WD_ALIGN_PARAGRAPH.CENTER)
    set_font(p.add_run("信息与人工智能学院"), east=HEI, size=22, bold=True, color=INK)
    p = doc.add_paragraph()
    para_fmt(p, first_indent=False, line=26, align=WD_ALIGN_PARAGRAPH.CENTER)
    set_font(p.add_run("（工业软件学院）"), size=14, color=GRAY)
    for _ in range(2):
        para_fmt(doc.add_paragraph(), first_indent=False, line=20)
    p = doc.add_paragraph()
    para_fmt(p, first_indent=False, line=44, align=WD_ALIGN_PARAGRAPH.CENTER)
    set_font(p.add_run("《人工智能导论》大作业"), east=HEI, size=26, bold=True, color=INK)
    p = doc.add_paragraph()
    para_fmt(p, first_indent=False, line=30, align=WD_ALIGN_PARAGRAPH.CENTER)
    set_font(p.add_run("创 意 设 计 说 明 书"), size=13, color=GRAY)
    for _ in range(4):
        para_fmt(doc.add_paragraph(), first_indent=False, line=20)

    t = doc.add_table(rows=4, cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    table_borders(t, "BFB6A4")
    rows = [("设计题目", TITLE), ("班　　级", ""), ("学　　号", ""), ("姓　　名", "")]
    for i, (k, v) in enumerate(rows):
        c0, c1 = t.rows[i].cells
        c0.width, c1.width = Cm(3.4), Cm(11.1)
        for c in (c0, c1):
            va = OxmlElement("w:vAlign"); va.set(qn("w:val"), "center")
            c._tc.get_or_add_tcPr().append(va)
        p0 = c0.paragraphs[0]
        para_fmt(p0, first_indent=False, line=30, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_font(p0.add_run(k), size=12, bold=True)
        p1 = c1.paragraphs[0]
        para_fmt(p1, first_indent=False, line=30, align=WD_ALIGN_PARAGRAPH.LEFT)
        set_font(p1.add_run(v), size=12, bold=(i == 0))
    for i, w in enumerate([3.4, 11.1]):
        t.columns[i].width = Cm(w)
    fix_grid(t, [3.4, 11.1])

    for _ in range(5):
        para_fmt(doc.add_paragraph(), first_indent=False, line=20)
    p = doc.add_paragraph()
    para_fmt(p, first_indent=False, line=26, align=WD_ALIGN_PARAGRAPH.CENTER)
    set_font(p.add_run("完成日期： 2026 年 11 月"), size=12)

    # ---------------- section 2
    new = doc.add_section(WD_SECTION.NEW_PAGE)
    new.page_width, new.page_height = Cm(21.0), Cm(29.7)
    new.top_margin = new.bottom_margin = Cm(2.54)
    new.left_margin = new.right_margin = Cm(3.17)
    pg = OxmlElement("w:pgNumType"); pg.set(qn("w:start"), "1")
    new._sectPr.append(pg)
    new.footer.is_linked_to_previous = False
    fp = new.footer.paragraphs[0]
    para_fmt(fp, first_indent=False, line=14, align=WD_ALIGN_PARAGRAPH.CENTER)
    page_field(fp)

    # ---------------- TOC
    p = doc.add_paragraph()
    para_fmt(p, first_indent=False, line=32, space_after=8, align=WD_ALIGN_PARAGRAPH.CENTER)
    set_font(p.add_run("目　　录"), east=HEI, size=16, bold=True, color=INK)
    for kind, txt in headings:
        p = doc.add_paragraph()
        pf = p.paragraph_format
        pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
        pf.line_spacing = Pt(18 if kind == "h1" else 13)
        pf.space_before = Pt(5 if kind == "h1" else 0)
        pf.space_after = Pt(0)
        pf.first_line_indent = Pt(0)
        pf.left_indent = Cm(0 if kind == "h1" else 0.85)
        pf.tab_stops.add_tab_stop(Cm(14.4), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
        set_font(p.add_run(txt), size=11.5 if kind == "h1" else 9.2, bold=(kind == "h1"))
        p.add_run("\t")
        set_font(p.runs[-1], size=9.5)
        set_font(p.add_run(str(pages.get(txt, ""))), size=9.5)
    doc.add_page_break()

    # ---------------- body title
    p = doc.add_paragraph()
    para_fmt(p, first_indent=False, line=30, space_after=4, align=WD_ALIGN_PARAGRAPH.CENTER)
    set_font(p.add_run(TITLE), east=HEI, size=18, bold=True, color=INK)
    p = doc.add_paragraph()
    para_fmt(p, first_indent=False, line=24, space_after=16, align=WD_ALIGN_PARAGRAPH.CENTER)
    set_font(p.add_run("—— " + SUBTITLE + " ——"), size=12, color=GRAY)

    # ---------------- body
    fi = ti = 0
    for it in items:
        k, v = it["k"], it["v"]
        if k == "h1":
            p = doc.add_paragraph()
            p.style = doc.styles["Heading 1"]
            para_fmt(p, first_indent=False, line=28, space_before=14, space_after=8,
                     align=WD_ALIGN_PARAGRAPH.LEFT)
            p.paragraph_format.keep_with_next = True
            set_font(p.add_run(v), size=14, bold=True, color=INK)
        elif k == "h2":
            p = doc.add_paragraph()
            p.style = doc.styles["Heading 2"]
            para_fmt(p, first_indent=False, line=24, space_before=9, space_after=4,
                     align=WD_ALIGN_PARAGRAPH.LEFT)
            p.paragraph_format.keep_with_next = True
            set_font(p.add_run(v), size=12, bold=True, color=INK)
        elif k in ("p", "b"):
            p = doc.add_paragraph()
            para_fmt(p, first_indent=True, align=WD_ALIGN_PARAGRAPH.JUSTIFY)
            set_font(p.add_run(v), size=10.5)
        elif k == "img":
            fi += 1
            path_img = os.path.join(IMG, v[0])
            p = doc.add_paragraph()
            pf = p.paragraph_format
            pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
            pf.space_before = Pt(8)
            pf.space_after = Pt(0)
            pf.first_line_indent = Pt(0)
            pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
            pf.keep_with_next = True
            p.add_run().add_picture(path_img, width=Cm(14.6))
            caption(doc, FIG_CAP[fi])
        elif k == "tbl":
            ti += 1
            widths, cap = TBLW[ti - 1]
            caption(doc, cap, above=True)
            data_table(doc, v["headers"], v["rows"], widths)

    doc.save(path)
    return headings


if __name__ == "__main__":
    hs = build(os.path.join(BASE, "构建", "_p1.docx"))
    print("ok", len(hs))
