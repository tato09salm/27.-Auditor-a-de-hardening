# API

Base local: `http://127.0.0.1:8000/api/v1`

Documentación interactiva de desarrollo: `http://127.0.0.1:8000/api/docs` (deshabilitada en
producción).

## Convenciones

- JSON UTF-8; fechas ISO 8601 con zona horaria.
- Autenticación web: `Authorization: Bearer <access_token>`.
- Refresh: cookie `cis_refresh` `HttpOnly`, rotativa.
- Automatización: `X-API-Key: cisa_...` con scopes.
- Idempotencia opcional en auditorías: `X-Idempotency-Key: <8-100 chars>`.
- Paginación: `page` (1+) y `page_size` (1-200).
- Error uniforme:

```json
{
  "detail": "Mensaje legible",
  "code": "validation_error",
  "fields": [{"field": "email", "message": "Valor inválido", "type": "value_error"}],
  "request_id": "f2..."
}
```

Los errores de validación no devuelven el valor enviado, para no filtrar contraseñas.

## Autenticación y setup

| Método | Ruta | Permiso | Descripción |
| --- | --- | --- | --- |
| GET | `/setup/status` | público | Indica si ya existe un administrador |
| POST | `/setup/initialize` | público, solo primera vez | Crea organización, admin y perfil por defecto |
| POST | `/auth/login` | público, rate limited | Devuelve access token y cookie de refresco |
| POST | `/auth/refresh` | cookie | Rota la sesión y devuelve nuevo access token |
| POST | `/auth/logout` | cookie | Revoca la sesión de refresco |
| GET | `/auth/me` | autenticado | Datos del usuario |
| GET | `/users/me` | autenticado | Datos del usuario y permisos |
| POST | `/auth/change-password` | autenticado | Revoca todas las sesiones |

### Ejemplo de login

```powershell
$body = @{ email = "admin@example.com"; password = "..." } | ConvertTo-Json
$r = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/v1/auth/login `
  -ContentType "application/json" -Body $body -SessionVariable session
