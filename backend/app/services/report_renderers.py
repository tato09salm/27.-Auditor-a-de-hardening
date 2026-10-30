"""Renderizadores PDF, Word y Excel con una presentación profesional."""

from __future__ import annotations

from copy import copy
from datetime import datetime
from enum import Enum
from uuid import UUID
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

NAVY = colors.HexColor("#0B1220")
CYAN = colors.HexColor("#06B6D4")
SLATE = colors.HexColor("#64748B")
LIGHT = colors.HexColor("#F1F5F9")
RED = colors.HexColor("#DC2626")
AMBER = colors.HexColor("#D97706")
GREEN = colors.HexColor("#059669")

STATUS_LABEL = {
    "passed": "APROBADO",
    "failed": "INCUMPLIDO",
    "not_applicable": "NO APLICA",
    "not_evaluated": "NO EVALUADO",
}
SEVERITY_LABEL = {
    "critical": "Crítica",
    "high": "Alta",
    "medium": "Media",
    "low": "Baja",
    "info": "Informativa",
}


def _score_text(value: float | None) -> str:
    return f"{value:.2f}%" if value is not None else "No calculable"


def _fmt_dt(value: datetime | None) -> str:
    return value.strftime("%Y-%m-%d %H:%M UTC") if value else "-"


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------
def _pdf_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "TitleX", parent=base["Title"], fontName="Helvetica-Bold", fontSize=24,
            textColor=NAVY, spaceAfter=8, leading=29
        ),
        "subtitle": ParagraphStyle(
            "SubX", parent=base["Normal"], fontSize=11, textColor=SLATE, spaceAfter=18
        ),
        "h1": ParagraphStyle(
            "H1X", parent=base["Heading1"], fontName="Helvetica-Bold", fontSize=16,
            textColor=NAVY, spaceBefore=14, spaceAfter=8
        ),
        "h2": ParagraphStyle(
            "H2X", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=11,
            textColor=colors.HexColor("#0E7490"), spaceBefore=10, spaceAfter=5
        ),
        "body": ParagraphStyle(
            "BodyX", parent=base["BodyText"], fontSize=9, leading=12, textColor=colors.HexColor("#1E293B")
        ),
        "small": ParagraphStyle(
            "SmallX", parent=base["BodyText"], fontSize=7.5, leading=9.5, textColor=SLATE
        ),
        "cell": ParagraphStyle(
            "CellX", parent=base["BodyText"], fontSize=7, leading=9,
            textColor=colors.HexColor("#1E293B"), splitLongWords=1
        ),
        "cellbold": ParagraphStyle(
            "CellBX", parent=base["BodyText"], fontSize=7, leading=9,
            fontName="Helvetica-Bold", textColor=NAVY, splitLongWords=1
        ),
        "code": ParagraphStyle(
            "CodeX", parent=base["BodyText"], fontName="Courier", fontSize=7,
            leading=9, textColor=colors.HexColor("#0F172A"), backColor=colors.HexColor("#F8FAFC")
        ),
        "callout": ParagraphStyle(
            "Callout", parent=base["BodyText"], fontSize=8.5, leading=11.5,
            textColor=colors.HexColor("#92400E"), backColor=colors.HexColor("#FFFBEB"),
            borderPadding=7, borderColor=colors.HexColor("#F59E0B"), borderWidth=0.7
        ),
    }


def _pdf_shell(title: str):
    class Doc(BaseDocTemplate):
        def __init__(self, filename: str, **kwargs):
            super().__init__(filename, **kwargs)
            frame = Frame(1.8 * cm, 1.9 * cm, A4[0] - 3.6 * cm, A4[1] - 3.8 * cm, id="normal")
            self.addPageTemplates(
                [PageTemplate(id="main", frames=[frame], onPage=self._decorate)]
            )

        def _decorate(self, canvas, doc):
            canvas.saveState()
            canvas.setFillColor(NAVY)
            canvas.rect(0, A4[1] - 1.15 * cm, A4[0], 1.15 * cm, stroke=0, fill=1)
            canvas.setFillColor(colors.white)
            canvas.setFont("Helvetica-Bold", 8)
            canvas.drawString(1.8 * cm, A4[1] - 0.72 * cm, "CIS HARDENING AUDITOR")
            canvas.setFillColor(colors.HexColor("#94A3B8"))
            canvas.setFont("Helvetica", 7)
            canvas.drawRightString(A4[0] - 1.8 * cm, A4[1] - 0.72 * cm, title[:90])
            canvas.setStrokeColor(colors.HexColor("#E2E8F0"))
            canvas.line(1.8 * cm, 1.35 * cm, A4[0] - 1.8 * cm, 1.35 * cm)
            canvas.setFillColor(SLATE)
            canvas.setFont("Helvetica", 7)
            canvas.drawString(
                1.8 * cm,
                1.0 * cm,
                "Evaluación de configuración. No constituye certificación CIS ni garantía de seguridad.",
            )
            canvas.drawRightString(A4[0] - 1.8 * cm, 1.0 * cm, f"Página {doc.page}")
            canvas.restoreState()

    return Doc


