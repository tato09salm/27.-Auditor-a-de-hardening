-- 00-crear-admin-demo.sql
-- Crea una organizacion y un administrador SOLO para el entorno de pruebas.
-- Credenciales: admin@demo.com / Auditoria2026!
-- No ejecutar en produccion.

BEGIN;

INSERT INTO organizations (name, slug, is_active)
SELECT 'Demo JMeter', 'demo-jmeter', true
WHERE NOT EXISTS (SELECT 1 FROM organizations WHERE slug = 'demo-jmeter');

INSERT INTO users (
  organization_id, email, full_name, password_hash,
  is_active, must_change_password, password_changed_at
)
SELECT o.id, 'admin@demo.com', 'Administrador Demo',
       '$2b$12$AxFmV1uZiuHIevevj8ZWz.7I3/IlXZjHAbfHTHX9IFQavuG52Tk1O',
       true, false, now()
FROM organizations o
WHERE o.slug = 'demo-jmeter'
  AND NOT EXISTS (SELECT 1 FROM users WHERE email = 'admin@demo.com');

INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM users u
CROSS JOIN roles r
WHERE u.email = 'admin@demo.com'
  AND r.code = 'admin'
  AND NOT EXISTS (
    SELECT 1 FROM user_roles ur WHERE ur.user_id = u.id AND ur.role_id = r.id
  );

COMMIT;

SELECT u.id, u.email, o.name AS organizacion, r.code AS rol
FROM users u
JOIN organizations o ON o.id = u.organization_id
JOIN user_roles ur ON ur.user_id = u.id
JOIN roles r ON r.id = ur.role_id
WHERE u.email = 'admin@demo.com';