$headers = @{ Authorization = "Bearer $($r.access_token)" }
```

No hay credenciales de demostración. El administrador se crea en `/setup`.

## Usuarios y RBAC

| Método | Ruta | Permiso |
| --- | --- | --- |
| GET | `/users` | `users:read` |
| POST | `/users` | `users:manage` |
| GET | `/users/{id}` | `users:read` |
| PATCH | `/users/{id}` | `users:manage` |
| POST | `/users/{id}/reset-password` | `users:manage` |
| GET | `/roles` | `users:read` |
| GET | `/organizations/me` | `dashboard:read` |

No se permite desactivar la propia cuenta ni dejar la organización sin un administrador activo.

## Servidores

| Método | Ruta | Permiso |
| --- | --- | --- |
| GET | `/servers` | `servers:read` |
| POST | `/servers` | `servers:manage` |
| GET | `/servers/{id}` | `servers:read` |
| PATCH | `/servers/{id}` | `servers:manage` |
| POST | `/servers/{id}/authorize` | `servers:manage` |
| PUT | `/servers/{id}/credential` | `servers:manage` |
| POST | `/servers/{id}/test-connection` | `audits:execute` o `servers:manage` |

Crear un servidor SSH exige: IP, usuario, huella SHA256, credencial y confirmación explícita de
autorización. La respuesta nunca incluye la credencial.

```json
{
  "name": "Portal web",
  "hostname": "portal.empresa.local",
  "ip_address": "10.20.10.15",
  "os_family": "ubuntu",
  "os_version": "22.04",
  "environment": "production",
  "connection_method": "ssh",
  "port": 22,
  "username": "cis-auditor",
  "auth_method": "key",
  "host_key_fingerprint": "SHA256:...",
  "credential": {"secret": "-----BEGIN OPENSSH PRIVATE KEY-----..."},
  "default_profile_id": "uuid",
  "authorization_confirmed": true,
  "allow_private_target": true,
  "notes": "Autorizado por Infraestructura el 2026-10-01"
}
```

Cambiar hostname/IP/puerto/usuario/autenticación/huella revoca la autorización y exige confirmarla
de nuevo.

## Benchmarks y perfiles

| Método | Ruta | Permiso |
| --- | --- | --- |
| GET | `/benchmarks` | `profiles:read` |
| GET | `/benchmarks/{id}/controls` | `profiles:read` |
| GET | `/profiles` | `profiles:read` |
| GET | `/profiles/{id}` | `profiles:read` |
| POST | `/profiles` | `profiles:manage` |
| PATCH | `/profiles/{id}` | `profiles:manage` |

Un perfil referencia un benchmark y un subconjunto de controles. Las ejecuciones guardan la versión
del benchmark para no alterar el histórico.

## Auditorías

| Método | Ruta | Permiso |
| --- | --- | --- |
| POST | `/audits` | `audits:execute` |
| GET | `/audits` | `audits:read` |
| GET | `/audits/{id}` | `audits:read` |
| GET | `/schedules` | `audits:read` |
| POST | `/schedules` | `schedules:manage` |
| PATCH | `/schedules/{id}` | `schedules:manage` |
| DELETE | `/schedules/{id}` | `schedules:manage` |

`POST /audits` devuelve `202` con el run en estado `queued`. Una segunda ejecución con el mismo
servidor y una run activa devuelve `409 audit_in_progress`.

```json
{"server_id": "uuid", "profile_id": "uuid"}
```

El detalle incluye los checks, el comando estático ejecutado y la evidencia truncada a límites
seguros. Los controles no evaluados se muestran como tales.

## Hallazgos

| Método | Ruta | Permiso |
| --- | --- | --- |
| GET | `/findings` | `findings:read` |
| GET | `/findings/{id}` | `findings:read` |
| PATCH | `/findings/{id}` | `findings:manage` |

Filtros: `status`, `severity`, `server_id`, `owner_id`, `search`, `include_closed`, paginación.

Transiciones permitidas:

```text
detected -> in_review | correction_planned | risk_accepted | false_positive
in_review -> detected | correction_planned | risk_accepted | false_positive
correction_planned -> in_review | fixed_pending_validation | risk_accepted
fixed_pending_validation -> correction_planned | resolved | risk_accepted
risk_accepted -> detected | resolved
resolved -> detected
false_positive -> detected
```

El cierre normal requiere una comprobación posterior satisfactoria. Solo un administrador puede
cerrar sin ella, con una justificación de al menos 20 caracteres. `risk_accepted` requiere fecha
futura y justificación.

## Recomendaciones IA

| Método | Ruta | Permiso |
| --- | --- | --- |
| POST | `/findings/{id}/recommendations` | `recommendations:generate` |
| GET | `/recommendations` | `recommendations:read` |
| GET | `/recommendations/{id}` | `recommendations:read` |
| POST | `/recommendations/{id}/review` | `recommendations:review` |

La generación devuelve `503` si Ollama no está disponible y `502` si el modelo devuelve una
estructura inválida. Una propuesta con `validation_status = dangerous` no puede aprobarse.

```json
{
  "decision": "approved",
  "comments": "Revisado con backup, ventana y rollback. Se aplicará fuera de la plataforma."
}
```

**No existe endpoint para ejecutar los comandos.** La aprobación solo documenta la revisión.

## Reportes

| Método | Ruta | Permiso |
| --- | --- | --- |
| POST | `/reports` | `reports:generate` |
| GET | `/reports` | `reports:read` |
| GET | `/reports/{id}/download` | `reports:read` |

```json
{
  "report_type": "technical",
  "format": "pdf",
  "audit_run_id": "uuid"
}
```

Para ejecutivo:

```json
{
  "report_type": "executive",
  "format": "docx",
  "server_id": "uuid-o-null",
  "period_start": "2026-09-01T00:00:00Z",
  "period_end": "2026-09-30T23:59:59Z"
}
```

Formatos: `pdf`, `docx`, `xlsx`. Los reportes con datos del conector simulado se nombran con prefijo
`simulado_` y muestran una advertencia visible.

## Dashboard

`GET /dashboard`

Filtros opcionales: `date_from`, `date_to`, `server_id`, `os_family`, `environment`, `profile_id`,
`severity`.

La respuesta incluye summary, tendencia semanal, controles con más fallos, ejecuciones recientes y
servidores con mayor riesgo. Todos los valores provienen de PostgreSQL.

## Bitácora

`GET /audit-logs` (`logs:read`)

Filtros: `action`, `module`, `result`, `user_id`, `date_from`, `date_to`, paginación. Los cambios se
redactan antes de persistir y no se pueden modificar ni borrar desde la API.

## Configuración y API keys

| Método | Ruta | Permiso |
| --- | --- | --- |
| GET | `/settings` | `settings:manage` |
| GET | `/settings/api-tokens` | `settings:manage` |
| POST | `/settings/api-tokens` | `settings:manage` |
| DELETE | `/settings/api-tokens/{id}` | `settings:manage` |

Scopes disponibles:

- `automation:execute`
- `automation:recommendations`
- `automation:reports`

El token completo se devuelve **una sola vez**. Solo se almacena su SHA-256.

## Automatización n8n

| Método | Ruta | Scope |
| --- | --- | --- |
| POST | `/automation/audits/run-due` | `automation:execute` |
| POST | `/automation/findings/refresh?days=30` | `automation:execute` |
| POST | `/automation/recommendations/refresh?limit=2` | `automation:recommendations` |
| POST | `/automation/reports/batch` | `automation:reports` |

```powershell
$headers = @{ "X-API-Key" = "cisa_xxx_yyy" }
Invoke-RestMethod -Method Post -Headers $headers `
  -Uri http://127.0.0.1:8000/api/v1/automation/audits/run-due
```

`run-due` bloquea las programaciones vencidas en PostgreSQL para evitar duplicados si n8n reintenta.
No acepta SQL, expresiones ni comandos libres.

## Salud

- `GET /health` (sin prefijo) — liveness.
- `GET /api/v1/health` — comprueba PostgreSQL.

## Códigos relevantes

| Código | Significado |
| --- | --- |
| `401` | Token inválido, expirado o cuenta bloqueada |
| `403` | Sin permiso RBAC o scope |
| `409` | Conflicto: run activa, transición inválida, servidor sin autorizar |
| `422` | Validación de entrada o regla de negocio |
| `429` | Rate limit de autenticación |
| `503` | IA no disponible o base de datos temporalmente caída |