def _table(data, widths, header=True, font=7):
    table = Table(data, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
    ]
    if header:
        commands += [
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), font),
        ]
        for cell in data[0]:
            if isinstance(cell, Paragraph):
                white_style = copy(cell.style)
                white_style.textColor = colors.white
                cell.style = white_style
    table.setStyle(TableStyle(commands))
    return table


def _pdf_cover(story, title: str, subtitle: str, meta: list[tuple[str, str]], score: float | None, styles):
    story.append(Spacer(1, 1.4 * cm))
    story.append(Paragraph("INFORME DE SEGURIDAD", styles["subtitle"]))
    story.append(Paragraph(escape(title), styles["title"]))
    story.append(Paragraph(escape(subtitle), styles["subtitle"]))
    story.append(Spacer(1, 0.4 * cm))
    score_color = "#059669" if (score or 0) >= 80 else ("#D97706" if (score or 0) >= 60 else "#DC2626")
    panel = Table(
        [[
            Paragraph(
                f"<font size='9' color='#64748B'>CUMPLIMIENTO DEL PERFIL</font><br/>"
                f"<font size='30' color='{score_color}'><b>{_score_text(score)}</b></font>",
                styles["body"],
            )
        ]],
        colWidths=[8.2 * cm],
    )
    panel.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )
    story.append(panel)
    story.append(Spacer(1, 0.6 * cm))
    rows = [[Paragraph(k, styles["cellbold"]), Paragraph(escape(v), styles["cell"])] for k, v in meta]
    story.append(_table(rows, [4.0 * cm, 11.4 * cm], header=False))
    story.append(Spacer(1, 0.8 * cm))
    story.append(
        Paragraph(
            "Este documento presenta resultados técnicos de una evaluación autorizada. "
            "No es una certificación oficial de CIS. Los comandos sugeridos por IA, si aparecen, "
            "fueron revisados por una persona y no se ejecutan desde la plataforma.",
            styles["small"],
        )
    )
    story.append(PageBreak())


