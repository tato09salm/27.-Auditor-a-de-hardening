# Fase 1 — Preparacion del entorno y datos de prueba

**Fecha:** 17/11/2026
**Estado:** completada

## 1. Que se hizo

| Paso | Resultado |
|---|---|
| PostgreSQL 17 local en `127.0.0.1:5432` | operativo |
| Base `27auditoria` | existente, esquema creado, catalogos CIS cargados (1 benchmark, 14 controles) |
| Organizacion de prueba | `Demo JMeter` (slug `demo-jmeter`) |
| Administrador de prueba | `admin@demo.com` / `Auditoria2026!` |
| Servidores sinteticos | 60 (`SRV-JM-001` a `SRV-JM-060`) |
| Auditorias completadas | 840 (14 por servidor, ultimos 14 dias) |
| Resultados de control | 11 760 (`hardening_checks`) |
| Hallazgos activos | 216 |
| Recomendaciones pendientes | 55 |
| Backend FastAPI | iniciado en `http://127.0.0.1:8000` |

> **Solo entorno de prueba.** Las credenciales y los datos son sinteticos. No
> usar este `.env` ni esta semilla en produccion.

## 2. Archivos creados

| Archivo | Funcion |
|---|---|
| `jmeter/sql/00-crear-admin-demo.sql` | organizacion + administrador de prueba |
| `jmeter/sql/01-seed-datos-prueba.sql` | volumen sintetico (servidores, auditorias, checks, hallazgos) |
| `jmeter/sql/02-verificar-semilla.sql` | comprobacion de volumen |
| `jmeter/sql/99-limpiar-semilla.sql` | borra solo los datos `SRV-JM-*` |
| `jmeter/scripts/run_sql.py` | ejecuta cualquier `.sql` sin Docker ni `psql` |
| `jmeter/resultados/escalones.csv` | tabla de escalones para el informe |

## 3. Como reproducirlo (sin Docker)

Stack nativo: PostgreSQL 17 y FastAPI instalados en el equipo. Ejecute desde la
raiz del proyecto.

```powershell
# 1. Administrador de prueba (solo si la base no tiene organizacion)
python .\jmeter\scripts\run_sql.py .\jmeter\sql\00-crear-admin-demo.sql

# 2. Semilla de volumen
python .\jmeter\scripts\run_sql.py .\jmeter\sql\01-seed-datos-prueba.sql

# 3. Verificacion
python .\jmeter\scripts\run_sql.py .\jmeter\sql\02-verificar-semilla.sql

# 4. Backend (si no esta corriendo)
cd .\backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

`jmeter/scripts/run_sql.py` lee la conexion desde `.env` (`DB_HOST`, `DB_PORT`,
`DB_NAME`, `DB_USER`, `DB_PASSWORD`) y ejecuta el archivo con `psycopg`, sin
necesidad de instalar el cliente `psql`.

## 4. Verificacion de volumen

Resultado de `02-verificar-semilla.sql`:

| Metrica | Valor |
|---|---|
| Servidores `SRV-JM-*` | 60 |
| Auditorias completadas | 840 |
| Checks | 11 760 |
| Checks fallidos | 3 066 |
| Hallazgos activos | 216 |
| Recomendaciones pendientes | 55 |

Criterio de desbloqueo de la Fase 0: cumplido. La base ya no esta vacia y el
Dashboard tiene volumen real que agregar.

### 4.1 Medicion del Dashboard (17/11/2026)

| Peticion | Tiempo |
|---|---|
| `GET /api/v1/dashboard` (1) | 405 ms |
| `GET /api/v1/dashboard` (2) | 206 ms |
| `GET /api/v1/dashboard` (3) | 243 ms |
| `GET /api/v1/dashboard` (4) | 237 ms |
| `GET /api/v1/dashboard` (5) | 324 ms |
| `GET /api/v1/findings?page=1&page_size=50` | 45 ms |

Respuesta del Dashboard: `audits_in_period=840`, `total_servers=60`,
`average_score=70.48`. Score promedio en base: 70.38 (min 16.67, max 100.00).

Esto es lo que hace valida la prueba: con un solo usuario el endpoint tarda
~250 ms; al subir hilos, ese costo compite por el pool de 30 conexiones y por
los 40 hilos de Starlette, que es exactamente el punto de colapso a documentar.

## 5. Pendiente inmediato (parte de esta fase)

1. Copiar `postgresql-42.x.jar` a la carpeta `lib/` de JMeter y reiniciar JMeter.
2. Confirmar que el login devuelve token y que el Dashboard responde 200.
3. Poner JMeter en tema claro antes de la primera captura.

Con eso se cierra la Fase 1 y se puede empezar la Fase 2 (prueba JDBC).
