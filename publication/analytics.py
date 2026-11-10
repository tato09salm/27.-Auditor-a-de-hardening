"""Construcción de las 6 tablas y 6 figuras del anexo editorial."""

from __future__ import annotations

import pandas as pd

from publication.model import (
    CHECK_STATUS_LABEL,
    ENVIRONMENT_LABEL,
    SEVERITY_LABEL,
    SEVERITY_ORDER,
    STATUS_LABEL,
    STATUS_ORDER,
    Dataset,
    FigureSpec,
    TableSpec,
)


def _dt(series: pd.Series) -> pd.Series:
    values = pd.to_datetime(series, errors="coerce")
    if getattr(values.dt, "tz", None) is not None:
        values = values.dt.tz_localize(None)
    return values


def _completed(runs: pd.DataFrame) -> pd.DataFrame:
    return runs[(runs["status"] == "completed") & runs["score"].notna()].copy()


def _latest(dataset: Dataset) -> pd.DataFrame:
    runs = _completed(dataset.runs)
    if runs.empty:
        return runs
    return runs.sort_values("run_date").groupby("server_id", as_index=False).tail(1)


def _level_short(value: str) -> str:
    text = str(value or "")
    if "Level 2" in text:
        return "N2"
    if "Level 1" in text:
        return "N1"
    return "—"


def _control_aggregate(dataset: Dataset) -> pd.DataFrame:
    checks = dataset.checks.copy()
    rows: list[dict] = []
    for code, group in checks.groupby("control_code"):
        counts = group["status"].value_counts()
        passed = int(counts.get("passed", 0))
        failed = int(counts.get("failed", 0))
        na = int(counts.get("not_applicable", 0))
        ne = int(counts.get("not_evaluated", 0))
        applicable = passed + failed
        control = dataset.controls[dataset.controls["code"] == code].iloc[0]
        rows.append(
            {
                "control_code": code,
                "control_title": control["title"],
                "severity": control["severity"],
                "official": bool(control["official"]),
                "category": control["category"],
                "passed": passed,
                "failed": failed,
                "not_applicable": na,
                "not_evaluated": ne,
                "applicable": applicable,
                "total": len(group),
                "pass_rate": round(100 * passed / applicable, 2) if applicable else None,
                "coverage": round(100 * applicable / len(group), 2),
                "avg_duration_ms": round(float(group["duration_ms"].fillna(0).mean()), 0),
            }
        )
    return pd.DataFrame(rows).sort_values(["pass_rate", "control_code"], na_position="last")