def render_pdf(data: dict[str, Any], path: Path) -> None:
    styles = _pdf_styles()
    technical = data["report_type"] == "technical"
    title = "Reporte técnico de hardening" if technical else "Reporte ejecutivo de seguridad"
    doc = _pdf_shell(title)(str(path), pagesize=A4, title=title, author="CIS Hardening Auditor")
    story: list[Any] = []
    org = data["organization"].name if data.get("organization") else "-"

    if technical:
        server = data["server"]
        run = data["run"]
        _pdf_cover(
            story,
            "Reporte técnico de hardening",
            f"{server.name} · {server.hostname}",
            [
                ("Organización", org),
                ("Servidor", f"{server.name} ({server.hostname} / {server.ip_address})"),
                ("Sistema operativo", f"{server.os_family} {server.os_version}"),
                ("Entorno", str(server.environment.value)),
                ("Auditoría", f"{run.id}"),
                ("Perfil", f"{data['profile'].name} · {data['benchmark'].name} v{data['benchmark'].version}"),
                ("Fecha de ejecución", _fmt_dt(run.finished_at or run.created_at)),
                ("Generado por", data.get("generated_by", "-")),
                ("Naturaleza", "DATOS SIMULADOS DE PRUEBAS" if data.get("is_simulated") else "Evaluación real"),
            ],
            data.get("score"),
            styles,
        )
        if data.get("is_simulated"):
            story.append(Paragraph(
                "ATENCIÓN: esta ejecución utilizó el conector simulado. Los resultados NO provienen de "
                "infraestructura real y se presentan únicamente como ejemplo de funcionamiento.",
                styles["callout"],
            ))
            story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph("1. Resumen de resultados", styles["h1"]))
        summary = [
            ["Indicador", "Valor"],
            ["Cumplimiento", _score_text(data.get("score"))],
            ["Controles aplicables evaluados", str(run.applicable_count)],
            ["Aprobados", str(run.passed_count)],
            ["Incumplidos", str(run.failed_count)],
            ["No aplicables", str(run.not_applicable_count)],
            ["No evaluados", str(run.not_evaluated_count)],
            ["Cobertura de evaluación", f"{float((run.summary or {}).get('coverage', 0)):.2f}%"],
            ["Hallazgos activos", str(len(data["findings"]))],
        ]
        story.append(
            _table(
                [[Paragraph(str(a), styles["cellbold"]), Paragraph(str(b), styles["cell"])] for a, b in summary],
                [7.0 * cm, 8.4 * cm],
            )
        )
        story.append(Spacer(1, 0.25 * cm))
        story.append(
            Paragraph(
                "Fórmula: aprobados / (aprobados + incumplidos) × 100. Los controles no aplicables y "
                "no evaluados se excluyen del denominador y se informan por separado.",
                styles["small"],
            )
        )
        story.append(Paragraph("2. Resultados por control", styles["h1"]))
        rows = [
            [
                Paragraph("Control", styles["cellbold"]),
                Paragraph("CIS", styles["cellbold"]),
                Paragraph("Severidad", styles["cellbold"]),
                Paragraph("Estado", styles["cellbold"]),
                Paragraph("Resultado observado", styles["cellbold"]),
            ]
        ]
        for item in data["checks"]:
            rows.append(
                [
                    Paragraph(escape(item["title"]), styles["cell"]),
                    Paragraph(escape(item["cis_reference"] or "Interno"), styles["cell"]),
                    Paragraph(SEVERITY_LABEL.get(item["severity"], item["severity"]), styles["cell"]),
                    Paragraph(STATUS_LABEL.get(item["status"], item["status"]), styles["cell"]),
                    Paragraph(escape(item["observed"]), styles["cell"]),
                ]
            )
        story.append(_table(rows, [4.7 * cm, 1.7 * cm, 1.7 * cm, 2.0 * cm, 5.3 * cm]))
        story.append(Paragraph("3. Hallazgos activos", styles["h1"]))
        if data["findings"]:
            rows = [
                [
                    Paragraph("Severidad", styles["cellbold"]),
                    Paragraph("Estado", styles["cellbold"]),
                    Paragraph("Hallazgo", styles["cellbold"]),
                    Paragraph("Vencimiento", styles["cellbold"]),
                ]
            ]
            for finding in data["findings"]:
                rows.append(
                    [
                        Paragraph(SEVERITY_LABEL.get(finding.severity.value, finding.severity.value), styles["cell"]),
                        Paragraph(str(finding.status.value), styles["cell"]),
                        Paragraph(escape(finding.title), styles["cell"]),
                        Paragraph(str(finding.due_date or "-"), styles["cell"]),
                    ]
                )
            story.append(_table(rows, [2.1 * cm, 2.6 * cm, 8.7 * cm, 2.0 * cm]))
        else:
            story.append(Paragraph("No hay hallazgos activos para este servidor.", styles["body"]))

        story.append(Paragraph("4. Recomendaciones aprobadas por revisión humana", styles["h1"]))
        if data["recommendations"]:
            for recommendation in data["recommendations"]:
                payload = recommendation.payload or {}
                block = [
                    Paragraph(escape(payload.get("problem", "Problema no detallado.")), styles["body"]),
                    Paragraph(
                        f"<b>Riesgo:</b> {escape(payload.get('risk', '-'))}",
                        styles["body"],
                    ),
                    Paragraph(
                        f"<b>Recomendación:</b> {escape(payload.get('recommendation', '-'))}",
                        styles["body"],
                    ),
                ]
                for step in payload.get("commands", [])[:6]:
                    block.append(Paragraph(escape(step.get("command", "")), styles["code"]))
                    block.append(Paragraph(escape(step.get("explanation", "")), styles["small"]))
                block.append(
                    Paragraph(
                        "Los comandos son sugerencias revisadas; no fueron ejecutados por la plataforma.",
                        styles["small"],
                    )
                )
                story.append(KeepTogether(block))
                story.append(Spacer(1, 0.25 * cm))
        else:
            story.append(Paragraph("No hay recomendaciones aprobadas para los hallazgos de este servidor.", styles["body"]))

        story.append(Paragraph("5. Evidencia técnica de incumplimientos", styles["h1"]))
        failed = [item for item in data["checks"] if item["status"] == "failed"]
        if failed:
            for item in failed:
                story.append(
                    Paragraph(
                        f"<b>{escape(item['code'])} · {escape(item['title'])}</b>", styles["h2"]
                    )
                )
                story.append(Paragraph(escape(item["observed"]), styles["body"]))
                if item["evidence_excerpt"]:
                    story.append(Paragraph(escape(item["evidence_excerpt"]), styles["code"]))
        else:
            story.append(Paragraph("Sin incumplimientos en los controles evaluados.", styles["body"]))
    else:
        _pdf_cover(
            story,
            "Reporte ejecutivo de seguridad",
            f"{org} · {data['period_start']} a {data['period_end']}",
            [
                ("Organización", org),
                ("Periodo", f"{data['period_start']} a {data['period_end']}"),
                ("Servidores con auditoría", str(len(data["latest_runs"]))),
                ("Generado por", data.get("generated_by", "-")),
                ("Fecha de generación", _fmt_dt(data.get("generated_at"))),
                ("Naturaleza", "INCLUYE DATOS SIMULADOS DE PRUEBAS" if data.get("has_simulated") else "Evaluación real"),
            ],
            data.get("average_score"),
            styles,
        )
        if data.get("has_simulated"):
            story.append(Paragraph(
                "ATENCIÓN: el periodo incluye auditorías con el conector simulado. Esos resultados no "
                "provienen de infraestructura real y están marcados como ejemplos de funcionamiento.",
                styles["callout"],
            ))
            story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph("1. Estado general", styles["h1"]))
        rows = [
            ["Indicador", "Valor"],
            ["Cumplimiento promedio", _score_text(data.get("average_score"))],
            ["Periodo anterior", _score_text(data.get("previous_average"))],
            ["Variación", f"{data['delta']:+.2f} pp" if data.get("delta") is not None else "Sin comparación"],
            ["Cobertura de evaluación", f"{data.get('coverage', 0):.2f}%"],
            ["Hallazgos críticos", str(data["severity_counts"]["critical"])],
            ["Hallazgos altos", str(data["severity_counts"]["high"])],
            ["Hallazgos medios", str(data["severity_counts"]["medium"])],
            ["Hallazgos bajos", str(data["severity_counts"]["low"])],
            ["Servidores evaluados", str(len(data["latest_runs"]))],
        ]
        story.append(
            _table(
                [[Paragraph(str(a), styles["cellbold"]), Paragraph(str(b), styles["cell"])] for a, b in rows],
                [7.0 * cm, 8.4 * cm],
            )
        )
        story.append(Paragraph("2. Evolución del cumplimiento", styles["h1"]))
        if data["trend"]:
            rows = [[Paragraph("Semana", styles["cellbold"]), Paragraph("Cumplimiento", styles["cellbold"])]]
            for point in data["trend"]:
                rows.append([str(point["period"]), _score_text(point["average_score"])])
            story.append(_table(rows, [8.0 * cm, 7.4 * cm]))
        else:
            story.append(Paragraph("No hay datos suficientes para mostrar una tendencia.", styles["body"]))
        story.append(Paragraph("3. Controles que fallan con mayor frecuencia", styles["h1"]))
        if data["top_failures"]:
            rows = [
                [
                    Paragraph("Control", styles["cellbold"]),
                    Paragraph("CIS", styles["cellbold"]),
                    Paragraph("Severidad", styles["cellbold"]),
                    Paragraph("Fallos", styles["cellbold"]),
                    Paragraph("Servidores", styles["cellbold"]),
                ]
            ]
            for item in data["top_failures"]:
                rows.append(
                    [
                        Paragraph(escape(item["title"]), styles["cell"]),
                        Paragraph(escape(item["cis_reference"] or "Interno"), styles["cell"]),
                        Paragraph(SEVERITY_LABEL.get(item["severity"], item["severity"]), styles["cell"]),
                        str(item["failure_count"]),
                        str(item["servers"]),
                    ]
                )
            story.append(_table(rows, [7.2 * cm, 2.0 * cm, 2.4 * cm, 1.6 * cm, 2.2 * cm]))
        story.append(Paragraph("4. Riesgos prioritarios", styles["h1"]))
        if data["riskiest"]:
            for finding in data["riskiest"][:8]:
                story.append(
                    Paragraph(
                        f"<b>{SEVERITY_LABEL.get(finding.severity.value, finding.severity.value)} · "
                        f"{escape(finding.title)}</b> — {escape(finding.server.name if finding.server else '')}. "
                        f"Estado: {escape(finding.status.value)}.",
                        styles["body"],
                    )
                )
        else:
            story.append(Paragraph("No se identificaron riesgos activos en el periodo.", styles["body"]))
        story.append(Paragraph("5. Acciones recomendadas", styles["h1"]))
        if data["actions"]:
            for index, action in enumerate(data["actions"], start=1):
                story.append(Paragraph(f"{index}. {escape(action['title'])}", styles["h2"]))
                story.append(Paragraph(escape(action["guidance"]), styles["body"]))
        else:
            story.append(Paragraph("No hay acciones derivadas de fallos en el periodo.", styles["body"]))

    story.append(Paragraph("Limitaciones de la evaluación", styles["h1"]))
    for limitation in data["limitations"]:
        story.append(Paragraph(f"- {escape(limitation)}", styles["small"]))
    story.append(Spacer(1, 0.4 * cm))
    story.append(
        Paragraph(
            "Documento generado automáticamente por CIS Hardening Auditor. "
            "No contiene contraseñas, claves privadas ni tokens.",
            styles["small"],
        )
    )
    doc.build(story)


