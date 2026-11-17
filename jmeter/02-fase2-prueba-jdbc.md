# Fase 2 — Prueba con base de datos (PostgreSQL)

**Fecha:** 17/11/2026
**Estado:** completada
**Plan:** `jmeter/plans/01-jdbc-hardening.jmx`

## 1. Objetivo

Medir el rendimiento de una consulta compleja contra PostgreSQL 17 mientras
aumenta el numero de conexiones concurrentes. Es la primera de las dos pruebas
obligatorias de la practica.

## 2. Estructura del plan

```
Test Plan: Practica JMeter - Prueba JDBC
├─ JDBC Connection Configuration (miBD)
├─ Thread Group "Hilos JDBC"
│    └─ JDBC Request: Controles mas incumplidos (JOIN + GROUP BY)
│         ├─ Aggregate Report
│         └─ Summary Report
```

## 3. Configuracion JDBC

| Campo | Valor |
|---|---|
| Variable Name | `miBD` |
| Database URL | `jdbc:postgresql://127.0.0.1:5432/27auditoria` |
| JDBC Driver class | `org.postgresql.Driver` |
| Username | `postgres` |
| Password | `${__P(db.password,)}` (se pasa al ejecutar, no esta en el archivo) |
| Max Number of Connections | **30** |
| Transaction isolation | DEFAULT |
| Connection age | 0 (sin reciclado forzado) |

El pool esta a 30 a proposito: es el mismo tamano que el pool de la aplicacion
(`DB_POOL_SIZE=10` + `DB_MAX_OVERFLOW=20`), asi el resultado es comparable con
la prueba HTTP.

## 4. Consulta usada

JOIN de 4 tablas, `GROUP BY`, `FILTER`, `AVG` y agregacion porcentual:

```sql
SELECT c.code, c.title, c.category, c.severity,
       COUNT(*) FILTER (WHERE h.status = 'failed') AS fallos,
       COUNT(*)                                    AS evaluaciones,
       ROUND(100.0 * COUNT(*) FILTER (WHERE h.status = 'failed') / COUNT(*), 1) AS pct_fallo,
       ROUND(AVG(h.duration_ms), 0)                AS ms_prom
FROM hardening_checks h
JOIN cis_controls c ON c.id = h.control_id
JOIN audit_runs   r ON r.id = h.run_id
JOIN servers      s ON s.id = r.server_id
WHERE r.status = 'completed'
  AND s.is_active
  AND r.created_at >= now() - interval '30 days'
GROUP BY c.code, c.title, c.category, c.severity
ORDER BY fallos DESC
LIMIT 10;
```

Las otras dos consultas de respaldo estan en `jmeter/sql/03-consultas-complejas.sql`.

## 5. Como ejecutarla

### Opcion A — Interfaz grafica (para las capturas)

1. Doble clic en `jmeter\scripts\abrir-jmeter.cmd` (abre JMeter con el tema
   claro y la contrasena de la BD ya cargada).
2. `File > Open` → `jmeter\plans\01-jdbc-hardening.jmx`.
3. Verificar que `JDBC Connection Configuration` muestre `miBD` y el pool en 30.
4. Cambiar los hilos en el Thread Group (10, 25, 50, ...).
5. Ejecutar con el boton verde y capturar el **Aggregate Report**.

> Si abre JMeter directamente sin el `.cmd`, el password llega vacio y la
> conexion falla. Use el `.cmd` o pase `-Jdb.password=...` al arrancar.

### Opcion B — Consola (para el reporte HTML)

```powershell
.\jmeter\scripts\run-jdbc.ps1 -Threads 100  -RampUp 10 -Duration 45 -Label jdbc2_100h
.\jmeter\scripts\run-jdbc.ps1 -Threads 150  -RampUp 10 -Duration 45 -Label jdbc2_150h
.\jmeter\scripts\run-jdbc.ps1 -Threads 200  -RampUp 10 -Duration 45 -Label jdbc2_200h
.\jmeter\scripts\run-jdbc.ps1 -Threads 1000 -RampUp 20 -Duration 45 -Label jdbc2_1000h
```

El script lee `DB_PASSWORD` de `.env`, ejecuta el plan y deja:

- `jmeter/resultados/<etiqueta>.jtl`
- `jmeter/reportes/<etiqueta>/index.html`

## 6. Resultado de la corrida base (10 hilos)

| Escalon | Hilos | Error % | Promedio | p95 | Throughput |
|---|---|---|---|---|---|
| jdbc2_100h | 100 | 0,00 % | 451 ms | 2 022 ms | 206,1 req/s |
| jdbc2_150h | 150 | 0,05 % | 720 ms | 2 313 ms | 194,7 req/s |
| jdbc2_200h | 200 | 0,41 % | 850 ms | 3 452 ms | 240,9 req/s |
| jdbc2_250h | 250 | 0,68 % | 1 032 ms | 4 887 ms | 231,3 req/s |
| jdbc2_300h | 300 | 1,49 % | 1 412 ms | 5 986 ms | 211,2 req/s |
| jdbc2_400h | 400 | 2,26 % | 1 380 ms | 6 526 ms | 283,0 req/s |
| jdbc2_1000h | 1000 | 14,61 % | 3 262 ms | 10 002 ms | 317,1 req/s |

Ramp-up 10 s (20 s en 1000) y duracion 45 s en todos. El primer error aparece a
los 150 hilos; el ultimo escalon con 0 % es **100 hilos**.

Causa del error: `java.sql.SQLException: Cannot get a connection, pool error
Timeout waiting for idle object, borrowMaxWaitDuration=PT10S`. Las 30 conexiones
del pool se agotan y las peticiones esperan 10 s antes de fallar.

## 7. Evidencias a capturar (fondo claro)

- [ ] Arbol del Test Plan completo
- [ ] `JDBC Connection Configuration` con `miBD`, URL y pool 30
- [ ] `JDBC Request` con la consulta visible
- [ ] Thread Group con el numero de hilos
- [ ] Aggregate Report de cada escalon
- [ ] Reporte HTML generado

## 8. Siguiente paso

Fase 3: plan HTTP del modulo Dashboard (`02-http-dashboard.jmx`), con login
unico en `setUp Thread Group` y token reutilizado por todos los hilos.