def build_tables(dataset: Dataset) -> dict[str, TableSpec]:
    latest = _latest(dataset)
    controls = dataset.controls.copy()
    control_agg = _control_aggregate(dataset)

    # Tabla 1. Muestra de servidores
    server_table = dataset.servers.merge(
        latest[["server_id", "score", "coverage", "run_date"]], on="server_id", how="left"
    )
    t1 = pd.DataFrame(
        {
            "Servidor": server_table["name"],
            "Hostname": server_table["hostname"],
            "Entorno": server_table["environment"].map(ENVIRONMENT_LABEL).fillna(
                server_table["environment"]
            ),
            "Sistema operativo": server_table["os_family"] + " " + server_table["os_version"],
            "Área responsable": server_table["owner_area"],
            "Conexión": server_table["connection_method"],
            "Perfil": server_table["profile_name"],
            "Auditorías": server_table["audit_count"],
            "Cumplimiento (%)": server_table["latest_score"],
            "Cobertura (%)": server_table["latest_coverage"],
            "Hallazgos activos": server_table["active_findings"],
            "Última auditoría": _dt(server_table["last_audit_at"]).dt.strftime("%Y-%m-%d"),
        }
    ).sort_values(["Cumplimiento (%)", "Servidor"], ascending=[False, True])
    table1 = TableSpec(
        number=1,
        slug="caracterizacion_servidores",
        title="Caracterización de la muestra de servidores auditados",
        explanation=(
            "Permite juzgar la validez externa y el alcance real de la evaluación. Un promedio "
            "agregado de cumplimiento oculta que la muestra puede mezclar producción, pruebas y "
            "desarrollo, distintos sistemas operativos, áreas responsables y niveles de exposición. "
            "Esta tabla hace explícita esa composición antes de interpretar cualquier indicador."
        ),
        description=(
            "Una fila por servidor. Las columnas describen el entorno, el sistema operativo, el área "
            "responsable, el método de conexión y el perfil aplicado. «Cumplimiento» y «Cobertura» "
            "corresponden a la última ejecución completada de cada servidor; «Hallazgos activos» "
            "excluye los resueltos y los falsos positivos documentados."
        ),
        notes=(
            f"Fuente: {dataset.source_label}. n={len(t1)} servidores. "
            f"Periodo: {dataset.metadata.get('period', 'última ejecución disponible')}. "
            "Score = aprobados / (aprobados + incumplidos) × 100; no aplicables y no evaluados se "
            "excluyen del denominador. " + dataset.metadata.get("warning", "")
        ),
        caption=(
            "Caracterización de la muestra de servidores auditados, con entorno, sistema operativo, "
            "perfil, cumplimiento y cobertura de la última ejecución."
        ),
        dataframe=t1,
        column_labels={column: column for column in t1.columns},
        percent_columns=["Cumplimiento (%)", "Cobertura (%)"],
        number_columns=["Auditorías", "Hallazgos activos"],
        column_widths=[1.2, 1.25, 0.72, 0.9, 0.95, 0.6, 1.25, 0.5, 0.95, 0.82, 0.68, 0.78],
    )

    # Tabla 2. Catálogo de controles
    catalog = controls.sort_values(["category", "code"]).copy()
    catalog["Nivel"] = catalog["cis_level"].map(_level_short)
    catalog["Mapeo"] = catalog["official"].map({True: "CIS oficial", False: "Interno"})
    catalog["Severidad"] = catalog["severity"].map(SEVERITY_LABEL)
    catalog["Propósito"] = catalog["description"].str.slice(0, 155).str.strip() + "…"
    t2 = catalog.rename(
        columns={
            "code": "Código",
            "cis_reference": "Referencia CIS",
            "title": "Control",
            "category": "Categoría",
        }
    )[["Código", "Referencia CIS", "Control", "Categoría", "Severidad", "Nivel", "Mapeo", "Propósito"]]
    t2["Referencia CIS"] = t2["Referencia CIS"].replace("", "—")
    table2 = TableSpec(
        number=2,
        slug="catalogo_controles",
        title="Catálogo de controles de hardening evaluados",
        explanation=(
            "Documenta el instrumento de medición y la transparencia del mapeo. La tabla distingue "
            "los controles con referencia CIS contrastada de los controles internos inspirados en "
            "buenas prácticas. Esta separación evita atribuir al estándar CIS resultados que la "
            "plataforma calcula con controles propios y permite reproducir el alcance del estudio."
        ),
        description=(
            "Una fila por control. «Referencia CIS» indica el identificador del benchmark cuando el "
            "mapeo fue verificado; «Mapeo» señala si el control es CIS oficial o interno. «Nivel» "
            "resume el perfil del benchmark (N1/N2) y «Propósito» resume el requisito evaluado."
        ),
        notes=(
            f"Fuente: {dataset.source_label}; catálogo de {len(t2)} controles activos. "
            "La referencia CIS se contrastó con CIS Ubuntu Linux 22.04 LTS Benchmark v1.0.0. "
            "Los controles internos no constituyen un mapeo oficial de CIS."
        ),
        caption=(
            "Catálogo de controles evaluados, con referencia CIS, severidad, nivel, tipo de mapeo y "
            "propósito de cada requisito."
        ),
        dataframe=t2,
        column_labels={column: column for column in t2.columns},
        column_widths=[0.82, 0.65, 1.5, 0.82, 0.55, 0.38, 0.6, 2.05],
    )

    # Tabla 3. Resultados agregados por control
    t3 = control_agg.rename(
        columns={
            "control_code": "Código",
            "control_title": "Control",
            "severity": "Severidad",
            "official": "Mapeo",
            "passed": "Aprobados",
            "failed": "Incumplidos",
            "not_applicable": "No aplica",
            "not_evaluated": "No evaluado",
            "applicable": "Evaluados",
            "pass_rate": "Tasa de aprobación (%)",
            "coverage": "Cobertura (%)",
            "avg_duration_ms": "Duración media (ms)",
        }
    ).copy()
    t3["Severidad"] = t3["Severidad"].map(SEVERITY_LABEL)
    t3["Mapeo"] = t3["Mapeo"].map({True: "CIS oficial", False: "Interno"})
    t3 = t3[
        [
            "Código",
            "Control",
            "Severidad",
            "Mapeo",
            "Evaluados",
            "Aprobados",
            "Incumplidos",
            "No aplica",
            "No evaluado",
            "Tasa de aprobación (%)",
            "Cobertura (%)",
            "Duración media (ms)",
        ]
    ]
    table3 = TableSpec(
        number=3,
        slug="resultados_por_control",
        title="Resultados agregados por control",
        explanation=(
            "Identifica los controles que concentran el incumplimiento y permite priorizar la "
            "remediación con evidencia. También muestra la cobertura: un control con una tasa alta "
            "pero con muchos casos no evaluados no ofrece la misma confianza que uno evaluado en "
            "todos los servidores."
        ),
        description=(
            "Una fila por control, agregando todas las ejecuciones del periodo. «Evaluados» es la "
            "suma de aprobados e incumplidos; la tasa de aprobación usa ese denominador. «Cobertura» "
            "indica qué proporción del total de checks del control pudo evaluarse. La duración media "
            "resume el coste operativo de la comprobación."
        ),
        notes=(
            f"Fuente: {dataset.source_label}; {len(dataset.checks)} checks y "
            f"{len(dataset.runs)} ejecuciones. La tasa excluye «No aplica» y «No evaluado». "
            "Las duraciones provienen del motor de comprobaciones y no incluyen la latencia de red "
            "del entorno de publicación. " + dataset.metadata.get("warning", "")
        ),
        caption=(
            "Resultados agregados por control: evaluados, aprobados, incumplidos, no aplicables, no "
            "evaluados, tasa de aprobación, cobertura y duración media."
        ),
        dataframe=t3,
        column_labels={column: column for column in t3.columns},
        percent_columns=["Tasa de aprobación (%)", "Cobertura (%)"],
        number_columns=["Evaluados", "Aprobados", "Incumplidos", "No aplica", "No evaluado"],
        column_widths=[0.7, 1.55, 0.55, 0.6, 0.55, 0.55, 0.6, 0.55, 0.6, 0.75, 0.65, 0.7],
    )

    # Tabla 4. Cumplimiento por categoría
    category_rows: list[dict] = []
    for category, group in dataset.checks.groupby("category"):
        counts = group["status"].value_counts()
        passed = int(counts.get("passed", 0))
        failed = int(counts.get("failed", 0))
        applicable = passed + failed
        category_rows.append(
            {
                "Categoría": category,
                "Controles": int(group["control_code"].nunique()),
                "Evaluados": applicable,
                "Aprobados": passed,
                "Incumplidos": failed,
                "No aplica": int(counts.get("not_applicable", 0)),
                "No evaluado": int(counts.get("not_evaluated", 0)),
                "Tasa de aprobación (%)": round(100 * passed / applicable, 2) if applicable else None,
                "Cobertura (%)": round(100 * applicable / len(group), 2),
            }
        )
    t4 = pd.DataFrame(category_rows).sort_values("Tasa de aprobación (%)")
    table4 = TableSpec(
        number=4,
        slug="cumplimiento_por_categoria",
        title="Cumplimiento por categoría de control",
        explanation=(
            "Agrupa los controles por dominio para una lectura ejecutiva. Las categorías permiten "
            "detectar patrones que un ranking individual de controles no muestra: por ejemplo, una "
            "organización puede tener buen cumplimiento de firewall y un déficit sistémico en "
            "gestión de parches o autenticación."
        ),
        description=(
            "Una fila por categoría. Los conteos agregan todos los checks del periodo. La tasa de "
            "aprobación excluye los no aplicables y no evaluados; la cobertura muestra la proporción "
            "de checks con evidencia suficiente. Las categorías se ordenan de menor a mayor tasa."
        ),
        notes=(
            f"Fuente: {dataset.source_label}; {len(dataset.checks)} checks. "
            "La categoría es la definida en el catálogo del benchmark y no implica una jerarquía de "
            "riesgo. " + dataset.metadata.get("warning", "")
        ),
        caption=(
            "Cumplimiento por categoría de control, con controles, evaluados, aprobados, incumplidos, "
            "tasa de aprobación y cobertura."
        ),
        dataframe=t4,
        column_labels={column: column for column in t4.columns},
        percent_columns=["Tasa de aprobación (%)", "Cobertura (%)"],
        number_columns=["Controles", "Evaluados", "Aprobados", "Incumplidos", "No aplica", "No evaluado"],
        column_widths=[1.55, 0.6, 0.65, 0.65, 0.65, 0.6, 0.65, 0.8, 0.65],
    )

    # Tabla 5. Hallazgos por severidad y estado
    findings = dataset.findings.copy()
    matrix = (
        findings.pivot_table(
            index="severity", columns="status", values="finding_id", aggfunc="count", fill_value=0
        )
        .reindex(SEVERITY_ORDER, fill_value=0)
    )
    for status in STATUS_ORDER:
        if status not in matrix.columns:
            matrix[status] = 0
    matrix = matrix[STATUS_ORDER]
    t5_rows = []
    for severity in SEVERITY_ORDER:
        row = {"Severidad": SEVERITY_LABEL[severity]}
        for status in STATUS_ORDER:
            row[STATUS_LABEL[status]] = int(matrix.loc[severity, status])
        total = sum(row[STATUS_LABEL[status]] for status in STATUS_ORDER)
        row["Total histórico"] = total
        row["Activos"] = total - row["Resuelto"] - row["Falso positivo"]
        t5_rows.append(row)
    t5 = pd.DataFrame(t5_rows)
    table5 = TableSpec(
        number=5,
        slug="hallazgos_severidad_estado",
        title="Hallazgos por severidad y estado del ciclo de vida",
        explanation=(
            "Muestra el estado del backlog y la madurez del proceso de remediación. Un total alto de "
            "hallazgos no implica necesariamente un backlog alto: parte puede estar resuelto o "
            "documentado como falso positivo. La lectura conjunta de severidad y estado permite "
            "distinguir riesgo abierto de deuda histórica."
        ),
        description=(
            "Matriz de severidad por estado. Cada celda cuenta hallazgos únicos, no ocurrencias. "
            "«Activos» agrega los estados distintos de resuelto y falso positivo. La columna «Total "
            "histórico» conserva los cierres para trazabilidad."
        ),
        notes=(
            f"Fuente: {dataset.source_label}; {len(findings)} hallazgos únicos. "
            "Un hallazgo resuelto exige una comprobación posterior satisfactoria o una justificación "
            "autorizada. «Riesgo aceptado» sigue siendo un hallazgo activo. "
            + dataset.metadata.get("warning", "")
        ),
        caption=(
            "Distribución de hallazgos únicos por severidad y estado del ciclo de vida, incluyendo "
            "total histórico y hallazgos activos."
        ),
        dataframe=t5,
        column_labels={column: column for column in t5.columns},
        number_columns=[
            "Detectado",
            "En revisión",
            "Corrección planificada",
            "Pendiente de validación",
            "Riesgo aceptado",
            "Resuelto",
            "Falso positivo",
            "Total histórico",
            "Activos",
        ],
        column_widths=[0.65, 0.55, 0.65, 0.8, 0.75, 0.65, 0.6, 0.6, 0.65, 0.6, 0.55],
    )

    # Tabla 6. Trazabilidad de ejecuciones
    runs = dataset.runs.copy().sort_values("run_date", ascending=False)
    t6 = pd.DataFrame(
        {
            "Ejecución": runs["run_id"].str.slice(0, 12),
            "Fecha": _dt(runs["run_date"]).dt.strftime("%Y-%m-%d %H:%M"),
            "Servidor": runs["server_name"],
            "Entorno": runs["server_id"].map(
                dataset.servers.set_index("server_id")["environment"]
            ).map(ENVIRONMENT_LABEL),
            "Disparador": runs["trigger_type"].map(
                {
                    "manual": "Manual",
                    "schedule": "Programada",
                    "automation": "Automatizada",
                    "retry": "Reintento",
                }
            ).fillna(runs["trigger_type"]),
            "Estado": runs["status"].map(
                {"completed": "Completada", "failed": "Fallida", "running": "Ejecutando", "queued": "En cola"}
            ).fillna(runs["status"]),
            "Controles": runs["total_controls"],
            "Aprobados": runs["passed"],
            "Incumplidos": runs["failed"],
            "No aplica": runs["not_applicable"],
            "No evaluado": runs["not_evaluated"],
            "Cumplimiento (%)": runs["score"],
            "Cobertura (%)": runs["coverage"],
            "Duración (s)": runs["duration_seconds"],
            "Simulado": runs["is_simulated"].map({True: "Sí", False: "No"}),
        }
    )
    table6 = TableSpec(
        number=6,
        slug="trazabilidad_ejecuciones",
        title="Trazabilidad y métricas de las ejecuciones",
        explanation=(
            "Hace reproducible la evaluación: cada fila conserva el servidor, la fecha, el disparador, "
            "el estado y los conteos que produjeron el score. Sin esta trazabilidad no es posible "
            "distinguir una mejora real de un cambio en la cobertura, un fallo de conexión o una "
            "ejecución incompleta."
        ),
        description=(
            "Una fila por ejecución. «Cumplimiento» usa aprobados sobre aplicables evaluados; "
            "«Cobertura» indica la proporción del perfil que pudo evaluarse. La duración corresponde "
            "al intervalo de ejecución registrado. «Simulado» identifica el uso del conector de "
            "pruebas."
        ),
        notes=(
            f"Fuente: {dataset.source_label}; {len(t6)} ejecuciones. "
            "Los fallos de conexión producen controles no evaluados y un score no calculable; no se "
            "imputan como aprobados. " + dataset.metadata.get("warning", "")
        ),
        caption=(
            "Trazabilidad de las ejecuciones: fecha, servidor, entorno, disparador, estado, conteos, "
            "cumplimiento, cobertura, duración y naturaleza simulada."
        ),
        dataframe=t6,
        column_labels={column: column for column in t6.columns},
        percent_columns=["Cumplimiento (%)", "Cobertura (%)"],
        number_columns=[
            "Controles",
            "Aprobados",
            "Incumplidos",
            "No aplica",
            "No evaluado",
            "Duración (s)",
        ],
        column_widths=[0.7, 0.85, 1.15, 0.6, 0.65, 0.65, 0.5, 0.5, 0.55, 0.5, 0.55, 0.65, 0.6, 0.55, 0.5],
    )

    return {
        table.slug: table
        for table in [table1, table2, table3, table4, table5, table6]
    }


