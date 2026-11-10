"""Renderizado de tablas y figuras en formatos de alta calidad."""

from __future__ import annotations

import io
import json
import math
import textwrap
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, Patch
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus import LongTable
from xml.sax.saxutils import escape

from publication.model import (
    SEVERITY_LABEL,
    SEVERITY_ORDER,
    STATUS_LABEL,
    STATUS_ORDER,
    Dataset,
    FigureSpec,
    TableSpec,
)

NAVY = "#0B1220"
INK = "#172033"
CYAN = "#06B6D4"
TEAL = "#0E7490"
SLATE = "#64748B"
LIGHT = "#F1F5F9"
LINE = "#DCE3ED"
WHITE = "#FFFFFF"
GREEN = "#059669"
AMBER = "#D97706"
ORANGE = "#EA580C"
RED = "#DC2626"
BLUE = "#2563EB"
VIOLET = "#7C3AED"
PINK = "#DB2777"

SEVERITY_COLORS = {
    "critical": RED,
    "high": ORANGE,
    "medium": AMBER,
    "low": BLUE,
    "info": SLATE,
}
STATUS_COLORS = {
    "detected": RED,
    "in_review": "#F59E0B",
    "correction_planned": BLUE,
    "fixed_pending_validation": CYAN,
    "risk_accepted": VIOLET,
    "resolved": GREEN,
    "false_positive": "#94A3B8",
}

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.edgecolor": LINE,
        "axes.labelcolor": SLATE,
        "axes.titlecolor": NAVY,
        "xtick.color": SLATE,
        "ytick.color": SLATE,
        "text.color": INK,
        "figure.facecolor": WHITE,
        "savefig.facecolor": WHITE,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)


# ---------------------------------------------------------------------------
# Composición de figuras
# ---------------------------------------------------------------------------
def _frame(
    spec: FigureSpec,
    figsize: tuple[float, float] = (11.5, 6.9),
    bottom: float = 0.15,
) -> plt.Figure:
    fig = plt.figure(figsize=figsize, facecolor=WHITE)
    fig.text(
        0.045,
        0.965,
        spec.full_title,
        fontsize=14.2,
        fontweight="bold",
        color=NAVY,
        ha="left",
        va="top",
    )
    fig.text(
        0.955,
        0.968,
        "CIS HARDENING AUDITOR · ANEXO EDITORIAL",
        fontsize=6.8,
        color=SLATE,
        ha="right",
        va="top",
    )
    fig.add_artist(
        Line2D([0.045, 0.955], [0.925, 0.925], transform=fig.transFigure, color=CYAN, lw=1.2)
    )
    note = textwrap.fill(spec.notes, width=158)
    fig.text(0.045, 0.022, note, fontsize=6.4, color=SLATE, ha="left", va="bottom", linespacing=1.3)
    fig.subplots_adjust(top=0.885, bottom=bottom, left=0.09, right=0.96)
    return fig


def _empty_message(ax: plt.Axes, message: str) -> None:
    ax.axis("off")
    ax.text(0.5, 0.5, message, ha="center", va="center", color=SLATE, fontsize=10)


