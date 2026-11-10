#!/usr/bin/env python3
"""Construye docs/articulo.docx a partir de docs/scripts/articulo.md.

Uso:
    python docs/scripts/build_article.py

Aplica el formato de Normas.docx: A4, márgenes de 3 cm (izquierda/derecha)
y 2,5 cm (superior/inferior), cuerpo Times New Roman 11, interlineado 1,15,
títulos numerados, tablas y figuras autosuficientes, referencias APA 7 con
sangría francesa y numeración de páginas.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[2]
MD = ROOT / "docs" / "scripts" / "articulo.md"
TAB = ROOT / "docs" / "tablas"
FIG = ROOT / "docs" / "figuras"
OUT = ROOT / "docs" / "articulo.docx"

BODY_FONT = "Times New Roman"
MONO_FONT = "Consolas"
INK = RGBColor(0x0B, 0x12, 0x20)
GREY = RGBColor(0x55, 0x5F, 0x6D)
HEADER_FILL = "DCE6F1"
BORDER = "AEB6C2"

TABLE_WIDTHS = {
    "tabla1_catalogo": [2.1, 1.5, 1.8, 5.1, 1.6, 2.9],
    "tabla2_flota": [5.0, 2.5, 2.5, 2.5, 2.5],
    "tabla3_por_control": [2.9, 1.6, 1.7, 1.7, 1.2, 2.3, 1.1, 1.1],
    "tabla4_rondas": [1.0, 1.0, 1.3, 1.0, 1.3, 1.1, 1.1, 1.6, 1.6, 1.8, 1.6],
    "tabla5_concordancia": [5.4, 2.8, 2.7, 2.1, 2.0],
    "tabla6_hallazgos": [2.0, 1.5, 1.7, 1.7, 1.7, 3.4, 2.5],
}

FIGURE_WIDTHS = {
    "figura1_cumplimiento_rondas": 15.0,
    "figura2_mapa_calor": 10.6,
    "figura3_control_verdad": 14.2,
    "figura4_matriz_confusion": 11.2,
    "figura5_hallazgos": 14.8,
    "figura6_latencia": 14.2,
}


# --------------------------------------------------------------------------- utilidades
def set_cell_border(cell, color: str = BORDER, size: int = 4) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right"):
        element = OxmlElement(f"w:{edge}")
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), str(size))
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), color)
        borders.append(element)
    tc_pr.append(borders)


def shade_cell(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def repeat_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def cant_split(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:cantSplit")
    el.set(qn("w:val"), "true")
    tr_pr.append(el)


def add_field(paragraph, instr: str) -> None:
    run = paragraph.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr_el = OxmlElement("w:instrText")
    instr_el.set(qn("xml:space"), "preserve")
    instr_el.text = instr
    fld_sep = OxmlElement("w:fldChar")
    fld_sep.set(qn("w:fldCharType"), "separate")
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_begin)
    run._r.append(instr_el)
    run._r.append(fld_sep)
    run._r.append(fld_end)


def style_document(doc: Document) -> None:
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.left_margin = Cm(3.0)
    section.right_margin = Cm(3.0)
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.header_distance = Cm(1.25)
    section.footer_distance = Cm(1.25)

    normal = doc.styles["Normal"]
    normal.font.name = BODY_FONT
    normal.font.size = Pt(11)
    normal.font.color.rgb = INK
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), BODY_FONT)
    pf = normal.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing = 1.15
    pf.space_after = Pt(6)
    pf.space_before = Pt(0)
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    for name, size, before, after, italic in (
        ("Heading 1", 12.5, 14, 6, False),
        ("Heading 2", 11.5, 10, 4, False),
        ("Heading 3", 11, 8, 3, True),
    ):
        st = doc.styles[name]
        st.font.name = BODY_FONT
        st.font.size = Pt(size)
        st.font.bold = True
        st.font.italic = italic
        st.font.color.rgb = INK
        st._element.rPr.rFonts.set(qn("w:eastAsia"), BODY_FONT)
        st.paragraph_format.space_before = Pt(before)
        st.paragraph_format.space_after = Pt(after)
        st.paragraph_format.keep_with_next = True
        st.paragraph_format.line_spacing = 1.0
        st.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT

    # Encabezado y pie
    header = section.header
    hp = header.paragraphs[0]
    hp.text = ""
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    hr = hp.add_run("Auditoría continua del hardening Linux basada en controles CIS")
    hr.font.name = BODY_FONT
    hr.font.size = Pt(8)
    hr.font.color.rgb = GREY
    hr.italic = True

    footer = section.footer
    fp = footer.paragraphs[0]
    fp.text = ""
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = fp.add_run("Página ")
    r.font.name = BODY_FONT
    r.font.size = Pt(9)
    r.font.color.rgb = GREY
    add_field(fp, " PAGE ")
    r2 = fp.add_run(" de ")
    r2.font.name = BODY_FONT
    r2.font.size = Pt(9)
    r2.font.color.rgb = GREY
    add_field(fp, " NUMPAGES ")
    for run in fp.runs:
        run.font.name = BODY_FONT
        run.font.size = Pt(9)
        run.font.color.rgb = GREY


def add_runs(paragraph, text: str, *, size: float | None = None, bold: bool = False,
             italic: bool = False, color: RGBColor | None = None, font: str | None = None) -> None:
    pattern = re.compile(r"(\*\*.+?\*\*|\*[^*]+?\*|`[^`]+`|<sub>.*?</sub>)")
    for token in pattern.split(text):
        if not token:
            continue
        b, i, mono, sub = bold, italic, False, False
        value = token
        if token.startswith("**") and token.endswith("**") and len(token) > 4:
            value = token[2:-2]
            b = True
        elif token.startswith("*") and token.endswith("*") and len(token) > 2:
            value = token[1:-1]
            i = True
        elif token.startswith("`") and token.endswith("`") and len(token) > 2:
            value = token[1:-1]
            mono = True
        elif token.startswith("<sub>") and token.endswith("</sub>"):
            value = token[5:-6]
            sub = True
        run = paragraph.add_run(value)
        run.bold = b
        run.italic = i
        run.font.name = MONO_FONT if mono else (font or BODY_FONT)
        run.font.size = Pt(size) if size else Pt(11)
        run.font.subscript = sub
        if color is not None:
            run.font.color.rgb = color


# --------------------------------------------------------------------------- bloques
def add_title_block(doc: Document) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(10)
    p.paragraph_format.line_spacing = 1.0
    r = p.add_run(
        "Auditoría continua y de solo lectura del hardening de servidores Linux "
        "basada en controles CIS: diseño, implementación y evaluación experimental "
        "de CIS Hardening Auditor"
    )
    r.font.name = BODY_FONT
    r.font.size = Pt(16)
    r.bold = True
    r.font.color.rgb = INK

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.0
    r = p.add_run("Ricardo Bernardo Velasquez Garcia")
    r.font.name = BODY_FONT
    r.font.size = Pt(11.5)
    r.bold = True
    r = p.add_run("  ·  ")
    r.font.size = Pt(11.5)
    r = p.add_run("Stiven Adrian Lopez Malca")
    r.font.name = BODY_FONT
    r.font.size = Pt(11.5)
    r.bold = True

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.0
    r = p.add_run("Universidad Nacional de Trujillo, Trujillo, Perú")
    r.font.name = BODY_FONT
    r.font.size = Pt(9.5)
    r.italic = True

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.0
    r = p.add_run(
        "ORCID: 0009-0005-8303-5480 (R. B. Velasquez Garcia)  ·  "
        "0009-0002-2483-5646 (S. A. Lopez Malca)"
    )
    r.font.name = BODY_FONT
    r.font.size = Pt(8.5)
    r.font.color.rgb = GREY

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(14)
    p.paragraph_format.line_spacing = 1.0
    r = p.add_run("Autor de correspondencia: rbvelasquezga@unitru.edu.pe")
    r.font.name = BODY_FONT
    r.font.size = Pt(8.5)
    r.font.color.rgb = GREY


def add_table(doc: Document, name: str, title: str, note: str, number: int) -> None:
    caption = doc.add_paragraph()
    caption.paragraph_format.space_before = Pt(8)
    caption.paragraph_format.space_after = Pt(3)
    caption.paragraph_format.keep_with_next = True
    caption.paragraph_format.line_spacing = 1.0
    r = caption.add_run(f"Tabla {number}. ")
    r.bold = True
    r.font.name = BODY_FONT
    r.font.size = Pt(9)
    add_runs(caption, title, size=9, bold=False)

    with open(TAB / f"{name}.csv", encoding="utf-8-sig") as fh:
        rows = list(csv.reader(fh))
    ncols = max(len(r) for r in rows)
    table = doc.add_table(rows=len(rows), cols=ncols)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    widths = TABLE_WIDTHS.get(name, [15.0 / ncols] * ncols)
    if len(widths) < ncols:
        widths += [widths[-1]] * (ncols - len(widths))

    for i, row_data in enumerate(rows):
        row = table.rows[i]
        cant_split(row)
        if i == 0:
            repeat_header(row)
        for j in range(ncols):
            cell = row.cells[j]
            cell.width = Cm(widths[j])
            text = row_data[j] if j < len(row_data) else ""
            cell.text = ""
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            p.paragraph_format.line_spacing = 1.0
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if j == 0 else WD_ALIGN_PARAGRAPH.CENTER
            is_panel = text.startswith("Panel")
            add_runs(
                p,
                text,
                size=7.0 if ncols >= 8 else 7.6,
                bold=(i == 0 or is_panel),
            )
            set_cell_border(cell)
            if i == 0:
                shade_cell(cell, HEADER_FILL)
            elif is_panel:
                shade_cell(cell, "EEF2F7")

    note_p = doc.add_paragraph()
    note_p.paragraph_format.space_before = Pt(3)
    note_p.paragraph_format.space_after = Pt(10)
    note_p.paragraph_format.line_spacing = 1.0
    note_p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r = note_p.add_run("Nota. ")
    r.bold = True
    r.font.name = BODY_FONT
    r.font.size = Pt(8)
    r.font.color.rgb = GREY
    add_runs(note_p, note, size=8, color=GREY)


def add_figure(doc: Document, name: str, title: str, note: str, number: int) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    run = p.add_run()
    run.add_picture(str(FIG / f"{name}.png"), width=Cm(FIGURE_WIDTHS.get(name, 15.0)))

    caption = doc.add_paragraph()
    caption.alignment = WD_ALIGN_PARAGRAPH.LEFT
    caption.paragraph_format.space_before = Pt(2)
    caption.paragraph_format.space_after = Pt(2)
    caption.paragraph_format.line_spacing = 1.0
    r = caption.add_run(f"Figura {number}. ")
    r.bold = True
    r.font.name = BODY_FONT
    r.font.size = Pt(9)
    add_runs(caption, title, size=9)

    note_p = doc.add_paragraph()
    note_p.paragraph_format.space_before = Pt(0)
    note_p.paragraph_format.space_after = Pt(10)
    note_p.paragraph_format.line_spacing = 1.0
    note_p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r = note_p.add_run("Nota. ")
    r.bold = True
    r.font.name = BODY_FONT
    r.font.size = Pt(8)
    r.font.color.rgb = GREY
    add_runs(note_p, note, size=8, color=GREY)


def add_body_paragraph(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Cm(0.5)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_runs(p, text)


def add_bullet(doc: Document, text: str) -> None:
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.left_indent = Cm(0.9)
    p.paragraph_format.first_line_indent = Cm(-0.35)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.15
    add_runs(p, text)


def build() -> None:
    text = MD.read_text(encoding="utf-8")
    lines = text.splitlines()
    doc = Document()
    style_document(doc)
    add_title_block(doc)

    table_no = 0
    figure_no = 0
    in_references = False
    paragraph_buffer: list[str] = []
    word_count = 0

    def flush() -> None:
        nonlocal word_count
        if paragraph_buffer:
            body = " ".join(part.strip() for part in paragraph_buffer).strip()
            if body:
                add_body_paragraph(doc, body)
                word_count += len(re.findall(r"\b\w+\b", body))
            paragraph_buffer.clear()

    for raw in lines:
        line = raw.rstrip()
        if not line:
            flush()
            continue

        if line.startswith("## "):
            flush()
            heading = line[3:].strip()
            in_references = heading.lower() == "referencias"
            p = doc.add_paragraph(style="Heading 1")
            add_runs(p, heading, size=12.5, bold=True)
            continue

        if line.startswith("### "):
            flush()
            heading = line[4:].strip()
            p = doc.add_paragraph(style="Heading 2")
            add_runs(p, heading, size=11.5, bold=True)
            continue

        if line.startswith("[[TABLA:"):
            flush()
            inner = line[len("[[TABLA:"):].rstrip("]")
            name, title, note = [part.strip() for part in inner.split("|", 2)]
            table_no += 1
            add_table(doc, name, title, note, table_no)
            continue

        if line.startswith("[[FIGURA:"):
            flush()
            inner = line[len("[[FIGURA:"):].rstrip("]")
            name, title, note = [part.strip() for part in inner.split("|", 2)]
            figure_no += 1
            add_figure(doc, name, title, note, figure_no)
            continue

        if in_references:
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.75)
            p.paragraph_format.first_line_indent = Cm(-0.75)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.line_spacing = 1.0
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            add_runs(p, line, size=9.5)
            word_count += len(re.findall(r"\b\w+\b", line))
            continue

        if line.startswith("- "):
            flush()
            add_bullet(doc, line[2:].strip())
            word_count += len(re.findall(r"\b\w+\b", line[2:]))
            continue

        paragraph_buffer.append(line)

    flush()

    # Metadatos
    props = doc.core_properties
    props.title = (
        "Auditoría continua y de solo lectura del hardening de servidores Linux "
        "basada en controles CIS"
    )
    props.author = "Ricardo Bernardo Velasquez Garcia; Stiven Adrian Lopez Malca"
    props.subject = "Auditoría continua, hardening Linux, CIS Benchmarks"
    props.keywords = (
        "auditoría continua; gestión de configuración de seguridad; CIS Benchmarks; "
        "monitoreo de cumplimiento; exactitud de diagnóstico; Linux"
    )
    props.comments = "Artículo generado a partir de experimento/ y docs/scripts/."

    doc.save(OUT)
    print(f"Guardado: {OUT}")
    print(f"Tablas: {table_no}; figuras: {figure_no}; palabras aproximadas: {word_count}")


if __name__ == "__main__":
    build()
