"""Ejecuta un archivo .sql contra la base de datos configurada en .env.

Pensado para un entorno nativo (sin Docker y sin psql instalado).

Uso:
    python .\\jmeter\\scripts\\run_sql.py .\\jmeter\\sql\\02-verificar-semilla.sql
"""

from __future__ import annotations

import sys
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parents[2]
DEFAULTS = {
    "DB_HOST": "127.0.0.1",
    "DB_PORT": "5432",
    "DB_NAME": "27auditoria",
    "DB_USER": "postgres",
    "DB_PASSWORD": "",
}


def load_env() -> dict[str, str]:
    values: dict[str, str] = {}
    for name in (ROOT / ".env", ROOT / ".env.example"):
        if not name.exists():
            continue
        for raw in name.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values.setdefault(key.strip(), value.strip())
        break
    for key, value in DEFAULTS.items():
        values.setdefault(key, value)
    return values


def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: python jmeter/scripts/run_sql.py <archivo.sql>")
        return 2

    script = Path(sys.argv[1])
    if not script.exists():
        print(f"No existe el archivo: {script}")
        return 2

    env = load_env()
    dsn = {
        "host": env["DB_HOST"],
        "port": env["DB_PORT"],
        "dbname": env["DB_NAME"],
        "user": env["DB_USER"],
        "password": env["DB_PASSWORD"],
    }
    print(f"Base: {dsn['user']}@{dsn['host']}:{dsn['port']}/{dsn['dbname']}")

    sql = script.read_text(encoding="utf-8")
    try:
        with psycopg.connect(**dsn, autocommit=True) as conn:
            conn.add_notice_handler(lambda diag: print(f"NOTICE: {diag.message_primary}"))
            with conn.cursor() as cur:
                cur.execute(sql)
                if cur.description:
                    headers = [col.name for col in cur.description]
                    print(" | ".join(headers))
                    for row in cur.fetchall():
                        print(" | ".join("" if v is None else str(v) for v in row))
    except psycopg.Error as exc:
        print(f"ERROR: {exc}")
        return 1

    print(f"OK: {script.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
