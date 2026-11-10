"""Genera el paquete editorial descargable y reproducible."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from publication.analytics import build_figures, build_tables
from publication.demo import build_demo_dataset
from publication.model import Dataset, FigureSpec, TableSpec
from publication.rendering import (
    render_figure,
    render_table_csv,
    render_table_pdf,
    render_table_xlsx,
)

PROJECT_NAME = "CIS Hardening Auditor"
PACKAGE_VERSION = "1.0.0"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write(path: Path, data: bytes) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return {
        "file": path.name,
        "bytes": len(data),
        "sha256": _sha256(data),
    }


def _caption_markdown(tables: list[TableSpec], figures: list[FigureSpec], dataset: Dataset) -> str:
    lines = [
        "# Leyendas y metadatos para el artículo",
        "",
        f"**Proyecto:** {PROJECT_NAME}  ",
        f"**Fuente:** {dataset.source_label}  ",
        f"**Organización:** {dataset.organization}  ",
        f"**Generado:** {dataset.generated_at.strftime('%Y-%m-%d %H:%M')}  ",
        "",
        "> **Advertencia de procedencia:** " + dataset.metadata.get("warning", "Revise la fuente antes de publicar."),
        "",
        "## Tablas",
        "",
    ]
    for table in tables:
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
            f"**Archivos:** {table.filename_base}.xlsx · {table.filename_base}.csv · {table.filename_base}.pdf",
            "",
        ]
    lines += ["## Figuras", ""]
    for figure in figures:
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
            f"**Archivos:** {figure.filename_base}.svg · {figure.filename_base}.pdf · {figure.filename_base}.png (600 dpi) · {figure.filename_base}_preview.png · {figure.filename_base}.csv",
            "",
        ]
    lines += [
        "## Reglas de uso",
        "",
        "- Las tablas y figuras están numeradas y deben citarse en el texto del artículo.",
        "- Las notas acompañan cada activo y deben mantenerse en la versión final.",
        "- Las figuras 1 y 2 son conceptuales; no dependen de la muestra.",
        "- Las tablas 1, 3, 4, 5 y 6 y las figuras 3–6 deben regenerarse con datos institucionales antes de una publicación empírica.",
        "- No se deben presentar datos sintéticos como mediciones reales.",
    ]
    return "\n".join(lines) + "\n"


def _readme(dataset: Dataset, tables: list[TableSpec], figures: list[FigureSpec]) -> str:
    lines = [
        "# Anexo editorial · CIS Hardening Auditor",
        "",
        f"Paquete generado el **{dataset.generated_at.strftime('%Y-%m-%d %H:%M')}**.",
        "",
        f"**Fuente:** {dataset.source_label}  ",
        f"**Organización:** {dataset.organization}  ",
        f"**Cobertura:** {len(dataset.servers)} servidores, {len(dataset.runs)} ejecuciones, "
        f"{len(dataset.checks)} checks y {len(dataset.findings)} hallazgos.",
        "",
        "## Advertencia de procedencia",
        "",
        "> " + dataset.metadata.get("warning", "Revise la procedencia de los datos antes de publicar."),
        "",
        "## Contenido",
        "",
        "```text",
        "tablas/    6 tablas en PDF vectorial, XLSX editable y CSV",
        "figuras/   6 figuras en SVG/PDF vectorial, PNG 600 dpi, preview y CSV de datos",
        "datos/     datasets normalizados para reproducibilidad",
        "manifiesto.json  metadatos, checksums y rutas de todos los activos",
        "leyendas_articulo.md  títulos, explicaciones, descripciones y notas listas para el artículo",
        "```",
        "",
        "## Índice",
        "",
    ]
    for table in tables:
        lines.append(f"- **{table.full_title}** — {table.title}")
    for figure in figures:
        lines.append(f"- **{figure.full_title}** — {figure.title}")
    lines += [
        "",
        "## Formatos y calidad",
        "",
        "- Tablas: PDF vectorial (imprenta), XLSX con metadatos y formato, CSV UTF-8 para análisis.",
        "- Figuras: SVG y PDF vectoriales, PNG a 600 dpi y CSV con los datos subyacentes.",
        "- Las fuentes, notas y limitaciones se incluyen en cada activo y en `leyendas_articulo.md`.",
        "",
        "## Antes de publicar",
        "",
        "1. Sustituya el dataset sintético por la fuente PostgreSQL institucional si el artículo reporta resultados empíricos.",
        "2. Revise autorización, anonimización y acuerdos de datos.",
        "3. Mantenga las notas y limitaciones en el manuscrito.",
        "4. Verifique que cada tabla y figura esté citada en el texto.",
    ]
    return "\n".join(lines) + "\n"


def build_package(output_dir: str | Path, clean: bool = True) -> Path:
    output = Path(output_dir).resolve()
    if clean and output.exists():
        for child in output.iterdir():
            if child.name == "_preview":
                continue
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
    output.mkdir(parents=True, exist_ok=True)
    dataset = build_demo_dataset()
    tables_map = build_tables(dataset)
    figures_map = build_figures(dataset)
    tables = [tables_map[key] for key in sorted(tables_map, key=lambda key: tables_map[key].number)]
    figures = [figures_map[key] for key in sorted(figures_map, key=lambda key: figures_map[key].number)]

    manifest: dict[str, Any] = {
        "project": PROJECT_NAME,
        "artifact": "Anexo editorial para artículo",
        "package_version": PACKAGE_VERSION,
        "generated_at": dataset.generated_at.isoformat(),
        "source": {
            "type": dataset.source_type,
            "label": dataset.source_label,
            "organization": dataset.organization,
            "note": dataset.source_note,
            "key": dataset.source_key,
        },
        "dataset": {
            "servers": len(dataset.servers),
            "runs": len(dataset.runs),
            "checks": len(dataset.checks),
            "controls": len(dataset.controls),
            "findings": len(dataset.findings),
            "metadata": dataset.metadata,
        },
        "tables": [],
        "figures": [],
        "data": [],
        "files": {},
    }

    for table in tables:
        files = {
            "xlsx": _write(
                output / "tablas" / f"{table.filename_base}.xlsx",
                render_table_xlsx(table, dataset),
            ),
            "csv": _write(
                output / "tablas" / f"{table.filename_base}.csv",
                render_table_csv(table),
            ),
            "pdf": _write(
                output / "tablas" / f"{table.filename_base}.pdf",
                render_table_pdf(table, dataset),
            ),
        }
        manifest["tables"].append(
            {
                "number": table.number,
                "slug": table.slug,
                "title": table.full_title,
                "caption": table.caption,
                "explanation": table.explanation,
                "description": table.description,
                "notes": table.notes,
                "rows": len(table.dataframe),
                "columns": list(table.dataframe.columns),
                "files": files,
            }
        )
        manifest["files"].update({f"tabla_{table.number:02d}_{key}": value for key, value in files.items()})

    for figure in figures:
        raw = render_figure(figure)
        files = {
            "svg": _write(
                output / "figuras" / f"{figure.filename_base}.svg",
                raw["svg"],
            ),
            "pdf": _write(
                output / "figuras" / f"{figure.filename_base}.pdf",
                raw["pdf"],
            ),
            "png_600dpi": _write(
                output / "figuras" / f"{figure.filename_base}.png",
                raw["png"],
            ),
            "preview": _write(
                output / "figuras" / f"{figure.filename_base}_preview.png",
                raw["preview"],
            ),
            "csv": _write(
                output / "figuras" / f"{figure.filename_base}.csv",
                raw["csv"],
            ),
        }
        manifest["figures"].append(
            {
                "number": figure.number,
                "slug": figure.slug,
                "title": figure.full_title,
                "caption": figure.caption,
                "explanation": figure.explanation,
                "description": figure.description,
                "notes": figure.notes,
                "draw_key": figure.draw_key,
                "files": files,
            }
        )
        manifest["files"].update(
            {f"figura_{figure.number:02d}_{key}": value for key, value in files.items()}
        )

    data_frames = {
        "servidores": dataset.servers,
        "ejecuciones": dataset.runs,
        "checks": dataset.checks,
        "controles": dataset.controls,
        "hallazgos": dataset.findings,
    }
    for name, frame in data_frames.items():
        data = frame.to_csv(index=False).encode("utf-8-sig")
        manifest["data"].append(_write(output / "datos" / f"{name}.csv", data))

    fingerprint = hashlib.sha256()
    for name in sorted(data_frames):
        fingerprint.update(data_frames[name].to_csv(index=False).encode("utf-8"))
    manifest["dataset"]["sha256"] = fingerprint.hexdigest()

    legend_file = _write(
        output / "leyendas_articulo.md",
        _caption_markdown(tables, figures, dataset).encode("utf-8"),
    )
    readme_file = _write(output / "LEEME.md", _readme(dataset, tables, figures).encode("utf-8"))
    manifest["files"]["leyendas"] = legend_file
    manifest["files"]["readme"] = readme_file
    manifest_json = json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8")
    manifest_file = _write(output / "manifiesto.json", manifest_json)
    manifest["files"]["manifest"] = manifest_file

    # ZIP con todas las piezas descargables.
    zip_path = output / "paquete_completo.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(output.rglob("*")):
            if not path.is_file() or path == zip_path or "_preview" in path.parts:
                continue
            archive.write(path, path.relative_to(output).as_posix())

    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera el anexo editorial descargable.")
    parser.add_argument(
        "--output",
        default="publication/output/demo",
        help="Directorio de salida (por defecto: publication/output/demo).",
    )
    parser.add_argument("--no-clean", action="store_true", help="No vaciar el directorio de salida.")
    args = parser.parse_args()
    output = build_package(args.output, clean=not args.no_clean)
    print(f"Paquete generado en: {output}")
    print(f"Tablas: 6 · Figuras: 6 · Manifiesto: {output / 'manifiesto.json'}")


if __name__ == "__main__":
    main()