def _draw_architecture(spec: FigureSpec) -> plt.Figure:
    fig = _frame(spec, figsize=(11.8, 7.25), bottom=0.09)
    ax = fig.add_axes([0.035, 0.08, 0.93, 0.81])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    def box(
        x: float,
        y: float,
        w: float,
        h: float,
        title: str,
        subtitle: str,
        face: str,
        edge: str = LINE,
        title_color: str = NAVY,
        subtitle_color: str = SLATE,
        size: float = 8.6,
    ) -> None:
        patch = FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.42,rounding_size=1.6",
            linewidth=1,
            edgecolor=edge,
            facecolor=face,
            zorder=2,
        )
        ax.add_patch(patch)
        ax.text(x + w / 2, y + h * 0.64, title, ha="center", va="center", fontsize=size, fontweight="bold", color=title_color, zorder=3)
        ax.text(x + w / 2, y + h * 0.31, subtitle, ha="center", va="center", fontsize=size - 1.4, color=subtitle_color, zorder=3, linespacing=1.25)

    def arrow(
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        *,
        dashed: bool = False,
        label: str | None = None,
        rad: float = 0.0,
    ) -> None:
        ax.annotate(
            "",
            xy=(x2, y2),
            xytext=(x1, y1),
            arrowprops={
                "arrowstyle": "-|>",
                "lw": 1.45,
                "color": TEAL if not dashed else SLATE,
                "linestyle": "--" if dashed else "-",
                "shrinkA": 2,
                "shrinkB": 2,
                "connectionstyle": f"arc3,rad={rad}",
            },
            zorder=1,
        )
        if label:
            ax.text(
                (x1 + x2) / 2,
                (y1 + y2) / 2 + 1.8,
                label,
                ha="center",
                va="bottom",
                fontsize=6.5,
                color=SLATE,
                bbox={"boxstyle": "round,pad=0.2", "fc": WHITE, "ec": "none", "alpha": 0.9},
                zorder=4,
            )

    # Capa de aplicación
    box(1, 71, 18, 15, "Usuarios", "Auditor · Analista\nAdministrador · Observador", "#ECFEFF", "#A5F3FC", TEAL)
    box(23, 71, 17, 15, "React SPA", "Consola de hardening\nresponsive", "#F8FAFC", LINE)
    box(44, 71, 18, 15, "FastAPI", "RBAC · validación\norquestación", "#ECFDF5", "#A7F3D0", "#065F46")
    box(66, 71, 20, 15, "PostgreSQL", "evidencia · hallazgos\nbitácora append-only", "#EFF6FF", "#BFDBFE", "#1E40AF")

    # Automatización y motor
    box(23, 53, 17, 10, "n8n", "programación\nAPI key con scope", "#F5F3FF", "#DDD6FE", "#5B21B6", size=8)
    box(44, 53, 18, 10, "Audit worker", "checks de solo lectura", "#F8FAFC", LINE, size=8)
    box(66, 53, 20, 10, "Servidor Linux", "objetivo autorizado", "#FFF7ED", "#FED7AA", "#9A3412", size=8)

    # Resultados auxiliares
    box(2, 32, 19, 11, "LangChain + Ollama", "propuesta JSON opcional\nsin herramientas", "#FAF5FF", "#E9D5FF", "#6B21A8", size=7.7)
    box(24, 32, 20, 11, "Revisión humana", "aprobar o rechazar\ncon comentario", "#F0FDF4", "#BBF7D0", "#166534", size=7.7)
    box(47, 32, 18, 11, "Reportes", "PDF · DOCX · XLSX\nchecksum SHA-256", "#F8FAFC", LINE, size=7.7)
    box(70, 32, 17, 11, "Anexo Streamlit", "6 tablas · 6 figuras\ndescarga editorial", "#ECFEFF", "#A5F3FC", TEAL, size=7.7)

    arrow(19, 78.5, 23, 78.5)
    arrow(40, 78.5, 44, 78.5)
    arrow(62, 78.5, 66, 78.5)
    arrow(40, 58, 44, 71, dashed=True, label="API key")
    arrow(53, 71, 53, 63)
    arrow(62, 58, 66, 58, label="SSH")
    arrow(21, 37.5, 24, 37.5, dashed=True, label="propuesta")

    # Flujo editorial inferior
    ax.add_patch(
        FancyBboxPatch(
            (1, 5),
            96,
            19,
            boxstyle="round,pad=0.35,rounding_size=1.3",
            facecolor="#F8FAFC",
            edgecolor=LINE,
            zorder=0,
        )
    )
    steps = [
        ("1", "Autorizar", "servidor y alcance"),
        ("2", "Comprobar", "SSH de solo lectura"),
        ("3", "Puntuar", "score y cobertura"),
        ("4", "Gestionar", "hallazgos y evidencia"),
        ("5", "Asistir", "IA + revisión humana"),
        ("6", "Entregar", "reportes y bitácora"),
    ]
    step_w = 13.2
    for index, (number, title, subtitle) in enumerate(steps):
        x = 3 + index * 15.3
        ax.add_patch(
            FancyBboxPatch(
                (x, 8),
                step_w,
                11,
                boxstyle="round,pad=0.25,rounding_size=0.9",
                facecolor=WHITE,
                edgecolor=LINE,
                zorder=2,
            )
        )
        ax.add_patch(plt.Circle((x + 3.2, 15.5), 1.35, color=CYAN, zorder=3))
        ax.text(x + 3.2, 15.5, number, ha="center", va="center", fontsize=6.5, fontweight="bold", color=NAVY, zorder=4)
        ax.text(x + 5.4, 15.7, title, ha="left", va="center", fontsize=7.2, fontweight="bold", color=NAVY, zorder=4)
        ax.text(x + 1.2, 11.7, subtitle, ha="left", va="center", fontsize=5.9, color=SLATE, zorder=4)
        if index < len(steps) - 1:
            ax.annotate(
                "",
                xy=(x + step_w + 1.35, 13.5),
                xytext=(x + step_w + 0.25, 13.5),
                arrowprops={"arrowstyle": "-|>", "lw": 1, "color": "#94A3B8"},
                zorder=1,
            )

    ax.text(
        1.5,
        0.6,
        "Sólido: flujo síncrono   ·   Punteado: componente opcional o automatizado   ·   La IA nunca ejecuta comandos",
        fontsize=5.9,
        color=SLATE,
        ha="left",
        va="bottom",
    )
    return fig


