"""Anexo editorial en Streamlit para el artículo de CIS Hardening Auditor.

Ejecutar:
    streamlit run streamlit_app.py

La aplicación permite generar/descargar 6 tablas y 6 figuras numeradas. Cada
activo incluye título, explicación, descripción y notas de fuente. Los datos
pueden provenir de PostgreSQL (solo lectura) o de un dataset sintético
reproducible, claramente etiquetado.
"""

from __future__ import annotations

import hashlib
import io
import json
import math
import zipfile
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from publication.analytics import build_figures, build_tables
from publication.demo import build_demo_dataset
from publication.model import Dataset
from publication.postgres import LiveDataError, available_organizations, load_live_dataset
from publication.rendering import (
    render_figure,
    render_table_csv,
    render_table_pdf,
    render_table_xlsx,
)

BASE_DIR = Path(__file__).resolve().parent
DEMO_DIR = BASE_DIR / "publication" / "output" / "demo"
ASSET_VERSION = "1.0.0"
PROJECT = "CIS Hardening Auditor"


st.set_page_config(
    page_title="Anexo editorial · CIS Hardening Auditor",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": (
            "Anexo editorial reproducible del proyecto CIS Hardening Auditor. "
            "6 tablas y 6 figuras para artículo, con descarga en formatos de imprenta."
        )
    },
)

