-- 03-consultas-complejas.sql
-- Consultas de la practica JDBC. Ejecutables en psql, DBeaver o en el JDBC Request.
-- Todas usan JOIN + GROUP BY y evitan SELECT *.

-- 1) Controles mas incumplidos (la que usa el plan 01-jdbc-hardening.jmx)
SELECT c.code,
       c.title,
       c.category,
       c.severity,
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

-- 2) Tendencia semanal del score por familia de sistema operativo
SELECT date_trunc('week', r.created_at)::date        AS semana,
       s.os_family,
       COUNT(*)                                      AS auditorias,
       ROUND(AVG(r.score), 2)                        AS score_promedio,
       ROUND(AVG(r.failed_count), 1)                 AS fallos_promedio,
       ROUND(100.0 * SUM(r.passed_count) / NULLIF(SUM(r.applicable_count), 0), 2) AS cobertura
FROM audit_runs r
JOIN servers s ON s.id = r.server_id
WHERE r.status = 'completed'
  AND r.created_at >= now() - interval '30 days'
GROUP BY 1, 2
ORDER BY 1 DESC, 2;

-- 3) Hallazgos abiertos por severidad y servidor (con subconsulta)
SELECT s.name,
       s.environment,
       f.severity,
       COUNT(*) AS abiertos,
       MIN(f.first_seen_at)::date AS mas_antiguo,
       (SELECT ROUND(AVG(r2.score), 2)
          FROM audit_runs r2
         WHERE r2.server_id = s.id AND r2.status = 'completed') AS score_servidor
FROM findings f
JOIN servers s ON s.id = f.server_id
WHERE f.status NOT IN ('resolved', 'false_positive')
GROUP BY s.id, s.name, s.environment, f.severity
HAVING COUNT(*) >= 2
ORDER BY abiertos DESC, s.name
LIMIT 25;