# ---------------------------------------------------------------------------
# DOCX
# ---------------------------------------------------------------------------
def _shade(cell, hex_color: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), hex_color)
    tc_pr.append(shd)


def _docx_table(doc: Document, headers: list[str], rows: list[list[str]], widths: list[float] | None = None):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = table.rows[0].cells
    for index, header in enumerate(headers):
        hdr[index].text = ""
        paragraph = hdr[index].paragraphs[0]
        run = paragraph.add_run(header)
        run.bold = True
        run.font.size = Pt(8)
        run.font.color.rgb = RGBColor(255, 255, 255)
        _shade(hdr[index], "0B1220")
    for row in rows:
        cells = table.add_row().cells
        for index, value in enumerate(row):
            cells[index].text = ""
            paragraph = cells[index].paragraphs[0]
            run = paragraph.add_run(str(value))
            run.font.size = Pt(7.5)
    if widths:
        for row in table.rows:
            for index, width in enumerate(widths):
                row.cells[index].width = Cm(width)
    return table


def _docx_header_footer(doc: Document, title: str) -> None:
    section = doc.sections[0]
    header = section.header
    paragraph = header.paragraphs[0]
    paragraph.text = f"CIS HARDENING AUDITOR  |  {title}"
    paragraph.style = doc.styles["Normal"]
    for run in paragraph.runs:
        run.font.size = Pt(7.5)
        run.font.color.rgb = RGBColor(100, 116, 139)
    footer = section.footer.paragraphs[0]
    footer.text = (
        "Evaluación de configuración. No constituye certificación CIS ni garantía de seguridad. "
        "No contiene secretos."
    )
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in footer.runs:
        run.font.size = Pt(7)
        run.font.color.rgb = RGBColor(100, 116, 139)


