from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import pandas as pd

SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"]
SEVERITY_LABEL = {
    "critical": "Crítica",
    "high": "Alta",
    "medium": "Media",
    "low": "Baja",
    "info": "Informativa",
}
STATUS_ORDER = [
    "detected",
    "in_review",
    "correction_planned",
    "fixed_pending_validation",
    "risk_accepted",
    "resolved",
    "false_positive",
]
STATUS_LABEL = {
    "detected": "Detectado",
    "in_review": "En revisión",
    "correction_planned": "Corrección planificada",
    "fixed_pending_validation": "Pendiente de validación",
    "risk_accepted": "Riesgo aceptado",
    "resolved": "Resuelto",
    "false_positive": "Falso positivo",
}
CHECK_STATUS_LABEL = {
    "passed": "Aprobado",
    "failed": "Incumplido",
    "not_applicable": "No aplica",
    "not_evaluated": "No evaluado",
}
ENVIRONMENT_LABEL = {
    "production": "Producción",
    "staging": "Pruebas",
    "development": "Desarrollo",
}


@dataclass
class Dataset:
    source_type: str
    source_key: str
    source_label: str
    source_note: str
    organization: str
    generated_at: datetime
    servers: pd.DataFrame
    runs: pd.DataFrame
    checks: pd.DataFrame
    controls: pd.DataFrame
    findings: pd.DataFrame
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_synthetic(self) -> bool:
        return self.source_type == "synthetic"

    @property
    def provenance_short(self) -> str:
        return "dataset sintético reproducible" if self.is_synthetic else "PostgreSQL institucional"


@dataclass
class TableSpec:
    number: int
    slug: str
    title: str
    explanation: str
    description: str
    notes: str
    caption: str
    dataframe: pd.DataFrame
    column_labels: dict[str, str]
    percent_columns: list[str] = field(default_factory=list)
    number_columns: list[str] = field(default_factory=list)
    column_widths: list[float] = field(default_factory=list)

    @property
    def label(self) -> str:
        return f"Tabla {self.number}"

    @property
    def full_title(self) -> str:
        return f"Tabla {self.number}. {self.title}"

    @property
    def filename_base(self) -> str:
        return f"tabla_{self.number:02d}_{self.slug}"


@dataclass
class FigureSpec:
    number: int
    slug: str
    title: str
    explanation: str
    description: str
    notes: str
    caption: str
    data: pd.DataFrame
    draw_key: str

    @property
    def label(self) -> str:
        return f"Figura {self.number}"

    @property
    def full_title(self) -> str:
        return f"Figura {self.number}. {self.title}"

    @property
    def filename_base(self) -> str:
        return f"figura_{self.number:02d}_{self.slug}"