st.markdown(
    """
    <style>
    :root {
      --navy: #0b1220;
      --ink: #172033;
      --cyan: #06b6d4;
      --teal: #0e7490;
      --slate: #64748b;
      --line: #dce3ed;
      --surface: #f7f9fc;
    }
    [data-testid="stAppViewContainer"] {
      background:
        radial-gradient(circle at 95% 0%, rgba(6,182,212,.075), transparent 30rem),
        radial-gradient(circle at 0% 100%, rgba(37,99,235,.045), transparent 34rem),
        #f7f9fc;
    }
    [data-testid="stHeader"] { background: transparent; }
    .block-container { max-width: 1480px; padding-top: 2.1rem; padding-bottom: 3rem; }
    h1, h2, h3, h4 { color: var(--navy); letter-spacing: -0.02em; }
    .hero {
      position: relative;
      overflow: hidden;
      border-radius: 22px;
      padding: 28px 30px 26px 30px;
      background:
        radial-gradient(circle at 92% 18%, rgba(6,182,212,.25), transparent 36%),
        linear-gradient(135deg, #07101e 0%, #0b1a2f 65%, #10233c 100%);
      color: white;
      border: 1px solid rgba(255,255,255,.08);
      box-shadow: 0 24px 55px -30px rgba(2,6,23,.62);
      margin-bottom: 18px;
    }
    .hero .kicker {
      color: #67e8f9;
      font-size: 10px;
      font-weight: 800;
      letter-spacing: .18em;
      text-transform: uppercase;
    }
    .hero h1 {
      color: white;
      font-size: 34px;
      line-height: 1.1;
      margin: 9px 0 8px 0;
      font-weight: 800;
    }
    .hero p { color: #b8c6d9; max-width: 860px; font-size: 14px; line-height: 1.65; margin: 0; }
    .hero .pill {
      display: inline-flex;
      margin-top: 16px;
      gap: 8px;
      padding: 6px 11px;
      border-radius: 999px;
      border: 1px solid rgba(103,232,249,.25);
      background: rgba(6,182,212,.10);
      color: #a5f3fc;
      font-size: 10px;
      font-weight: 700;
      letter-spacing: .04em;
    }
    .asset-label {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      color: var(--teal);
      font-size: 10px;
      font-weight: 800;
      letter-spacing: .16em;
      text-transform: uppercase;
      margin-bottom: 3px;
    }
    .asset-title { font-size: 21px; font-weight: 800; color: var(--navy); line-height: 1.22; margin: 0 0 4px 0; }
    .asset-sub { color: var(--slate); font-size: 12px; line-height: 1.6; margin-bottom: 12px; }
    .meta-label { color: #0e7490; font-size: 9px; font-weight: 800; letter-spacing: .14em; text-transform: uppercase; }
    .meta-text { color: #334155; font-size: 12px; line-height: 1.65; }
    .note-box {
      background: #f8fafc;
      border-left: 3px solid #06b6d4;
      border-radius: 0 10px 10px 0;
      padding: 9px 12px;
      color: #64748b;
      font-size: 10.5px;
      line-height: 1.55;
      margin-top: 7px;
    }
    .provenance {
      border-radius: 14px;
      padding: 13px 15px;
      font-size: 12px;
      line-height: 1.6;
      margin: 8px 0 14px 0;
    }
    .provenance.synthetic { background: #fffbeb; border: 1px solid #fde68a; color: #78350f; }
    .provenance.live { background: #ecfdf5; border: 1px solid #a7f3d0; color: #065f46; }
    .metric-card {
      background: white;
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 12px 14px;
      height: 100%;
    }
    .metric-card .k { color: #64748b; font-size: 9px; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; }
    .metric-card .v { color: var(--navy); font-size: 23px; font-weight: 800; margin-top: 3px; }
    .metric-card .d { color: #94a3b8; font-size: 10px; margin-top: 2px; }
    [data-testid="stSidebar"] { background: #0b1220; }
    [data-testid="stSidebar"] * { color: #e2e8f0; }
    [data-testid="stSidebar"] .stRadio label, [data-testid="stSidebar"] .stSelectbox label { color: #cbd5e1 !important; }
    [data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.10); }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: #cbd5e1; }
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] { color: #94a3b8; }
    .stDownloadButton button, .stButton button {
      border-radius: 9px !important;
      font-weight: 700 !important;
      font-size: 11px !important;
    }
    .stTabs [data-baseweb="tab"] { font-weight: 700; font-size: 12px; }
    .stTabs [aria-selected="true"] { color: #0e7490 !important; }
    details { background: #f8fafc; border: 1px solid var(--line); border-radius: 10px; padding: 8px 12px; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Carga de datos
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False, ttl=60)
def get_organizations() -> pd.DataFrame:
    try:
        return available_organizations()
    except LiveDataError:
        return pd.DataFrame(columns=["organization_id", "name", "slug"])


@st.cache_data(show_spinner=False)
def get_specs(source_mode: str, org_id: str | None) -> tuple[Dataset, dict, dict]:
    if source_mode == "live" and org_id:
        dataset = load_live_dataset(org_id)
    else:
        dataset = build_demo_dataset()
    return dataset, build_tables(dataset), build_figures(dataset)


def _sha256_frame_set(dataset: Dataset) -> str:
    digest = hashlib.sha256()
    for name, frame in [
        ("servers", dataset.servers),
        ("runs", dataset.runs),
        ("checks", dataset.checks),
        ("controls", dataset.controls),
        ("findings", dataset.findings),
    ]:
        digest.update(name.encode())
        digest.update(frame.to_csv(index=False).encode("utf-8"))
    return digest.hexdigest()


@st.cache_data(show_spinner=False)
def table_assets(source_mode: str, org_id: str | None, slug: str) -> dict[str, bytes]:
    dataset, tables, _ = get_specs(source_mode, org_id)
    table = tables[slug]
    if source_mode == "demo":
        prefix = DEMO_DIR / "tablas" / table.filename_base
        paths = {
            "xlsx": prefix.with_suffix(".xlsx"),
            "csv": prefix.with_suffix(".csv"),
            "pdf": prefix.with_suffix(".pdf"),
        }
        if all(path.exists() for path in paths.values()):
            return {key: path.read_bytes() for key, path in paths.items()}
    return {
        "xlsx": render_table_xlsx(table, dataset),
        "csv": render_table_csv(table),
        "pdf": render_table_pdf(table, dataset),
    }


@st.cache_data(show_spinner=False)
def figure_assets(source_mode: str, org_id: str | None, slug: str) -> dict[str, bytes]:
    dataset, _, figures = get_specs(source_mode, org_id)
    figure = figures[slug]
    if source_mode == "demo":
        prefix = DEMO_DIR / "figuras" / figure.filename_base
        paths = {
            "png": prefix.with_suffix(".png"),
            "preview": Path(str(prefix) + "_preview.png"),
            "svg": prefix.with_suffix(".svg"),
            "pdf": prefix.with_suffix(".pdf"),
            "csv": prefix.with_suffix(".csv"),
        }
        if all(path.exists() for path in paths.values()):
            return {key: path.read_bytes() for key, path in paths.items()}
    return render_figure(figure)


@st.cache_data(show_spinner=False)
def static_zip() -> bytes | None:
    path = DEMO_DIR / "paquete_completo.zip"
    return path.read_bytes() if path.exists() else None


def _format_cell(value, column: str, spec) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "—"
    if pd.isna(value):
        return "—"
    if column in spec.percent_columns:
        return f"{float(value):.2f}%"
    if column in spec.number_columns:
        if isinstance(value, str):
            return value
        if isinstance(value, float) and not value.is_integer():
            return f"{value:.2f}"
        return f"{int(value):,}".replace(",", " ")
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.strftime("%Y-%m-%d %H:%M")
    return str(value)


def preview_frame(table):
    frame = table.dataframe.copy()
    for column in frame.columns:
        frame[column] = frame[column].map(lambda value, col=column: _format_cell(value, col, table))
    return frame


def format_bytes(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.0f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


def provenance_manifest(dataset: Dataset, tables: dict, figures: dict) -> dict:
    return {
        "project": PROJECT,
        "artifact": "Anexo editorial para artículo",
        "version": ASSET_VERSION,
        "generated_at": dataset.generated_at.isoformat(),
        "source": {
            "type": dataset.source_type,
            "label": dataset.source_label,
            "organization": dataset.organization,
            "note": dataset.source_note,
            "fingerprint": _sha256_frame_set(dataset),
        },
        "dataset": {
            "servers": len(dataset.servers),
            "runs": len(dataset.runs),
            "checks": len(dataset.checks),
            "controls": len(dataset.controls),
            "findings": len(dataset.findings),
            "metadata": dataset.metadata,
        },
        "tables": [
            {
                "number": table.number,
                "title": table.full_title,
                "caption": table.caption,
                "explanation": table.explanation,
                "description": table.description,
                "notes": table.notes,
            }
            for table in sorted(tables.values(), key=lambda item: item.number)
        ],
        "figures": [
            {
                "number": figure.number,
                "title": figure.full_title,
                "caption": figure.caption,
                "explanation": figure.explanation,
                "description": figure.description,
                "notes": figure.notes,
            }
            for figure in sorted(figures.values(), key=lambda item: item.number)
        ],
    }


def captions_markdown(dataset: Dataset, tables: dict, figures: dict) -> str:
    lines = [
        "# Leyendas y metadatos para el artículo",
        "",
        f"**Proyecto:** {PROJECT}  ",
        f"**Fuente:** {dataset.source_label}  ",
        f"**Organización:** {dataset.organization}  ",
        f"**Generado:** {dataset.generated_at.strftime('%Y-%m-%d %H:%M')}  ",
        "",
        f"> **Procedencia:** {dataset.source_note}",
        "",
        "## Tablas",
        "",
    ]
    for table in sorted(tables.values(), key=lambda item: item.number):
        lines += [
            f"### {table.full_title}",
            "",
            f"**Título para el artículo:** {table.caption}",
            "",
            f"**Explicación:** {table.explanation}",
            "",
            f"**Descripción:** {table.description}",
            "",
            f"**Nota:** {table.notes}",
            "",
        ]
    lines += ["## Figuras", ""]
    for figure in sorted(figures.values(), key=lambda item: item.number):
        lines += [
            f"### {figure.full_title}",
            "",
            f"**Título para el artículo:** {figure.caption}",
            "",
            f"**Explicación:** {figure.explanation}",
            "",
            f"**Descripción:** {figure.description}",
            "",
            f"**Nota:** {figure.notes}",
            "",
        ]
    lines += [
        "## Reglas de uso",
        "",
        "- Cada tabla y figura debe citarse en el texto.",
        "- Las notas deben acompañar la versión final.",
        "- Las figuras 1 y 2 son conceptuales; las figuras 3–6 y las tablas 1, 3–6 requieren datos empíricos si el artículo reporta resultados.",
        "- No presente datos sintéticos como mediciones reales.",
    ]
    return "\n".join(lines) + "\n"


def make_live_zip(source_mode: str, org_id: str | None) -> bytes:
    dataset, tables, figures = get_specs(source_mode, org_id)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for table in sorted(tables.values(), key=lambda item: item.number):
            assets = table_assets(source_mode, org_id, table.slug)
            for fmt, data in assets.items():
                archive.writestr(f"tablas/{table.filename_base}.{fmt}", data)
        for figure in sorted(figures.values(), key=lambda item: item.number):
            assets = figure_assets(source_mode, org_id, figure.slug)
            for fmt, data in assets.items():
                suffix = ".png" if fmt == "png" else ("_preview.png" if fmt == "preview" else f".{fmt}")
                archive.writestr(f"figuras/{figure.filename_base}{suffix}", data)
        archive.writestr(
            "manifiesto.json",
            json.dumps(provenance_manifest(dataset, tables, figures), ensure_ascii=False, indent=2),
        )
        archive.writestr(
            "leyendas_articulo.md",
            captions_markdown(dataset, tables, figures),
        )
        for name, frame in [
            ("servidores", dataset.servers),
            ("ejecuciones", dataset.runs),
            ("checks", dataset.checks),
            ("controles", dataset.controls),
            ("hallazgos", dataset.findings),
        ]:
            archive.writestr(f"datos/{name}.csv", frame.to_csv(index=False).encode("utf-8-sig"))
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# Barra lateral y selección de fuente
# ---------------------------------------------------------------------------
orgs = get_organizations()
has_live = not orgs.empty

with st.sidebar:
    st.markdown(
        "<div style='padding: 4px 0 14px 0'><div style='font-size:26px'>🛡️</div>"
        "<div style='font-size:16px;font-weight:800;letter-spacing:-.02em;color:#fff'>Anexo editorial</div>"
        "<div style='font-size:10px;color:#67e8f9;font-weight:700;letter-spacing:.14em;margin-top:2px'>CIS HARDENING AUDITOR</div></div>",
        unsafe_allow_html=True,
    )
    st.divider()
    source_options = ["Demostración sintética"] + (["PostgreSQL institucional"] if has_live else [])
    source_label = st.radio(
        "Fuente de datos",
        source_options,
        index=0,
        help="PostgreSQL solo aparece si hay organizaciones con ejecuciones. El dataset sintético permite probar todo el anexo sin tocar infraestructura.",
    )
    source_mode = "demo" if source_label.startswith("Demostración") else "live"
    org_id = None
    if source_mode == "live":
        labels = {row["organization_id"]: f"{row['name']} ({row['slug']})" for _, row in orgs.iterrows()}
        org_id = st.selectbox("Organización", list(labels), format_func=lambda key: labels[key])
    if st.button("Actualizar datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.caption("Lectura de PostgreSQL en modo `default_transaction_read_only=on`.")
    st.divider()
    st.markdown("**Qué contiene**")
    st.caption("6 tablas · 6 figuras · 12 fichas editoriales con título, explicación y descripción.")
    st.markdown("**Calidad de descarga**")
    st.caption("Tablas: PDF vectorial, XLSX editable y CSV. Figuras: SVG/PDF vectorial, PNG 600 dpi y CSV de datos.")
    with st.expander("Cómo usar en el artículo"):
        st.markdown(
            "1. Elija la fuente y verifique la advertencia de procedencia.\n"
            "2. Descargue el paquete completo o cada activo.\n"
            "3. Incorpore las leyendas de la pestaña **Leyendas y metadatos**.\n"
            "4. Mantenga la nota de fuente y las limitaciones.\n"
            "5. Para resultados empíricos, use PostgreSQL institucional y revise anonimización."
        )
    st.divider()
    st.caption(f"Paquete editorial v{ASSET_VERSION}")


# ---------------------------------------------------------------------------
# Carga principal
# ---------------------------------------------------------------------------
try:
    with st.spinner("Preparando tablas, figuras y metadatos…"):
        dataset, tables, figures = get_specs(source_mode, org_id)
except LiveDataError as exc:
    st.error(f"No fue posible cargar PostgreSQL: {exc}")
    st.info("Cambie la fuente a **Demostración sintética** para revisar el anexo completo.")
    st.stop()
except Exception as exc:  # noqa: BLE001
    st.error("No fue posible construir el anexo editorial.")
    st.exception(exc)
    st.stop()

tables_ordered = sorted(tables.values(), key=lambda item: item.number)
figures_ordered = sorted(figures.values(), key=lambda item: item.number)
latest_scores = [
    float(value) for value in dataset.servers.get("latest_score", pd.Series(dtype=float)).dropna()
]
mean_score = sum(latest_scores) / len(latest_scores) if latest_scores else None
active_findings = int(
    (~dataset.findings["status"].isin(["resolved", "false_positive"])).sum()
) if not dataset.findings.empty else 0
fingerprint = _sha256_frame_set(dataset)
period = dataset.metadata.get("period") or (
    f"{pd.to_datetime(dataset.runs['run_date']).min():%Y-%m-%d} a "
    f"{pd.to_datetime(dataset.runs['run_date']).max():%Y-%m-%d}"
    if not dataset.runs.empty
    else "sin periodo"
)

st.markdown(
    f"""
    <div class="hero">
      <div class="kicker">Anexo editorial · material para artículo</div>
      <h1>Seis tablas y seis figuras para comunicar la evidencia</h1>
      <p>
        Activos editoriales del proyecto <b>{PROJECT}</b>, numerados y autosuficientes.
        Cada elemento incluye título, explicación, descripción, nota de fuente y descarga
        en formatos de imprenta. La app no modifica la base de datos.
      </p>
      <div class="pill">6 tablas · 6 figuras · PDF/SVG vectorial · PNG 600 dpi · XLSX/CSV</div>
    </div>
    """,
    unsafe_allow_html=True,
)

if dataset.is_synthetic:
    st.markdown(
        f"""
        <div class="provenance synthetic">
          <b>Datos sintéticos reproducibles.</b> {dataset.source_note}
          Las tablas y figuras de resultados son una demostración metodológica, no mediciones
          empíricas. Antes de enviar un artículo con resultados, regenere el anexo con
          <b>PostgreSQL institucional</b>. Figuras 1 y 2 son conceptuales.
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        f"""
        <div class="provenance live">
          <b>Datos institucionales.</b> {dataset.source_note}
          Revise autorización, anonimización y acuerdos de datos antes de publicar.
          La lectura se realizó en modo de solo lectura.
        </div>
        """,
        unsafe_allow_html=True,
    )