def render_docx(data: dict[str, Any], path: Path) -> None:
    technical = data["report_type"] == "technical"
    title = "Reporte técnico de hardening" if technical else "Reporte ejecutivo de seguridad"
    doc = Document()
    section = doc.sections[0]
    section.page_height = Cm(29.7)
    section.page_width = Cm(21.0)
    section.top_margin = Cm(1.8)
    section.bottom_margin = Cm(1.8)
    section.left_margin = Cm(1.7)
    section.right_margin = Cm(1.7)
    styles = doc.styles
    styles["Normal"].font.name = "Calibri"
    styles["Normal"].font.size = Pt(9)
    _docx_header_footer(doc, title)
    doc.core_properties.title = title
    doc.core_properties.author = "CIS Hardening Auditor"

    header = doc.add_paragraph()
    run = header.add_run("INFORME DE SEGURIDAD")
    run.font.size = Pt(8)
    run.font.color.rgb = RGBColor(6, 182, 212)
    run.bold = True
    h = doc.add_heading(title, level=0)
    h.style.font.color.rgb = RGBColor(11, 18, 32)
    org = data["organization"].name if data.get("organization") else "-"

    if technical:
        server = data["server"]
        run_data = data["run"]
        doc.add_paragraph(f"{server.name} · {server.hostname} · {server.ip_address}")
        table = doc.add_table(rows=0, cols=2)
        table.style = "Table Grid"
        meta = [
            ("Organización", org),
            ("Sistema operativo", f"{server.os_family} {server.os_version}"),
            ("Entorno", server.environment.value),
            ("Perfil", f"{data['profile'].name} · {data['benchmark'].name} v{data['benchmark'].version}"),
            ("Auditoría", str(run_data.id)),
            ("Fecha", _fmt_dt(run_data.finished_at or run_data.created_at)),
            ("Generado por", data.get("generated_by", "-")),
            ("Cumplimiento", _score_text(data.get("score"))),
            ("Naturaleza", "DATOS SIMULADOS DE PRUEBAS" if data.get("is_simulated") else "Evaluación real"),
        ]
        for key, value in meta:
            cells = table.add_row().cells
            cells[0].text = key
            cells[1].text = value
            cells[0].paragraphs[0].runs[0].bold = True
            _shade(cells[0], "F1F5F9")
        if data.get("is_simulated"):
            doc.add_paragraph(
                "ATENCIÓN: esta ejecución utilizó el conector simulado. Los resultados no provienen de "
                "infraestructura real y se presentan únicamente como ejemplo."
            )
        doc.add_heading("1. Resumen de resultados", level=1)
        doc.add_paragraph(
            "Fórmula: aprobados / (aprobados + incumplidos) × 100. No aplicables y no evaluados "
            "se excluyen del denominador y se muestran por separado."
        )
        _docx_table(
            doc,
            ["Indicador", "Valor"],
            [
                ["Aprobados", str(run_data.passed_count)],
                ["Incumplidos", str(run_data.failed_count)],
                ["No aplicables", str(run_data.not_applicable_count)],
                ["No evaluados", str(run_data.not_evaluated_count)],
                ["Cobertura", f"{float((run_data.summary or {}).get('coverage', 0)):.2f}%"],
                ["Hallazgos activos", str(len(data["findings"]))],
            ],
            [7.5, 8.0],
        )
        doc.add_heading("2. Resultados por control", level=1)
        _docx_table(
            doc,
            ["Control", "CIS", "Severidad", "Estado", "Observado"],
            [
                [
                    item["title"],
                    item["cis_reference"] or "Interno",
                    SEVERITY_LABEL.get(item["severity"], item["severity"]),
                    STATUS_LABEL.get(item["status"], item["status"]),
                    item["observed"],
                ]
                for item in data["checks"]
            ],
            [4.7, 1.7, 1.8, 2.0, 5.2],
        )
        doc.add_heading("3. Hallazgos activos", level=1)
        if data["findings"]:
            _docx_table(
                doc,
                ["Severidad", "Estado", "Hallazgo", "Vence"],
                [
                    [
                        SEVERITY_LABEL.get(f.severity.value, f.severity.value),
                        f.status.value,
                        f.title,
                        str(f.due_date or "-"),
                    ]
                    for f in data["findings"]
                ],
                [2.2, 2.6, 9.0, 2.0],
            )
        else:
            doc.add_paragraph("No hay hallazgos activos.")
        doc.add_heading("4. Recomendaciones aprobadas", level=1)
        if data["recommendations"]:
            for recommendation in data["recommendations"]:
                payload = recommendation.payload or {}
                doc.add_heading(payload.get("problem", "Recomendación")[:120], level=2)
                doc.add_paragraph(f"Riesgo: {payload.get('risk', '-')}")
                doc.add_paragraph(f"Recomendación: {payload.get('recommendation', '-')}")
                for step in payload.get("commands", [])[:6]:
                    p = doc.add_paragraph()
                    r = p.add_run(step.get("command", ""))
                    r.font.name = "Consolas"
                    r.font.size = Pt(8)
                    doc.add_paragraph(step.get("explanation", ""))
        else:
            doc.add_paragraph("No hay recomendaciones aprobadas.")
        doc.add_heading("5. Evidencia de incumplimientos", level=1)
        for item in [item for item in data["checks"] if item["status"] == "failed"]:
            doc.add_heading(f"{item['code']} · {item['title']}", level=2)
            doc.add_paragraph(item["observed"])
            if item["evidence_excerpt"]:
                p = doc.add_paragraph()
                r = p.add_run(item["evidence_excerpt"][:3000])
                r.font.name = "Consolas"
                r.font.size = Pt(7)
    else:
        doc.add_paragraph(f"{org} · {data['period_start']} a {data['period_end']}")
        if data.get("has_simulated"):
            doc.add_paragraph(
                "ATENCIÓN: el periodo incluye auditorías simuladas. Los resultados no provienen de "
                "infraestructura real y están marcados como ejemplos."
            )
        doc.add_heading("1. Estado general", level=1)
        _docx_table(
            doc,
            ["Indicador", "Valor"],
            [
                ["Cumplimiento promedio", _score_text(data.get("average_score"))],
                ["Periodo anterior", _score_text(data.get("previous_average"))],
                ["Variación", f"{data['delta']:+.2f} pp" if data.get("delta") is not None else "Sin comparación"],
                ["Cobertura", f"{data.get('coverage', 0):.2f}%"],
                ["Críticos", str(data["severity_counts"]["critical"])],
                ["Altos", str(data["severity_counts"]["high"])],
                ["Medios", str(data["severity_counts"]["medium"])],
                ["Bajos", str(data["severity_counts"]["low"])],
                ["Servidores evaluados", str(len(data["latest_runs"]))],
            ],
            [8.0, 8.0],
        )
        doc.add_heading("2. Evolución", level=1)
        if data["trend"]:
            _docx_table(
                doc,
                ["Semana", "Cumplimiento"],
                [[str(p["period"]), _score_text(p["average_score"])] for p in data["trend"]],
                [8.0, 8.0],
            )
        doc.add_heading("3. Controles con más fallos", level=1)
        if data["top_failures"]:
            _docx_table(
                doc,
                ["Control", "CIS", "Severidad", "Fallos", "Servidores"],
                [
                    [
                        item["title"],
                        item["cis_reference"] or "Interno",
                        SEVERITY_LABEL.get(item["severity"], item["severity"]),
                        str(item["failure_count"]),
                        str(item["servers"]),
                    ]
                    for item in data["top_failures"]
                ],
                [7.0, 2.0, 2.2, 1.6, 2.0],
            )
        doc.add_heading("4. Riesgos prioritarios", level=1)
        for finding in data["riskiest"][:8]:
            doc.add_paragraph(
                f"[{SEVERITY_LABEL.get(finding.severity.value, finding.severity.value)}] "
                f"{finding.title} — {finding.server.name if finding.server else ''} "
                f"({finding.status.value})"
            )
        doc.add_heading("5. Acciones recomendadas", level=1)
        for index, action in enumerate(data["actions"], start=1):
            doc.add_heading(f"{index}. {action['title']}", level=2)
            doc.add_paragraph(action["guidance"])

    doc.add_heading("Limitaciones", level=1)
    for limitation in data["limitations"]:
        doc.add_paragraph(limitation, style="List Bullet")
    doc.save(str(path))