def _draw_score_coverage(spec: FigureSpec) -> plt.Figure:
    fig = _frame(spec, figsize=(11.5, 6.7), bottom=0.17)
    ax = fig.add_subplot(111)
    data = spec.data.dropna(subset=["score"]).sort_values("score", ascending=True)
    if data.empty:
        _empty_message(ax, "Sin ejecuciones completadas para graficar.")
        return fig
    y = np.arange(len(data))
    colors = [
        GREEN if value >= 80 else (AMBER if value >= 60 else RED) for value in data["score"]
    ]
    ax.barh(y + 0.16, data["coverage"], height=0.34, color="#DCE6F2", edgecolor="none", label="Cobertura")
    ax.barh(y - 0.16, data["score"], height=0.34, color=colors, edgecolor="none", label="Cumplimiento")
    for index, row in enumerate(data.itertuples()):
        ax.text(row.score + 1.5, index - 0.16, f"{row.score:.1f}%", va="center", fontsize=7.2, color=NAVY, fontweight="bold")
        ax.text(row.coverage + 1.5, index + 0.16, f"{row.coverage:.0f}%", va="center", fontsize=6.4, color=SLATE)
    ax.axvline(80, color=SLATE, linestyle=(0, (4, 3)), lw=0.9, alpha=0.65)
    ax.text(80.6, len(data) - 0.35, "referencia 80 %", fontsize=6.3, color=SLATE, va="top")
    ax.set_yticks(y)
    ax.set_yticklabels(data["server_name"], fontsize=8.2)
    ax.set_xlim(0, 108)
    ax.set_xlabel("Porcentaje (0–100)")
    ax.grid(axis="x", color="#EEF2F7", lw=0.8)
    ax.set_axisbelow(True)
    ax.legend(loc="lower right", frameon=False, fontsize=7.5, ncol=2)
    return fig