metric_cols = st.columns(6)
metric_values = [
    ("Servidores", len(dataset.servers), "unidades de análisis"),
    ("Ejecuciones", len(dataset.runs), period),
    ("Controles", len(dataset.controls), "catálogo evaluado"),
    ("Checks", len(dataset.checks), "observaciones"),
    ("Hallazgos", len(dataset.findings), f"{active_findings} activos"),
    ("Score medio", f"{mean_score:.1f}%" if mean_score is not None else "—", "última ejecución"),
]
for column, (key, value, detail) in zip(metric_cols, metric_values, strict=True):
    with column:
        st.markdown(
            f"<div class='metric-card'><div class='k'>{key}</div><div class='v'>{value}</div><div class='d'>{detail}</div></div>",
            unsafe_allow_html=True,
        )

st.caption(
    f"Fuente: {dataset.source_label} · {dataset.organization} · Generado: "
    f"{dataset.generated_at:%Y-%m-%d %H:%M} · Huella del dataset: `{fingerprint[:16]}…`"
)

# Descarga del paquete completo
live_zip_key = f"live_zip_{org_id}" if org_id else "live_zip"
zip_bytes = static_zip() if source_mode == "demo" else st.session_state.get(live_zip_key)
download_col, info_col = st.columns([1.1, 3.4])
with download_col:
    if zip_bytes:
        st.download_button(
            "Descargar paquete completo (.zip)",
            data=zip_bytes,
            file_name="anexo_editorial_cis_hardening_auditor.zip",
            mime="application/zip",
            use_container_width=True,
            type="primary",
        )
    elif source_mode == "live":
        if st.button("Preparar paquete completo", use_container_width=True, type="primary"):
            with st.spinner("Empaquetando 6 tablas y 6 figuras en alta calidad…"):
                st.session_state[live_zip_key] = make_live_zip(source_mode, org_id)
            st.rerun()
