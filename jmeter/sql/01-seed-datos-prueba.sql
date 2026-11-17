-- 01-seed-datos-prueba.sql
-- Semilla sintetica de volumen para las pruebas de carga JMeter.
-- PostgreSQL 17. NO usar sobre datos reales.
--
-- Uso (entorno nativo, sin Docker):
--   python .\jmeter\scripts\run_sql.py .\jmeter\sql\01-seed-datos-prueba.sql
--
-- Genera: 60 servidores, 840 auditorias completadas (ultimos 14 dias),
-- ~40 000 hardening_checks, ~700 findings activos y recomendaciones.

BEGIN;

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM servers WHERE name = 'SRV-JM-001') THEN
    RAISE EXCEPTION 'La semilla ya existe. Ejecute 99-limpiar-semilla.sql para regenerarla.';
  END IF;
END $$;

-- Contexto: organizacion, usuario, perfil y benchmark existentes.
CREATE TEMP TABLE _ctx ON COMMIT DROP AS
SELECT o.id AS org_id,
       (SELECT u.id FROM users u
         WHERE u.organization_id = o.id
         ORDER BY u.created_at, u.id LIMIT 1) AS user_id,
       (SELECT p.id FROM audit_profiles p
         WHERE p.organization_id = o.id
         ORDER BY p.is_default DESC, p.created_at LIMIT 1) AS profile_id,
       b.id AS benchmark_id,
       b.version AS benchmark_version
FROM (SELECT id FROM organizations ORDER BY created_at, id LIMIT 1) o
CROSS JOIN (SELECT id, version FROM cis_benchmarks
            ORDER BY (os_family = 'ubuntu') DESC, created_at, id LIMIT 1) b;

DO $$
DECLARE
  v_org uuid; v_bm uuid; v_user uuid; v_profile uuid; v_controls int;
BEGIN
  SELECT org_id, benchmark_id, user_id, profile_id
    INTO v_org, v_bm, v_user, v_profile
    FROM _ctx;

  IF v_org IS NULL THEN
    RAISE EXCEPTION 'No hay organizacion. Cree el administrador desde la app antes de sembrar.';
  END IF;
  IF v_bm IS NULL THEN
    RAISE EXCEPTION 'No hay benchmark CIS en la base.';
  END IF;
  IF v_user IS NULL THEN
    RAISE EXCEPTION 'No hay usuario en la organizacion.';
  END IF;

  IF v_profile IS NULL THEN
    INSERT INTO audit_profiles
      (organization_id, benchmark_id, name, description, is_default, is_active, created_by_id)
    VALUES
      (v_org, v_bm, 'Perfil carga JMeter',
       'Perfil sintetico para pruebas de rendimiento', false, true, v_user)
    RETURNING id INTO v_profile;
    UPDATE _ctx SET profile_id = v_profile;
  END IF;

  SELECT count(*) INTO v_controls
    FROM cis_controls WHERE benchmark_id = v_bm AND is_active;
  IF v_controls = 0 THEN
    RAISE EXCEPTION 'El benchmark no tiene controles activos.';
  END IF;

  RAISE NOTICE 'Semilla: org=% controles_activos=%', v_org, v_controls;
END $$;

-- 1) Servidores sinteticos
INSERT INTO servers (
  organization_id, name, hostname, ip_address, os_family, os_version,
  environment, owner_area, connection_method, port, username, auth_method,
  status, is_active, is_simulated, authorization_confirmed,
  authorized_by_id, authorized_at, last_audit_at, default_profile_id,
  notes, created_by_id
)
SELECT c.org_id,
       'SRV-JM-' || lpad(i::text, 3, '0'),
       'srv-jm-' || i || '.lab.local',
       '10.90.' || ((i - 1) / 250) || '.' || (((i - 1) % 250) + 1),
       'ubuntu', '22.04',
       (ARRAY['production', 'staging', 'development'])[1 + (i % 3)],
       'Pruebas de carga',
       'simulated', 22, 'jmeter', 'key',
       'online', true, true, true,
       c.user_id, now(), now() - make_interval(days => i % 14),
       c.profile_id,
       'Servidor sintetico para pruebas JMeter',
       c.user_id