def _draw_trend(spec: FigureSpec) -> plt.Figure:
    fig = _frame(spec, figsize=(11.5, 7.1), bottom=0.14)
    data = spec.data.dropna(subset=["score"]).copy()
    if data.empty:
        ax = fig.add_subplot(111)
        _empty_message(ax, "Sin ejecuciones completadas para graficar.")
        return fig
    data["run_date"] = pd.to_datetime(data["run_date"])
    latest = data.sort_values("run_date").groupby("server_name").tail(1)
    order = latest.sort_values("score")["server_name"].tolist()
    if len(order) > 8:
        order = order[:8]
    data = data[data["server_name"].isin(order)]
    ncols = 4
    nrows = max(1, math.ceil(len(order) / ncols))
    axes = fig.subplots(nrows, ncols, sharey=True)
    if nrows == 1 and ncols == 1:
        axes = np.array([axes])
    axes = np.array(axes).reshape(-1)
    for index, server in enumerate(order):
        ax = axes[index]
        subset = data[data["server_name"] == server].sort_values("run_date")
        month_names = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
        positions = np.arange(len(subset))
        ax.plot(positions, subset["score"], color=TEAL, lw=1.8, marker="o", ms=4.2, mfc=WHITE, mew=1.5)
        ax.axhline(80, color="#94A3B8", ls=(0, (3, 3)), lw=0.8)
        ax.set_ylim(0, 105)
        ax.set_xlim(-0.2, max(0.2, len(subset) - 0.8))
        ax.set_title(server, fontsize=7.8, loc="left", color=NAVY, pad=5)
        ax.set_xticks(positions)
        ax.set_xticklabels([month_names[date.month - 1] for date in subset["run_date"]], fontsize=6)
        ax.tick_params(axis="y", labelsize=6)
        ax.grid(axis="y", color="#EEF2F7", lw=0.7)
        ax.set_axisbelow(True)
        if subset["score"].notna().any():
            last = subset.dropna(subset=["score"]).iloc[-1]
            ax.annotate(
                f"{last['score']:.0f}%",
                xy=(positions[-1], last["score"]),
                xytext=(4, 4),
                textcoords="offset points",
                fontsize=6.2,
                color=NAVY,
            )
    for index in range(len(order), len(axes)):
        axes[index].axis("off")
    return fig


def _draw_control_rate(spec: FigureSpec) -> plt.Figure:
    fig = _frame(spec, figsize=(11.5, 7.25), bottom=0.17)
    ax = fig.add_subplot(111)
    data = spec.data.dropna(subset=["pass_rate"]).sort_values("pass_rate", ascending=True)
    if data.empty:
        _empty_message(ax, "Sin controles evaluados para graficar.")
        return fig
    y = np.arange(len(data))
    colors = [SEVERITY_COLORS.get(severity, SLATE) for severity in data["severity"]]
    for index, row in enumerate(data.itertuples()):
        ax.plot([0, row.pass_rate], [index, index], color="#DCE6F2", lw=2, zorder=1)
        ax.scatter(
            row.pass_rate,
            index,
            s=22 + min(90, row.applicable * 1.4),
            color=SEVERITY_COLORS.get(row.severity, SLATE),
            edgecolor=WHITE,
            linewidth=0.8,
            zorder=3,
        )
        ax.text(row.pass_rate + 2.2, index, f"{row.pass_rate:.1f}%  (n={int(row.applicable)})", va="center", fontsize=6.7, color=NAVY)
    labels = [
        f"{code} (I)" if not official else code
        for code, official in zip(data["control_code"], data["official"], strict=True)
    ]
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=7.2, family="DejaVu Sans")
    ax.set_xlim(0, 108)
    ax.set_xlabel("Tasa de aprobación sobre controles evaluados (%)")
    ax.grid(axis="x", color="#EEF2F7", lw=0.8)
    ax.set_axisbelow(True)
    legend_handles = [
        Patch(facecolor=SEVERITY_COLORS[severity], label=label)
        for severity, label in [("high", "Alta"), ("medium", "Media"), ("low", "Baja")]
    ]
    ax.legend(handles=legend_handles, loc="lower right", frameon=False, fontsize=7, title="Severidad", title_fontsize=7)
    return fig