with info_col:
    st.caption(
        "El ZIP incluye tablas PDF/XLSX/CSV, figuras SVG/PDF/PNG 600 dpi/CSV, datos normalizados, "
        "manifiesto con checksums y leyendas para el artículo."
    )

tab_tables, tab_figures, tab_legends = st.tabs(["Tablas (6)", "Figuras (6)", "Leyendas y metadatos"])

# ---------------------------------------------------------------------------
# Tablas
# ---------------------------------------------------------------------------
with tab_tables:
    st.markdown(
        "Las tablas priorizan valores exactos. El PDF es vectorial para maquetación; "
        "XLSX conserva formato y metadatos; CSV permite reproducibilidad."
    )
    for table in tables_ordered:
        assets = table_assets(source_mode, org_id, table.slug)
        with st.container(border=True):
            st.markdown(
                f"<div class='asset-label'>TABLA {table.number} · {len(table.dataframe)} filas</div>"
                f"<div class='asset-title'>{table.title}</div>"
                f"<div class='asset-sub'>{table.caption}</div>",
                unsafe_allow_html=True,
            )
            left, right = st.columns([2.15, 1.0], gap="large")
            with left:
                st.markdown("<div class='meta-label'>Explicación</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='meta-text'>{table.explanation}</div>", unsafe_allow_html=True)
                st.markdown("<div class='meta-label' style='margin-top:12px'>Descripción</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='meta-text'>{table.description}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='note-box'><b>Nota.</b> {table.notes}</div>", unsafe_allow_html=True)
            with right:
                st.markdown("<div class='meta-label'>Descargas de alta calidad</div>", unsafe_allow_html=True)
                st.download_button(
                    "PDF vectorial",
                    data=assets["pdf"],
                    file_name=f"{table.filename_base}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key=f"table_{table.number}_pdf",
                )
                st.download_button(
                    "XLSX editable",
                    data=assets["xlsx"],
                    file_name=f"{table.filename_base}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key=f"table_{table.number}_xlsx",
                )
                st.download_button(
                    "CSV de datos",
                    data=assets["csv"],
                    file_name=f"{table.filename_base}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key=f"table_{table.number}_csv",
                )
                st.caption(
                    f"{format_bytes(len(assets['pdf']))} PDF · {format_bytes(len(assets['xlsx']))} XLSX · "
                    f"{format_bytes(len(assets['csv']))} CSV"
                )
            st.dataframe(
                preview_frame(table),
                use_container_width=True,
                hide_index=True,
                height=min(440, 82 + 35 * len(table.dataframe)),
            )