FROM _ctx c
CROSS JOIN generate_series(1, 60) AS i;

-- 2) Auditorias completadas: 14 por servidor, repartidas en los ultimos 14 dias
INSERT INTO audit_runs (
  organization_id, server_id, profile_id, benchmark_id, benchmark_version,
  status, trigger_type, triggered_by_id, started_at, finished_at,
  total_controls, is_simulated, summary, created_at
)
SELECT x.org_id, x.server_id, x.profile_id, x.benchmark_id, x.benchmark_version,
       'completed', 'automation', x.user_id,
       x.ts, x.ts + interval '40 seconds',
       x.total_controls, true, '{}'::jsonb, x.ts
FROM (
  SELECT c.org_id, s.id AS server_id, c.profile_id, c.benchmark_id,
         c.benchmark_version, c.user_id,
         now() - make_interval(
           days  => d,
           hours => (abs(hashtext(s.id::text || d::text)) % 10)
         ) AS ts,
         (SELECT count(*) FROM cis_controls ctl
           WHERE ctl.benchmark_id = c.benchmark_id AND ctl.is_active) AS total_controls
  FROM _ctx c
  JOIN servers s
    ON s.organization_id = c.org_id
   AND s.name LIKE 'SRV-JM-%'
  CROSS JOIN generate_series(0, 13) AS d
) x;

-- 3) Resultados de control: ~62% passed, ~26% failed, 7% N/A, 5% sin evaluar
INSERT INTO hardening_checks (
  run_id, control_id, status, severity, observed_value, evidence,
  command_executed, duration_ms, evaluated_at, created_at
)
SELECT r.id, ctl.id,
       CASE WHEN p < 62 THEN 'passed'
            WHEN p < 88 THEN 'failed'
            WHEN p < 95 THEN 'not_applicable'
            ELSE 'not_evaluated' END,
       ctl.severity,
       'valor sintetico observado',
       jsonb_build_object('origen', 'semilla-jmeter'),
       'chequeo-simulado',
       50 + (p * 7) % 450,
       r.created_at + interval '25 seconds',
       r.created_at + interval '25 seconds'
FROM audit_runs r
JOIN servers s
  ON s.id = r.server_id
 AND s.name LIKE 'SRV-JM-%'
JOIN cis_controls ctl
  ON ctl.benchmark_id = r.benchmark_id
 AND ctl.is_active
CROSS JOIN LATERAL (
  SELECT abs(hashtext(r.id::text || ctl.id::text)) % 100 AS p
) q;

-- 4) Agregados coherentes en audit_runs
UPDATE audit_runs r
SET total_controls        = a.total,
    applicable_count      = a.applicable,
    passed_count          = a.passed,
    failed_count          = a.failed,
    not_applicable_count  = a.na,
    not_evaluated_count   = a.ne,
    score                 = round(100.0 * a.passed / GREATEST(a.applicable, 1), 2)
FROM (
  SELECT run_id,
         count(*)                                                   AS total,
         count(*) FILTER (WHERE status IN ('passed', 'failed'))     AS applicable,
         count(*) FILTER (WHERE status = 'passed')                  AS passed,
         count(*) FILTER (WHERE status = 'failed')                  AS failed,
         count(*) FILTER (WHERE status = 'not_applicable')          AS na,
         count(*) FILTER (WHERE status = 'not_evaluated')           AS ne
  FROM hardening_checks
  GROUP BY run_id
) a
WHERE r.id = a.run_id;

-- 5) Ultima auditoria por servidor
CREATE TEMP TABLE _latest ON COMMIT DROP AS
SELECT DISTINCT ON (r.server_id)
       r.id AS run_id, r.server_id, r.organization_id, r.created_at
FROM audit_runs r
JOIN servers s
  ON s.id = r.server_id
 AND s.name LIKE 'SRV-JM-%'
