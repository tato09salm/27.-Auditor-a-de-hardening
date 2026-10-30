# Operación, respaldo y recuperación

## 1. Servicios

| Servicio | Puerto local | Salud |
| --- | --- | --- |
| Frontend Vite/Nginx | 5173 / 8080 | `GET /healthz` en Nginx |
| API | 8000 | `GET /api/v1/health` |
| PostgreSQL | 5432 | `pg_isready` |
| n8n | 5678 | Interfaz `/healthz` |
| Ollama | 11434 | `GET /api/tags` |

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
docker compose ps
docker compose logs -f backend
```

## 2. Respaldos

### 2.1 PostgreSQL

Use `pg_dump` con formato custom:

```powershell
$env:PGPASSWORD = "<DB_PASSWORD>"
& "C:\Program Files\PostgreSQL\17\bin\pg_dump.exe" `
  -h localhost -U postgres -Fc -d 27auditoria `
  -f "D:\backups\27auditoria_$(Get-Date -Format yyyyMMdd_HHmm).dump"
```

Programe una tarea diaria y verifique el código de salida. Conserve al menos:

- 7 copias diarias;
- 4 semanales;
- 12 mensuales;
- una copia fuera del host.

### 2.2 Claves y configuración

Respalde por separado y cifrado:

- `FERNET_KEY` (sin ella no se descifran credenciales);
- `SECRET_KEY` (cambia e invalida sesiones);
- `N8N_ENCRYPTION_KEY`;
- `.env` completo;
- certificados TLS.

No guarde estas claves junto al dump de PostgreSQL en el mismo medio sin cifrado.

### 2.3 Reportes

Los reportes se guardan en `backend/generated/` o en el volumen `reports_data`. Copie el directorio y
conserve los checksums SHA-256 de la tabla `reports`.

### 2.4 n8n

Si usa PostgreSQL, respalde la base `n8n` con el mismo procedimiento:

```powershell
& "C:\Program Files\PostgreSQL\17\bin\pg_dump.exe" `
  -h localhost -U postgres -Fc -d n8n -f "D:\backups\n8n.dump"
```

Las credenciales de n8n están cifradas con `N8N_ENCRYPTION_KEY`; sin esa clave el backup es
inservible.

## 3. Restauración

### 3.1 Prueba en una base temporal

Nunca restaure directamente sobre producción sin haber probado.

```powershell
$env:PGPASSWORD = "<DB_PASSWORD>"
& "C:\Program Files\PostgreSQL\17\bin\createdb.exe" -h localhost -U postgres 27auditoria_restore
& "C:\Program Files\PostgreSQL\17\bin\pg_restore.exe" `
  -h localhost -U postgres -d 27auditoria_restore --clean --if-exists `
  "D:\backups\27auditoria_20261029_0300.dump"
```

Ajuste `DB_NAME=27auditoria_restore`, arranque una instancia de prueba y valide:

- login y permisos;
- cantidad de servidores, runs y hallazgos;
- descarga de reportes;
- bitácora append-only;
- credenciales SSH (prueba de conexión).

### 3.2 Restauración productiva

1. Detenga backend y n8n.
2. Realice un backup del estado actual.
3. Restaure la base.
4. Restaure el volumen de reportes.
5. Restaure `.env` y claves.
6. Arranque backend (`alembic upgrade head` es idempotente).
7. Verifique salud y login.
8. Reactive n8n.

## 4. Migraciones

```powershell
cd backend
python -m alembic current
python -m alembic upgrade head
```

Antes de actualizar:

- backup;
- leer la migración;
- probar en una copia;
- revisar `alembic check` para detectar drift.

No ejecute `downgrade` en producción sin un plan específico: puede eliminar tablas y datos.

## 5. Tareas periódicas

### Diarias

- Revisar salud de API, PostgreSQL y n8n.
- Revisar fallos de auditorías y runs atascadas.
- Revisar hallazgos críticos/altos nuevos.
- Confirmar backups.

### Semanales

- Revisar recomendaciones pendientes.
- Revisar aceptaciones de riesgo vencidas.
- Revisar intentos de login fallidos y `auth.refresh.reuse_detected`.
- Revisar espacio de reportes.

### Mensuales

- Probar restauración en una base temporal.
- Revisar roles y usuarios inactivos.
- Rotar API keys de n8n según política.
- Revisar dependencias (`pip-audit`, `npm audit`).
- Revisar autorizaciones de servidores y CIDRs.
- Revisar la deriva entre benchmark y perfil.

## 6. Runs atascadas

Al arrancar, las runs `queued`/`running` con más de 2 horas se marcan como fallidas. Para revisar
manualmente:

```sql
SELECT id, server_id, status, started_at, error_message
FROM audit_runs
WHERE status IN ('queued', 'running')
ORDER BY created_at;
```

No cambie estados a mano sin documentar el incidente. La restricción única de run activa impide crear
otra hasta resolver la anterior.

## 7. Rotación de secretos

| Secreto | Procedimiento | Efecto |
| --- | --- | --- |
| `SECRET_KEY` | Cambiar y reiniciar | Invalida access/refresh tokens |
| `FERNET_KEY` | Requiere re-cifrar credenciales; no está automatizado | Sin re-cifrado se pierden credenciales |
| API keys n8n | Crear nueva, actualizar n8n, revocar anterior | Corte breve de automatización |
| Contraseña PostgreSQL | Cambiar en DB y `.env`, reiniciar backend | Corte breve |
| `N8N_ENCRYPTION_KEY` | No rotar sin migración de n8n | n8n pierde credenciales |
| Credenciales SSH | Actualizar en el servidor y en la consola | Requiere prueba |

La rotación de `FERNET_KEY` no está implementada en la v1. Planifique una ventana y un script de
re-cifrado antes de cambiarla.

## 8. Monitoreo mínimo

- `GET /api/v1/health` cada minuto.
- Errores 5xx en el proxy.
- Runs fallidas por servidor.
- Crecimiento de `audit_logs`, `hardening_checks` y reportes.
- Latencia de generación de reportes.
- Estado de Ollama (si se usa).
- Espacio en disco y backups.

No exponga métricas con datos sensibles en un endpoint público.

## 9. Retención

La v1 conserva todo el histórico. Defina una política antes de producción:

- runs y checks: 12-24 meses;
- reportes: según obligación legal;
- bitácora: mínimo 12 meses o más;
- logs de proxy: 90 días;
- backups: según RPO/RTO.

Cualquier purga debe preservar integridad referencial y coordinarse con la bitácora.

## 10. Actualización de la aplicación

1. Backup.
2. Descargar nueva versión.
3. Revisar migraciones y notas.
4. `docker compose build` o actualizar entorno virtual.
5. `alembic upgrade head`.
6. Reiniciar backend y frontend.
7. Verificar salud, login, una auditoría programada y una descarga de reporte.
8. Revisar logs y rollback si es necesario.

## 11. Contactos y escalamiento

Defina:

- propietario de la plataforma;
- responsable de infraestructura;
- responsable de seguridad;
- canal de incidentes;
- proveedor de n8n/Ollama si aplica.