# ---------------------------------------------------------------------------
# Figuras
# ---------------------------------------------------------------------------
with tab_figures:
    st.markdown(
        "Las figuras se entregan en SVG y PDF vectoriales para imprenta, PNG a 600 dpi "
        "para revisión y CSV con los datos subyacentes. Todas incluyen título, fuente y nota."
    )
    for figure in figures_ordered:
        assets = figure_assets(source_mode, org_id, figure.slug)
        with st.container(border=True):
            st.markdown(
                f"<div class='asset-label'>FIGURA {figure.number} · {figure.slug.replace('_', ' ')}</div>"
                f"<div class='asset-title'>{figure.title}</div>"
                f"<div class='asset-sub'>{figure.caption}</div>",
                unsafe_allow_html=True,
            )
            st.image(assets["preview"], use_container_width=True)
            left, right = st.columns([2.2, 1.0], gap="large")
            with left:
                st.markdown("<div class='meta-label'>Explicación</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='meta-text'>{figure.explanation}</div>", unsafe_allow_html=True)
                st.markdown("<div class='meta-label' style='margin-top:12px'>Descripción</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='meta-text'>{figure.description}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='note-box'><b>Nota.</b> {figure.notes}</div>", unsafe_allow_html=True)
            with right:
                st.markdown("<div class='meta-label'>Descargas de alta calidad</div>", unsafe_allow_html=True)
                st.download_button(
                    "PNG 600 dpi",
                    data=assets["png"],
                    file_name=f"{figure.filename_base}.png",
                    mime="image/png",
                    use_container_width=True,
                    key=f"figure_{figure.number}_png",
                )
                st.download_button(
                    "SVG vectorial",
                    data=assets["svg"],
                    file_name=f"{figure.filename_base}.svg",
                    mime="image/svg+xml",
                    use_container_width=True,
                    key=f"figure_{figure.number}_svg",
                )
                st.download_button(
                    "PDF vectorial",
                    data=assets["pdf"],
                    file_name=f"{figure.filename_base}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key=f"figure_{figure.number}_pdf",
                )
                st.download_button(
                    "CSV de datos",
                    data=assets["csv"],
                    file_name=f"{figure.filename_base}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key=f"figure_{figure.number}_csv",
                )
                st.caption(
                    f"{format_bytes(len(assets['png']))} PNG · {format_bytes(len(assets['svg']))} SVG · "
                    f"{format_bytes(len(assets['pdf']))} PDF"
                )

