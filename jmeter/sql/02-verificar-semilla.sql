-- 02-verificar-semilla.sql
-- Comprueba que la base tiene volumen suficiente para medir el Dashboard.

SELECT 'organizaciones'          AS metrica, count(*)::text AS valor FROM organizations
UNION ALL SELECT 'servidores SRV-JM',      count(*)::text FROM servers WHERE name LIKE 'SRV-JM-%'
UNION ALL SELECT 'auditorias completadas', count(*)::text FROM audit_runs r
  JOIN servers s ON s.id = r.server_id AND s.name LIKE 'SRV-JM-%'
  WHERE r.status = 'completed'
UNION ALL SELECT 'checks',                 count(*)::text FROM hardening_checks hc
  JOIN audit_runs r ON r.id = hc.run_id
  JOIN servers s ON s.id = r.server_id AND s.name LIKE 'SRV-JM-%'
UNION ALL SELECT 'checks failed',          count(*)::text FROM hardening_checks hc
  JOIN audit_runs r ON r.id = hc.run_id
  JOIN servers s ON s.id = r.server_id AND s.name LIKE 'SRV-JM-%'
  WHERE hc.status = 'failed'
UNION ALL SELECT 'findings activos',       count(*)::text FROM findings f
  JOIN servers s ON s.id = f.server_id AND s.name LIKE 'SRV-JM-%'
  WHERE f.status NOT IN ('resolved', 'false_positive')
UNION ALL SELECT 'recomendaciones pendientes', count(*)::text
  FROM remediation_recommendations rr
  JOIN findings f ON f.id = rr.finding_id
  JOIN servers s ON s.id = f.server_id AND s.name LIKE 'SRV-JM-%'
  WHERE rr.status = 'pending_review';

-- Rango de fechas: debe caer dentro de los ultimos 30 dias (rango por defecto del Dashboard)
SELECT min(r.created_at) AS primer_run,
       max(r.created_at) AS ultimo_run,
       count(*)        AS runs_en_ventana
FROM audit_runs r
JOIN servers s ON s.id = r.server_id AND s.name LIKE 'SRV-JM-%'
WHERE r.created_at >= now() - interval '30 days';

-- Score promedio: debe ser un valor intermedio, no 0 ni 100
SELECT round(avg(score), 2) AS score_promedio,
       min(score)           AS score_min,
       max(score)           AS score_max
FROM audit_runs r
JOIN servers s ON s.id = r.server_id AND s.name LIKE 'SRV-JM-%'
WHERE r.status = 'completed';
