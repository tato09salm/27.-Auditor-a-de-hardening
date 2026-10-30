"""Fórmula de cumplimiento transparente y testeable.

score = aprobados / (aprobados + incumplidos) * 100

No aplicables y no evaluados quedan fuera del denominador, pero se informan por
separado. Si no hay controles aplicables evaluados, el score es None (nunca 100).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Iterable

from app.enums import CheckStatus, Severity


@dataclass(frozen=True)
class Score:
    total: int
    applicable: int
    passed: int
    failed: int
    not_applicable: int
    not_evaluated: int
    score: Decimal | None
    coverage: Decimal

    def as_dict(self) -> dict:
        return {
            "total": self.total,
            "applicable": self.applicable,
            "passed": self.passed,
            "failed": self.failed,
            "not_applicable": self.not_applicable,
            "not_evaluated": self.not_evaluated,
            "score": float(self.score) if self.score is not None else None,
            "coverage": float(self.coverage),
        }


def calculate_score(statuses: Iterable[CheckStatus | str]) -> Score:
    values = [status.value if isinstance(status, CheckStatus) else status for status in statuses]
    total = len(values)
    passed = values.count(CheckStatus.PASSED.value)
    failed = values.count(CheckStatus.FAILED.value)
    not_applicable = values.count(CheckStatus.NOT_APPLICABLE.value)
    not_evaluated = values.count(CheckStatus.NOT_EVALUATED.value)
    applicable = passed + failed
    score: Decimal | None
    if applicable == 0:
        score = None
    else:
        score = (Decimal(passed) / Decimal(applicable) * Decimal(100)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    coverage = (
        (Decimal(applicable) / Decimal(total) * Decimal(100)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        if total
        else Decimal("0.00")
    )
    return Score(
        total=total,
        applicable=applicable,
        passed=passed,
        failed=failed,
        not_applicable=not_applicable,
        not_evaluated=not_evaluated,
        score=score,
        coverage=coverage,
    )


def severity_counts(findings: Iterable[tuple[Severity | str, int]]) -> dict[str, int]:
    result = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for severity, count in findings:
        key = severity.value if isinstance(severity, Severity) else severity
        if key in result:
            result[key] += count
    return result