# ---------------------------------------------------------------------------
# Leyendas y metadatos
# ---------------------------------------------------------------------------
with tab_legends:
    st.markdown(
        "Copie las leyendas en el manuscrito o descárguelas como Markdown. Cada ficha conserva "
        "título, explicación, descripción y nota; el manifiesto incluye la huella del dataset."
    )
    legend_text = captions_markdown(dataset, tables, figures)
    manifest = provenance_manifest(dataset, tables, figures)
    col_a, col_b, col_c = st.columns([1, 1, 2])
    with col_a:
        st.download_button(
            "Leyendas (.md)",
            data=legend_text.encode("utf-8"),
            file_name="leyendas_articulo.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with col_b:
        st.download_button(
            "Manifiesto (.json)",
            data=json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8"),
            file_name="manifiesto_editorial.json",
            mime="application/json",
            use_container_width=True,
        )
    with col_c:
        st.caption(
            f"Huella del dataset: `{fingerprint}` · {len(tables)} tablas · {len(figures)} figuras · "
            f"fuente: {dataset.source_label}"
        )
    st.divider()
    for table in tables_ordered:
        with st.expander(f"{table.full_title}", expanded=False):
            st.markdown(f"**Título para el artículo:** {table.caption}")
            st.markdown(f"**Explicación:** {table.explanation}")
            st.markdown(f"**Descripción:** {table.description}")
            st.markdown(f"**Nota:** {table.notes}")
    for figure in figures_ordered:
        with st.expander(f"{figure.full_title}", expanded=False):
            st.markdown(f"**Título para el artículo:** {figure.caption}")
            st.markdown(f"**Explicación:** {figure.explanation}")
            st.markdown(f"**Descripción:** {figure.description}")
            st.markdown(f"**Nota:** {figure.notes}")

st.divider()
st.caption(
    f"{PROJECT} · Anexo editorial v{ASSET_VERSION} · 6 tablas / 6 figuras · "
    "Los formatos vectoriales son la mejor opción para imprenta; PNG 600 dpi es una copia raster de alta resolución. "
    "No se presentan datos sintéticos como resultados empíricos."
)