def _draw_findings(spec: FigureSpec) -> plt.Figure:
    fig = _frame(spec, figsize=(11.5, 6.9), bottom=0.22)
    ax = fig.add_subplot(111)
    data = spec.data.copy()
    if data.empty:
        _empty_message(ax, "Sin hallazgos para graficar.")
        return fig
    pivot = (
        data.pivot_table(index="severity", columns="status", values="count", aggfunc="sum", fill_value=0)
        .reindex(SEVERITY_ORDER, fill_value=0)
        .reindex(columns=STATUS_ORDER, fill_value=0)
    )
    y = np.arange(len(pivot))
    left = np.zeros(len(pivot))
    for status in STATUS_ORDER:
        values = pivot[status].to_numpy()
        ax.barh(
            y,
            values,
            left=left,
            color=STATUS_COLORS[status],
            edgecolor=WHITE,
            linewidth=0.8,
            label=STATUS_LABEL[status],
        )
        left += values
    for index, total in enumerate(left):
        ax.text(total + 0.7, index, f"{int(total)}", va="center", fontsize=7.5, color=NAVY, fontweight="bold")
    ax.set_yticks(y)
    ax.set_yticklabels([SEVERITY_LABEL[level] for level in pivot.index], fontsize=8.4)
    ax.invert_yaxis()
    ax.set_xlabel("Hallazgos únicos")
    ax.set_xlim(0, max(1, left.max()) * 1.15)
    ax.grid(axis="x", color="#EEF2F7", lw=0.8)
    ax.set_axisbelow(True)
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.18),
        ncol=4,
        frameon=False,
        fontsize=6.9,
        handlelength=1.0,
        columnspacing=1.1,
    )
    return fig


def _draw_heatmap(spec: FigureSpec) -> plt.Figure:
    fig = _frame(spec, figsize=(11.8, 6.4), bottom=0.22)
    ax = fig.add_subplot(111)
    data = spec.data.copy()
    if data.empty:
        _empty_message(ax, "Sin datos para el mapa de calor.")
        return fig
    matrix = data.pivot(index="server_name", columns="category", values="pass_rate")
    matrix = matrix.sort_index()
    if len(matrix) > 10:
        matrix = matrix.iloc[:10]
    values = matrix.to_numpy(dtype=float)
    image = ax.imshow(values, cmap="YlGnBu", vmin=0, vmax=100, aspect="auto")
    short_categories = {
        "Actualizaciones": "Parches",
        "Hardening del kernel": "Kernel",
        "Permisos de archivos": "Permisos",
        "Registro de eventos": "Registro",
    }
    ax.set_xticks(np.arange(matrix.shape[1]))
    ax.set_xticklabels(
        [
            textwrap.fill(
                short_categories.get(str(column), str(column)),
                width=14,
                break_long_words=False,
            )
            for column in matrix.columns
        ],
        rotation=22,
        ha="right",
        fontsize=7.2,
    )
    ax.set_yticks(np.arange(matrix.shape[0]))
    ax.set_yticklabels(matrix.index, fontsize=7.4)
    for row in range(matrix.shape[0]):
        for col in range(matrix.shape[1]):
            value = matrix.iloc[row, col]
            if pd.isna(value):
                continue
            text_color = WHITE if value >= 58 else NAVY
            ax.text(col, row, f"{value:.0f}", ha="center", va="center", fontsize=6.7, color=text_color, fontweight="bold")
    cbar = fig.colorbar(image, ax=ax, fraction=0.032, pad=0.02)
    cbar.set_label("Tasa de aprobación (%)", fontsize=7)
    cbar.ax.tick_params(labelsize=6)
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    return fig


