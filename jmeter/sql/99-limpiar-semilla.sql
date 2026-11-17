-- 99-limpiar-semilla.sql
-- Borra SOLO los datos sinteticos de las pruebas JMeter (servidores SRV-JM-*).
-- No toca organizaciones, usuarios, benchmarks ni controles.

BEGIN;

DELETE FROM remediation_reviews rr
USING remediation_recommendations rc, findings f, servers s
WHERE rr.recommendation_id = rc.id
  AND rc.finding_id = f.id
  AND f.server_id = s.id
  AND s.name LIKE 'SRV-JM-%';

DELETE FROM remediation_recommendations rc
USING findings f, servers s
WHERE rc.finding_id = f.id
  AND f.server_id = s.id
  AND s.name LIKE 'SRV-JM-%';

DELETE FROM finding_events fe
USING findings f, servers s
WHERE fe.finding_id = f.id
  AND f.server_id = s.id
  AND s.name LIKE 'SRV-JM-%';

DELETE FROM findings f
USING servers s
WHERE f.server_id = s.id
  AND s.name LIKE 'SRV-JM-%';

DELETE FROM hardening_checks hc
USING audit_runs r, servers s
WHERE hc.run_id = r.id
  AND r.server_id = s.id
  AND s.name LIKE 'SRV-JM-%';

DELETE FROM scheduled_audits sa
USING servers s
WHERE sa.server_id = s.id
  AND s.name LIKE 'SRV-JM-%';

DELETE FROM audit_runs r
USING servers s
WHERE r.server_id = s.id
  AND s.name LIKE 'SRV-JM-%';

DELETE FROM server_credentials sc
USING servers s
WHERE sc.server_id = s.id
  AND s.name LIKE 'SRV-JM-%';

DELETE FROM servers s WHERE s.name LIKE 'SRV-JM-%';

DELETE FROM audit_profiles p
WHERE p.name = 'Perfil carga JMeter'
  AND NOT EXISTS (SELECT 1 FROM audit_runs r WHERE r.profile_id = p.id);

COMMIT;

SELECT 'restantes servers SRV-JM-%' AS control,
       count(*) AS filas
FROM servers WHERE name LIKE 'SRV-JM-%';