WHERE r.status = 'completed'
ORDER BY r.server_id, r.created_at DESC, r.id;

UPDATE servers s
SET last_audit_at = l.created_at
FROM _latest l
WHERE s.id = l.server_id;

-- 6) Hallazgos activos (uno por servidor + control fallido en la ultima auditoria)
INSERT INTO findings (
  organization_id, server_id, control_id, first_seen_run_id, last_seen_run_id,
  status, severity, priority, title, description, owner_id, due_date,
  first_seen_at, last_seen_at, occurrence_count, created_at, updated_at
)
SELECT l.organization_id, l.server_id, hc.control_id, l.run_id, l.run_id,
       CASE (abs(hashtext(l.server_id::text || hc.control_id::text)) % 10)
         WHEN 0 THEN 'in_review'
         WHEN 1 THEN 'correction_planned'
         WHEN 2 THEN 'risk_accepted'
         WHEN 3 THEN 'fixed_pending_validation'
         ELSE 'detected'
       END,
       ctl.severity,
       CASE ctl.severity
         WHEN 'critical' THEN 1
         WHEN 'high'     THEN 2
         WHEN 'medium'   THEN 3
         ELSE 4
       END,
       ctl.code || ' - ' || ctl.title,
       'Incumplimiento sintetico del control ' || ctl.code
         || ' detectado en ' || s.hostname,
       c.user_id,
       current_date + 15,
       l.created_at, l.created_at,
       1 + (abs(hashtext(s.name || ctl.code)) % 5),
       l.created_at, l.created_at
FROM _latest l
JOIN hardening_checks hc
  ON hc.run_id = l.run_id
 AND hc.status = 'failed'
JOIN cis_controls ctl ON ctl.id = hc.control_id
JOIN servers s ON s.id = l.server_id
CROSS JOIN _ctx c
ON CONFLICT (server_id, control_id)
  WHERE status NOT IN ('resolved', 'false_positive')
  DO NOTHING;

-- 7) Recomendaciones pendientes de revision para ~1/3 de los hallazgos
INSERT INTO remediation_recommendations (
  organization_id, finding_id, source, provider, model, status,
  payload, confidence, validation_status, created_by_id
)
SELECT f.organization_id, f.id, 'reference', 'plantilla', 'referencia-interna',
       'pending_review',
       jsonb_build_object(
         'resumen', 'Aplicar el endurecimiento indicado por CIS',
         'pasos', jsonb_build_array(
           'Revisar el control ' || ctl.code,
           'Aplicar la guia de remediacion',
           'Revalidar con una auditoria'
         )
       ),
       0.80, 'validated', c.user_id
FROM findings f
JOIN cis_controls ctl ON ctl.id = f.control_id
JOIN servers s
  ON s.id = f.server_id
 AND s.name LIKE 'SRV-JM-%'
CROSS JOIN _ctx c
WHERE (abs(hashtext(f.id::text)) % 3) = 0;

COMMIT;

-- Resumen final
SELECT 'servers' AS tabla, count(*) AS filas FROM servers WHERE name LIKE 'SRV-JM-%'
UNION ALL SELECT 'audit_runs', count(*) FROM audit_runs r
  JOIN servers s ON s.id = r.server_id AND s.name LIKE 'SRV-JM-%'
UNION ALL SELECT 'hardening_checks', count(*) FROM hardening_checks hc
  JOIN audit_runs r ON r.id = hc.run_id
  JOIN servers s ON s.id = r.server_id AND s.name LIKE 'SRV-JM-%'
UNION ALL SELECT 'findings', count(*) FROM findings f
  JOIN servers s ON s.id = f.server_id AND s.name LIKE 'SRV-JM-%'
UNION ALL SELECT 'recommendations', count(*) FROM remediation_recommendations rr
  JOIN findings f ON f.id = rr.finding_id
  JOIN servers s ON s.id = f.server_id AND s.name LIKE 'SRV-JM-%';