def draw_figure(spec: FigureSpec) -> plt.Figure:
    handlers = {
        "architecture": _draw_architecture,
        "score_coverage": _draw_score_coverage,
        "trend": _draw_trend,
        "control_rate": _draw_control_rate,
        "findings": _draw_findings,
        "heatmap": _draw_heatmap,
    }
    if spec.draw_key not in handlers:
        raise ValueError(f"Figura no implementada: {spec.draw_key}")
    return handlers[spec.draw_key](spec)


def render_figure(spec: FigureSpec) -> dict[str, bytes]:
    """Genera SVG/PDF vectoriales, PNG 600 dpi, preview y CSV de datos."""
    fig = draw_figure(spec)
    files: dict[str, bytes] = {}
    for format_name, dpi in [("png", 600), ("preview", 150)]:
        buffer = io.BytesIO()
        fig.savefig(
            buffer,
            format="png",
            dpi=dpi,
            bbox_inches="tight",
            pad_inches=0.22,
            facecolor=WHITE,
        )
        files[format_name] = buffer.getvalue()
    for format_name, metadata in [("svg", None), ("pdf", {"Title": spec.full_title, "Author": "CIS Hardening Auditor", "Subject": spec.caption})]:
        buffer = io.BytesIO()
        fig.savefig(
            buffer,
            format=format_name,
            bbox_inches="tight",
            pad_inches=0.22,
            facecolor=WHITE,
            metadata=metadata,
        )
        files[format_name] = buffer.getvalue()
    plt.close(fig)
    files["csv"] = spec.data.to_csv(index=False).encode("utf-8-sig")
    return files


# ---------------------------------------------------------------------------
# Tablas
# ---------------------------------------------------------------------------
def _format_cell(value: Any, column: str, spec: TableSpec) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "—"
    if pd.isna(value):
        return "—"
    if column in spec.percent_columns:
        return f"{float(value):.2f}%"
    if column in spec.number_columns:
        if isinstance(value, (int, np.integer)):
            return f"{int(value):,}".replace(",", " ")
        if isinstance(value, float):
            return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.strftime("%Y-%m-%d %H:%M")
    return str(value)


def render_table_csv(spec: TableSpec) -> bytes:
    return spec.dataframe.to_csv(index=False).encode("utf-8-sig")