def build_figures(dataset: Dataset) -> dict[str, FigureSpec]:
    latest = _latest(dataset)
    completed = _completed(dataset.runs)
    findings = dataset.findings.copy()

    f2_data = (
        latest.merge(
            dataset.servers[["server_id", "environment"]], on="server_id", how="left"
        )[["server_name", "environment", "score", "coverage", "run_date"]]
        .sort_values("score", ascending=True)
    )
    figure2 = FigureSpec(
        number=2,
        slug="cumplimiento_cobertura_servidor",
        title="Cumplimiento y cobertura por servidor",
        explanation=(
            "Compara el resultado de la última auditoría con la proporción de controles que pudo "
            "evaluarse. Un score alto acompañado de baja cobertura no es comparable con un score "
            "similar obtenido sobre el perfil completo; la cobertura es parte del resultado, no un "
            "detalle técnico."
        ),
        description=(
            "Barras horizontales ordenadas por cumplimiento. La barra oscura representa el score y "
            "la barra clara la cobertura. La línea vertical punteada en 80 % es una referencia de "
            "lectura, no un umbral de certificación."
        ),
        notes=(
            f"Fuente: {dataset.source_label}; última ejecución completada por servidor (n={len(f2_data)}). "
            "Score = aprobados / (aprobados + incumplidos) × 100. "
            + dataset.metadata.get("warning", "")
        ),
        caption=(
            "Cumplimiento y cobertura por servidor en la última ejecución completada; la cobertura "
            "acompaña al score y no se interpreta como certificación."
        ),
        data=f2_data,
        draw_key="score_coverage",
    )

    f3_data = completed[["server_name", "run_date", "score", "coverage"]].sort_values(
        ["server_name", "run_date"]
    )
    figure3 = FigureSpec(
        number=3,
        slug="evolucion_cumplimiento",
        title="Evolución del cumplimiento por servidor",
        explanation=(
            "Permite observar mejoras y regresiones a lo largo de las ejecuciones. La evolución es "
            "descriptiva: no demuestra causalidad ni atribuye el cambio a una corrección concreta, "
            "pero ayuda a formular hipótesis y a detectar servidores que requieren seguimiento."
        ),
        description=(
            "Pequeños múltiplos, uno por servidor. Cada punto es una ejecución completada; la línea "
            "punteada marca 80 % como referencia visual. La escala es común para facilitar la "
            "comparación entre servidores."
        ),
        notes=(
            f"Fuente: {dataset.source_label}; {len(f3_data)} observaciones de "
            f"{f3_data['server_name'].nunique()} servidores. Los huecos indican ejecuciones no "
            "completadas o sin score calculable. " + dataset.metadata.get("warning", "")
        ),
        caption=(
            "Evolución del cumplimiento por servidor a lo largo de las ejecuciones completadas, con "
            "referencia visual en 80 %."
        ),
        data=f3_data,
        draw_key="trend",
    )

    control_agg = _control_aggregate(dataset)
    f4_data = control_agg[
        ["control_code", "control_title", "severity", "official", "pass_rate", "applicable"]
    ].sort_values("pass_rate")
    figure4 = FigureSpec(
        number=4,
        slug="tasa_aprobacion_control",
        title="Tasa de aprobación por control",
        explanation=(
            "Ordena los controles por dificultad observada y facilita la priorización. Los controles "
            "con menor tasa son candidatos a revisión, pero la decisión debe considerar severidad, "
            "exposición del servidor y esfuerzo de remediación; la tasa por sí sola no define el riesgo."
        ),
        description=(
            "Gráfico de puntos y tallos. La posición indica la tasa de aprobación sobre controles "
            "evaluados y el color la severidad. El tamaño del punto representa el número de casos "
            "evaluados; los controles internos se marcan con «(I)»."
        ),
        notes=(
            f"Fuente: {dataset.source_label}; {len(dataset.checks)} checks. Denominador = aprobados "
            "+ incumplidos; se excluyen no aplicables y no evaluados. El tamaño del punto es "
            "proporcional a los casos evaluados; «(I)» identifica controles internos sin referencia "
            "CIS oficial. " + dataset.metadata.get("warning", "")
        ),
        caption=(
            "Tasa de aprobación por control, ordenada de menor a mayor, con severidad, número de casos "
            "e identificación de controles internos."
        ),
        data=f4_data,
        draw_key="control_rate",
    )

    status_matrix = (
        findings.pivot_table(
            index="severity", columns="status", values="finding_id", aggfunc="count", fill_value=0
        )
        .reindex(SEVERITY_ORDER, fill_value=0)
    )
    for status in STATUS_ORDER:
        if status not in status_matrix.columns:
            status_matrix[status] = 0
    status_matrix = status_matrix[STATUS_ORDER]
    f5_data = status_matrix.reset_index().melt(
        id_vars="severity", var_name="status", value_name="count"
    )
    figure5 = FigureSpec(
        number=5,
        slug="hallazgos_severidad_estado",
        title="Hallazgos por severidad y estado",
        explanation=(
            "Resume la composición del backlog y la madurez del ciclo de vida. La severidad indica "
            "potencial impacto; el estado indica en qué punto del proceso está la respuesta. Juntos "
            "permiten distinguir riesgo abierto, trabajo en curso y deuda histórica."
        ),
        description=(
            "Barras horizontales apiladas por severidad. Cada segmento representa un estado del ciclo "
            "de vida y el total se anota al final. «Resuelto» y «Falso positivo» son cierres; «Riesgo "
            "aceptado» permanece activo."
        ),
        notes=(
            f"Fuente: {dataset.source_label}; {len(findings)} hallazgos únicos. "
            "Los conteos son hallazgos, no ocurrencias de auditoría. "
            + dataset.metadata.get("warning", "")
        ),
        caption=(
            "Distribución de hallazgos únicos por severidad y estado del ciclo de vida, con total por "
            "severidad."
        ),
        data=f5_data,
        draw_key="findings",
    )

    matrix = (
        dataset.checks.groupby(["server_name", "category"])
        .apply(
            lambda group: pd.Series(
                {
                    "pass_rate": (
                        100
                        * (group["status"] == "passed").sum()
                        / max(1, (group["status"].isin(["passed", "failed"])).sum())
                    ),
                    "evaluated": int(group["status"].isin(["passed", "failed"]).sum()),
                }
            ),
            include_groups=False,
        )
        .reset_index()
    )
    figure6 = FigureSpec(
        number=6,
        slug="mapa_calor_servidor_categoria",
        title="Mapa de calor de cumplimiento por servidor y categoría",
        explanation=(
            "Revela patrones que no se ven en promedios globales: un servidor puede cumplir bien en "
            "firewall y fallar sistemáticamente en actualizaciones, o una categoría puede ser débil en "
            "toda la muestra. El mapa orienta auditorías de seguimiento y discusiones de priorización."
        ),
        description=(
            "Filas: servidores. Columnas: categorías de control. El color y el número indican la tasa "
            "de aprobación agregada de todas las ejecuciones; los valores más oscuros corresponden a "
            "mayor cumplimiento. Las celdas con pocos casos deben interpretarse con cautela."
        ),
        notes=(
            f"Fuente: {dataset.source_label}; {len(dataset.checks)} checks agregados por servidor y "
            "categoría. Tasa = aprobados / (aprobados + incumplidos). "
            + dataset.metadata.get("warning", "")
        ),
        caption=(
            "Mapa de calor de tasa de aprobación por servidor y categoría de control, agregando todas "
            "las ejecuciones del periodo."
        ),
        data=matrix,
        draw_key="heatmap",
    )

    architecture_nodes = pd.DataFrame(
        [
            ("Usuarios", "Auditor, analista, administrador y observador"),
            ("Frontend", "React SPA y anexo Streamlit de publicación"),
            ("API", "FastAPI, RBAC, validación y orquestación"),
            ("PostgreSQL", "Controles, ejecuciones, evidencia y bitácora append-only"),
            ("Motor SSH", "Comandos estáticos de solo lectura y host key pinning"),
            ("Servidor Linux", "Objetivo autorizado; no se modifica"),
            ("LangChain + Ollama", "Propuesta JSON opcional, sin ejecución"),
            ("Revisión humana", "Aprobación o rechazo documentado"),
            ("n8n", "Programación de auditorías y reportes"),
        ],
        columns=["componente", "función"],
    )
    figure1 = FigureSpec(
        number=1,
        slug="arquitectura_referencia",
        title="Arquitectura de referencia y flujo de auditoría",
        explanation=(
            "Sitúa los límites de confianza del sistema: la consola no ejecuta comandos de corrección, "
            "el motor SSH solo lee configuración y la IA propone texto para revisión humana. Esta "
            "separación es una decisión de diseño central para reducir el riesgo operativo y explicar "
            "por qué la plataforma no modifica los servidores."
        ),
        description=(
            "Diagrama conceptual. La ruta principal va del usuario a la SPA, la API y PostgreSQL; el "
            "worker consulta el servidor por SSH de solo lectura. La IA es opcional y su salida pasa "
            "por revisión humana. n8n orquesta programaciones mediante API keys con alcance limitado."
        ),
        notes=(
            "Fuente y elaboración: figura conceptual propia. No representa una topología de despliegue "
            "específica ni incluye secretos. La IA no tiene herramientas de ejecución."
        ),
        caption=(
            "Arquitectura de referencia y flujo de auditoría: límites de confianza, lectura SSH, "
            "scoring, IA opcional y revisión humana."
        ),
        data=architecture_nodes,
        draw_key="architecture",
    )

    return {
        figure.slug: figure
        for figure in [figure1, figure2, figure3, figure4, figure5, figure6]
    }
