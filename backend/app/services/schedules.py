from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

try:  # pragma: no cover - croniter se usa si está disponible
    from croniter import croniter as _croniter
except ImportError:  # pragma: no cover
    _croniter = None


class ScheduleError(ValueError):
    pass


def _parse_field(field: str, minimum: int, maximum: int) -> set[int]:
    values: set[int] = set()
    if field in {"*", "?"}:
        return set(range(minimum, maximum + 1))
    for part in field.split(","):
        step = 1
        if "/" in part:
            part, step_raw = part.split("/", 1)
            try:
                step = int(step_raw)
            except ValueError as exc:
                raise ScheduleError("Paso de cron inválido.") from exc
            if step <= 0:
                raise ScheduleError("Paso de cron inválido.")
        if part in {"*", "?"}:
            start, end = minimum, maximum
        elif "-" in part:
            start_raw, end_raw = part.split("-", 1)
            try:
                start, end = int(start_raw), int(end_raw)
            except ValueError as exc:
                raise ScheduleError("Rango de cron inválido.") from exc
        else:
            try:
                start = end = int(part)
            except ValueError as exc:
                raise ScheduleError("Valor de cron inválido.") from exc
        if start < minimum or end > maximum or start > end:
            raise ScheduleError("Valor de cron fuera de rango.")
        values.update(range(start, end + 1, step))
    return values


def _next_native(expression: str, base: datetime) -> datetime:
    parts = expression.split()
    if len(parts) != 5:
        raise ScheduleError("El cron debe tener cinco campos.")
    minute = _parse_field(parts[0], 0, 59)
    hour = _parse_field(parts[1], 0, 23)
    day = _parse_field(parts[2], 1, 31)
    month = _parse_field(parts[3], 1, 12)
    weekday = _parse_field(parts[4].replace("7", "0"), 0, 6)
    current = base.replace(second=0, microsecond=0) + timedelta(minutes=1)
    for _ in range(60 * 24 * 366 * 5):
        cron_weekday = (current.weekday() + 1) % 7  # domingo=0, lunes=1
        day_matches = current.day in day
        weekday_matches = cron_weekday in weekday
        if parts[2] != "*" and parts[4] != "*":
            calendar_matches = day_matches or weekday_matches
        else:
            calendar_matches = day_matches and weekday_matches
        if (
            current.minute in minute
            and current.hour in hour
            and current.month in month
            and calendar_matches
        ):
            return current
        current += timedelta(minutes=1)
    raise ScheduleError("No fue posible calcular la próxima ejecución.")


def next_run(cron_expression: str, timezone_name: str) -> datetime:
    try:
        zone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise ScheduleError("Zona horaria inválida.") from exc
    now = datetime.now(zone)
    try:
        if _croniter is not None:
            value = _croniter(cron_expression, now).get_next(datetime)
        else:
            value = _next_native(cron_expression, now)
    except (ValueError, KeyError) as exc:
        raise ScheduleError("Expresión cron inválida.") from exc
    return value.astimezone(timezone.utc)