def render_table_xlsx(spec: TableSpec, dataset: Dataset) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Tabla"
    data = spec.dataframe.copy()
    ws.sheet_view.showGridLines = False
    last_col = get_column_letter(len(data.columns))
    ws.merge_cells(f"A1:{last_col}1")
    ws["A1"] = "CIS HARDENING AUDITOR · ANEXO EDITORIAL"
    ws["A1"].font = Font(name="Calibri", size=9, bold=True, color="0891B2")
    ws.merge_cells(f"A2:{last_col}2")
    ws["A2"] = spec.full_title
    ws["A2"].font = Font(name="Calibri", size=16, bold=True, color="0B1220")
    ws.merge_cells(f"A3:{last_col}3")
    ws["A3"] = "Explicación: " + spec.explanation
    ws["A3"].alignment = Alignment(wrap_text=True, vertical="top")
    ws["A3"].font = Font(name="Calibri", size=9, color="334155")
    ws.row_dimensions[3].height = 45
    ws.merge_cells(f"A4:{last_col}4")
    ws["A4"] = "Descripción: " + spec.description
    ws["A4"].alignment = Alignment(wrap_text=True, vertical="top")
    ws["A4"].font = Font(name="Calibri", size=9, color="334155")
    ws.row_dimensions[4].height = 55
    ws.merge_cells(f"A5:{last_col}5")
    ws["A5"] = "Nota: " + spec.notes
    ws["A5"].alignment = Alignment(wrap_text=True, vertical="top")
    ws["A5"].font = Font(name="Calibri", size=8, italic=True, color="64748B")
    ws.row_dimensions[5].height = 50

    header_row = 7
    for col_index, column in enumerate(data.columns, start=1):
        cell = ws.cell(row=header_row, column=col_index, value=column)
        cell.fill = PatternFill("solid", fgColor="0B1220")
        cell.font = Font(name="Calibri", size=9, bold=True, color="FFFFFF")
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = Border(
            left=Side(style="thin", color="1E293B"),
            right=Side(style="thin", color="1E293B"),
            top=Side(style="thin", color="1E293B"),
            bottom=Side(style="thin", color="1E293B"),
        )
    ws.row_dimensions[header_row].height = 34

    for row_index, row in enumerate(data.itertuples(index=False), start=header_row + 1):
        for col_index, (column, value) in enumerate(zip(data.columns, row, strict=True), start=1):
            cell = ws.cell(row=row_index, column=col_index, value=value)
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            cell.font = Font(name="Calibri", size=8.5, color="172033")
            cell.border = Border(
                left=Side(style="thin", color="DCE3ED"),
                right=Side(style="thin", color="DCE3ED"),
                top=Side(style="thin", color="DCE3ED"),
                bottom=Side(style="thin", color="DCE3ED"),
            )
            if row_index % 2 == 0:
                cell.fill = PatternFill("solid", fgColor="F8FAFC")
            if column in spec.percent_columns:
                cell.number_format = '0.00"%"'
            elif column in spec.number_columns:
                if "Duración" in column:
                    cell.number_format = "0.00"
                else:
                    cell.number_format = "#,##0"
        ws.row_dimensions[row_index].height = 28

    last_row = header_row + len(data)
    for index, weight in enumerate(spec.column_widths or [1] * len(data.columns), start=1):
        ws.column_dimensions[get_column_letter(index)].width = max(10, min(38, 12 + weight * 9))
    ws.freeze_panes = f"A{header_row + 1}"
    ws.auto_filter.ref = f"A{header_row}:{last_col}{last_row}"

    notes_row = last_row + 2
    ws.merge_cells(f"A{notes_row}:{last_col}{notes_row}")
    ws[f"A{notes_row}"] = "Nota: " + spec.notes
    ws[f"A{notes_row}"].alignment = Alignment(wrap_text=True, vertical="top")
    ws[f"A{notes_row}"].font = Font(name="Calibri", size=8, italic=True, color="64748B")
    ws.row_dimensions[notes_row].height = 52
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_title_rows = f"{header_row}:{header_row}"

    meta = wb.create_sheet("Metadatos")
    meta["A1"] = "Metadatos editoriales"
    meta["A1"].font = Font(name="Calibri", size=14, bold=True, color="0B1220")
    rows = [
        ("Número", f"Tabla {spec.number}"),
        ("Título", spec.title),
        ("Explicación", spec.explanation),
        ("Descripción", spec.description),
        ("Notas", spec.notes),
        ("Fuente", dataset.source_label),
        ("Organización", dataset.organization),
        ("Generado", dataset.generated_at.strftime("%Y-%m-%d %H:%M")),
        ("Filas", len(data)),
        ("Columnas", len(data.columns)),
    ]
    for index, (key, value) in enumerate(rows, start=3):
        meta.cell(row=index, column=1, value=key).font = Font(name="Calibri", bold=True, color="334155")
        meta.cell(row=index, column=2, value=value).alignment = Alignment(wrap_text=True, vertical="top")
    meta.column_dimensions["A"].width = 18
    meta.column_dimensions["B"].width = 110
    meta.sheet_view.showGridLines = False
    wb.properties.title = spec.full_title
    wb.properties.creator = "CIS Hardening Auditor"
    wb.properties.subject = spec.caption
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def _pdf_shell(title: str):
    class Doc(BaseDocTemplate):
        def __init__(self, filename: str, **kwargs: Any):
            super().__init__(filename, **kwargs)
            frame = Frame(
                1.15 * cm,
                1.45 * cm,
                landscape(A4)[0] - 2.3 * cm,
                landscape(A4)[1] - 2.75 * cm,
                id="normal",
            )
            self.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=self._decorate)])

        def _decorate(self, canvas, doc):
            width, height = landscape(A4)
            canvas.saveState()
            canvas.setFillColor(colors.HexColor(NAVY))
            canvas.rect(0, height - 1.05 * cm, width, 1.05 * cm, stroke=0, fill=1)
            canvas.setFillColor(colors.white)
            canvas.setFont("Helvetica-Bold", 7.5)
            canvas.drawString(1.15 * cm, height - 0.66 * cm, "CIS HARDENING AUDITOR · ANEXO EDITORIAL")
            canvas.setFillColor(colors.HexColor("#94A3B8"))
            canvas.setFont("Helvetica", 7)
            canvas.drawRightString(width - 1.15 * cm, height - 0.66 * cm, title[:110])
            canvas.setStrokeColor(colors.HexColor("#DCE3ED"))
            canvas.line(1.15 * cm, 1.0 * cm, width - 1.15 * cm, 1.0 * cm)
            canvas.setFillColor(colors.HexColor(SLATE))
            canvas.setFont("Helvetica", 6.5)
            canvas.drawString(
                1.15 * cm,
                0.66 * cm,
                "Documento generado para artículo. Las notas y la fuente acompañan cada tabla.",
            )
            canvas.drawRightString(width - 1.15 * cm, 0.66 * cm, f"Página {doc.page}")
            canvas.restoreState()

    return Doc