# ---------------------------------------------------------------------------
# XLSX
# ---------------------------------------------------------------------------
EXCEL_HEADER_FILL = PatternFill("solid", fgColor="0B1220")
EXCEL_HEADER_FONT = Font(color="FFFFFF", bold=True, size=10)
EXCEL_ALT = PatternFill("solid", fgColor="F1F5F9")
EXCEL_BORDER = Border(
    left=Side(style="thin", color="CBD5E1"),
    right=Side(style="thin", color="CBD5E1"),
    top=Side(style="thin", color="CBD5E1"),
    bottom=Side(style="thin", color="CBD5E1"),
)


def _excel_safe(value: Any) -> Any:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, str) and value[:1] in {"=", "+", "-", "@"}:
        return "'" + value
    return value


def _sheet(wb: Workbook, title: str, headers: list[str], rows: list[list[Any]], widths: list[int]):
    ws = wb.create_sheet(title=title[:31])
    ws.append([_excel_safe(value) for value in headers])
    for cell in ws[1]:
        cell.fill = EXCEL_HEADER_FILL
        cell.font = EXCEL_HEADER_FONT
        cell.alignment = Alignment(vertical="center", wrap_text=True)
        cell.border = EXCEL_BORDER
    for row in rows:
        ws.append([_excel_safe(value) for value in row])
    for row_idx in range(2, ws.max_row + 1):
        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.border = EXCEL_BORDER
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            if row_idx % 2 == 0:
                cell.fill = EXCEL_ALT
    for index, width in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(index)].width = width
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    ws.sheet_view.showGridLines = False
    return ws