def render_table_pdf(spec: TableSpec, dataset: Dataset) -> bytes:
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TableTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=19,
        textColor=colors.HexColor(NAVY),
        alignment=TA_LEFT,
        spaceAfter=5,
    )
    body_style = ParagraphStyle(
        "TableBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#334155"),
    )
    small_style = ParagraphStyle(
        "TableSmall",
        parent=body_style,
        fontSize=7,
        leading=9,
        textColor=colors.HexColor(SLATE),
    )
    cell_style = ParagraphStyle(
        "Cell",
        parent=body_style,
        fontSize=6.4,
        leading=8.0,
        splitLongWords=1,
    )
    head_style = ParagraphStyle(
        "Head",
        parent=cell_style,
        fontName="Helvetica-Bold",
        textColor=colors.white,
        fontSize=6.2,
    )
    data = spec.dataframe
    buffer = io.BytesIO()
    doc = _pdf_shell(spec.full_title)(buffer, pagesize=landscape(A4), title=spec.full_title, author="CIS Hardening Auditor")
    story: list[Any] = [
        Paragraph(escape(spec.full_title), title_style),
        Spacer(1, 0.18 * cm),
        Paragraph("<b>Explicación.</b> " + escape(spec.explanation), body_style),
        Spacer(1, 0.12 * cm),
        Paragraph("<b>Descripción.</b> " + escape(spec.description), body_style),
        Spacer(1, 0.18 * cm),
        Paragraph("<b>Nota.</b> " + escape(spec.notes), small_style),
        Spacer(1, 0.3 * cm),
    ]
    header = [Paragraph(escape(str(column)), head_style) for column in data.columns]
    rows: list[list[Any]] = [header]
    for record in data.itertuples(index=False):
        rows.append(
            [
                Paragraph(escape(_format_cell(value, column, spec)), cell_style)
                for column, value in zip(data.columns, record, strict=True)
            ]
        )
    available = landscape(A4)[0] - 2.3 * cm
    weights = spec.column_widths or [1.0] * len(data.columns)
    total_weight = sum(weights)
    widths = [available * (weight / total_weight) for weight in weights]
    table = LongTable(rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
    commands = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(NAVY)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#DCE3ED")),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
    ]
    table.setStyle(TableStyle(commands))
    story.append(table)
    doc.build(story)
    return buffer.getvalue()