def render_xlsx(data: dict[str, Any], path: Path) -> None:
    technical = data["report_type"] == "technical"
    wb = Workbook()
    summary = wb.active
    summary.title = "Resumen"
    summary.sheet_view.showGridLines = False
    summary["A1"] = "CIS HARDENING AUDITOR"
    summary["A1"].font = Font(size=16, bold=True, color="0B1220")
    summary["A2"] = "Reporte técnico de hardening" if technical else "Reporte ejecutivo de seguridad"
    summary["A2"].font = Font(size=12, color="0E7490")
    summary["A4"] = "Organización"
    summary["B4"] = _excel_safe(data["organization"].name if data.get("organization") else "-")
    summary["A5"] = "Generado"
    summary["B5"] = data["generated_at"].strftime("%Y-%m-%d %H:%M UTC")
    summary["A6"] = "Generado por"
    summary["B6"] = _excel_safe(data.get("generated_by", "-"))
    summary["A8"] = "Naturaleza"
    summary["B8"] = (
        "Datos simulados de pruebas"
        if (data.get("is_simulated") or data.get("has_simulated"))
        else "Evaluación real"
    )
    summary["B8"].font = Font(bold=True, color="B45309" if (data.get("is_simulated") or data.get("has_simulated")) else "047857")
    summary["A9"] = "Limitaciones"
    summary["A9"].font = Font(bold=True)
    for index, limitation in enumerate(data["limitations"], start=10):
        summary[f"A{index}"] = _excel_safe(limitation)
        summary.merge_cells(start_row=index, start_column=1, end_row=index, end_column=4)
        summary[f"A{index}"].alignment = Alignment(wrap_text=True)
    summary.column_dimensions["A"].width = 32
    summary.column_dimensions["B"].width = 60

    if technical:
        server = data["server"]
        run_data = data["run"]
        summary["A3"] = _excel_safe(f"{server.name} · {server.hostname}")
        summary["A7"] = "Cumplimiento"
        summary["B7"] = _score_text(data.get("score"))
        summary["B7"].font = Font(bold=True, size=14, color="059669" if (data.get("score") or 0) >= 80 else "D97706")
        _sheet(
            wb,
            "Resumen ejecutivo",
            ["Indicador", "Valor"],
            [
                ["Servidor", server.name],
                ["Hostname", server.hostname],
                ["IP", server.ip_address],
                ["SO", f"{server.os_family} {server.os_version}"],
                ["Entorno", server.environment.value],
                ["Perfil", data["profile"].name],
                ["Benchmark", f"{data['benchmark'].name} v{data['benchmark'].version}"],
                ["Auditoría", str(run_data.id)],
                ["Fecha", _fmt_dt(run_data.finished_at or run_data.created_at)],
                ["Cumplimiento", _score_text(data.get("score"))],
                ["Aprobados", run_data.passed_count],
                ["Incumplidos", run_data.failed_count],
                ["No aplicables", run_data.not_applicable_count],
                ["No evaluados", run_data.not_evaluated_count],
                ["Cobertura", float((run_data.summary or {}).get("coverage", 0))],
            ],
            [32, 70],
        )
        _sheet(
            wb,
            "Controles",
            ["Código", "CIS", "Control", "Categoría", "Severidad", "Estado", "Observado", "Evidencia", "Guía"],
            [
                [
                    item["code"],
                    item["cis_reference"] or "Interno",
                    item["title"],
                    item["category"],
                    SEVERITY_LABEL.get(item["severity"], item["severity"]),
                    STATUS_LABEL.get(item["status"], item["status"]),
                    item["observed"],
                    item["evidence_excerpt"],
                    item["guidance"],
                ]
                for item in data["checks"]
            ],
            [14, 12, 42, 20, 12, 14, 45, 80, 55],
        )
        _sheet(
            wb,
            "Hallazgos",
            ["Severidad", "Estado", "Hallazgo", "Responsable", "Vence", "Ocurrencias", "Última detección"],
            [
                [
                    SEVERITY_LABEL.get(f.severity.value, f.severity.value),
                    f.status.value,
                    f.title,
                    f.owner_id or "",
                    str(f.due_date or ""),
                    f.occurrence_count,
                    _fmt_dt(f.last_seen_at),
                ]
                for f in data["findings"]
            ],
            [14, 20, 55, 38, 14, 12, 24],
        )
        _sheet(
            wb,
            "Recomendaciones",
            ["Estado", "Problema", "Riesgo", "Recomendación", "Comandos", "Revisado por", "Revisado"],
            [
                [
                    r.status.value,
                    (r.payload or {}).get("problem", ""),
                    (r.payload or {}).get("risk", ""),
                    (r.payload or {}).get("recommendation", ""),
                    "\n".join(step.get("command", "") for step in (r.payload or {}).get("commands", [])),
                    r.reviewed_by_id or "",
                    _fmt_dt(r.reviewed_at),
                ]
                for r in data["recommendations"]
            ],
            [20, 55, 40, 65, 60, 38, 22],
        )
    else:
        summary["A3"] = _excel_safe(f"{data['period_start']} a {data['period_end']}")
        summary["A7"] = "Cumplimiento promedio"
        summary["B7"] = _score_text(data.get("average_score"))
        summary["B7"].font = Font(bold=True, size=14, color="059669" if (data.get("average_score") or 0) >= 80 else "D97706")
        _sheet(
            wb,
            "Resumen ejecutivo",
            ["Indicador", "Valor"],
            [
                ["Periodo", f"{data['period_start']} a {data['period_end']}"],
                ["Cumplimiento promedio", _score_text(data.get("average_score"))],
                ["Periodo anterior", _score_text(data.get("previous_average"))],
                ["Variación (pp)", data.get("delta")],
                ["Cobertura", data.get("coverage", 0)],
                ["Críticos", data["severity_counts"]["critical"]],
                ["Altos", data["severity_counts"]["high"]],
                ["Medios", data["severity_counts"]["medium"]],
                ["Bajos", data["severity_counts"]["low"]],
                ["Servidores evaluados", len(data["latest_runs"])],
            ],
            [32, 60],
        )
        _sheet(
            wb,
            "Tendencia",
            ["Semana", "Cumplimiento"],
            [[str(point["period"]), point["average_score"]] for point in data["trend"]],
            [16, 18],
        )
        _sheet(
            wb,
            "Controles con fallos",
            ["Control", "CIS", "Severidad", "Fallos", "Servidores afectados"],
            [
                [
                    item["title"],
                    item["cis_reference"] or "Interno",
                    SEVERITY_LABEL.get(item["severity"], item["severity"]),
                    item["failure_count"],
                    item["servers"],
                ]
                for item in data["top_failures"]
            ],
            [55, 12, 14, 10, 18],
        )
        _sheet(
            wb,
            "Riesgos",
            ["Severidad", "Hallazgo", "Servidor", "Estado", "Última detección"],
            [
                [
                    SEVERITY_LABEL.get(f.severity.value, f.severity.value),
                    f.title,
                    f.server.name if f.server else "",
                    f.status.value,
                    _fmt_dt(f.last_seen_at),
                ]
                for f in data["riskiest"]
            ],
            [14, 55, 28, 20, 22],
        )
        _sheet(
            wb,
            "Acciones",
            ["Control", "Guía de corrección", "Fallos"],
            [[a["title"], a["guidance"], a["failures"]] for a in data["actions"]],
            [45, 90, 10],
        )

    wb.save(str(path))
