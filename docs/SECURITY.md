# Seguridad

## 1. Modelo de amenazas

### Activos

- Credenciales SSH de servidores auditados.
- Evidencia de configuración y hallazgos.
- Historial de auditorías y reportes.
- Usuarios, roles y bitácora.
- Claves de firma JWT y de cifrado Fernet.

### Actores y riesgos

| Actor | Riesgo |
| --- | --- |
| Usuario autenticado con rol limitado | Acceso a otra organización o elevación de privilegios |
| Atacante con un token robado | Uso hasta expiración o refresh |
| Administrador comprometido | Cambio de configuración y exfiltración |
| Servidor auditado malicioso | Salida hostil, agotamiento de recursos, intento de prompt injection |
| Atacante de red | SSRF, acceso a metadata cloud, suplantación SSH |
| Modelo de IA | Alucinaciones, comandos destructivos, fuga de datos |
| n8n comprometido | Uso de API keys con alcance excesivo |
| Operador de base de datos | Alteración de bitácora o lectura de datos |

## 2. Controles implementados

### 2.1 Autenticación

- Contraseñas con **bcrypt** (coste 12), mínimo 12 caracteres y 3 clases.
- Bloqueo de cuenta tras 5 intentos fallidos por 15 minutos (configurable).
- Rate limiting por IP+cuenta y por IP (en memoria; ver limitaciones).
- Access token JWT de 15 minutos con `iss`, `aud`, `exp`, `iat` y tipo.
- Refresh token aleatorio de 48 bytes, almacenado solo como SHA-256.
- Cookie de refresco `HttpOnly`, `Secure` en producción, `SameSite=Lax`, path
  `/api/v1/auth`.
- Rotación de refresh; reutilización de un token rotado revoca todas las sesiones del usuario.
- Cambio de contraseña invalida tokens emitidos antes del cambio y revoca refresh tokens.
- Si `must_change_password` está activo, la API solo permite cambiar la contraseña o consultar el perfil hasta completar el cambio.
- Usuario inactivo, bloqueado u organización inactiva no pueden autenticarse.
- El primer administrador se crea con bloqueo transaccional; no existe credencial por defecto.

### 2.2 Autorización

- RBAC normalizado: `users`, `roles`, `permissions`, `user_roles`, `role_permissions`.
- Cada endpoint usa una dependencia `require_permission` o `require_api_scope`.
- Todo recurso se filtra por `organization_id` del usuario.
- El frontend oculta opciones, pero el backend vuelve a autorizar.
- Un usuario no puede desactivarse a sí mismo ni dejar la organización sin administrador.
- Las API keys de n8n tienen scopes y no heredan permisos de administrador.

Matriz resumida:

| Permiso | Admin | Auditor | Analista | Observador |
| --- | :---: | :---: | :---: | :---: |
| Dashboard | ✓ | ✓ | ✓ | ✓ |
| Ver servidores | ✓ | ✓ | ✓ | ✓ |
| Gestionar servidores | ✓ |  |  |  |
| Ver perfiles | ✓ | ✓ | ✓ | ✓ |
| Gestionar perfiles | ✓ | ✓ |  |  |
| Ejecutar auditorías | ✓ | ✓ |  |  |
| Ver auditorías/evidencia | ✓ | ✓ | ✓ | ✓ |
| Gestionar hallazgos | ✓ |  | ✓ |  |
| Generar IA | ✓ |  | ✓ |  |
| Revisar IA | ✓ | ✓ |  |  |
| Generar reportes | ✓ | ✓ | ✓ |  |
| Ver reportes | ✓ | ✓ | ✓ | ✓ |
| Gestionar programaciones | ✓ | ✓ |  |  |
| Gestionar usuarios | ✓ |  |  |  |
| Ver bitácora | ✓ | ✓ |  |  |
| Configuración y API keys | ✓ |  |  |  |

### 2.3 Secretos

- Credenciales SSH cifradas con **Fernet** usando `FERNET_KEY` externa a PostgreSQL.
- La API nunca devuelve `secret_ciphertext`, contraseñas ni claves privadas.
- Los logs de SQLAlchemy usan `hide_parameters=True`.
- La bitácora redacta claves sensibles (`password`, `secret`, `token`, `private_key`, etc.).
- Los reportes no incluyen credenciales; el ejemplo de evidencia solo contiene metadatos de archivos.
- `.env` está en `.gitignore`; `.env.example` no contiene secretos reales.
- n8n cifra sus credenciales con `N8N_ENCRYPTION_KEY`.

### 2.4 Aislamiento de red y SSH

- Se conecta a la **IP registrada**, no a un nombre resuelto en tiempo de conexión: evita DNS
  rebinding.
- Bloqueo permanente de loopback, link-local, multicast, no especificado, reservado y metadatos
  cloud (`169.254.169.254`, `169.254.170.2`, `100.100.100.200`, `192.0.0.192`).
- Redes privadas requieren tres condiciones:
  1. `AUDIT_ALLOW_PRIVATE_TARGETS=true`;
  2. `server.allow_private_target=true`;
  3. `server.authorization_confirmed=true`.
- `AUDIT_ALLOWED_CIDRS` permite una allowlist adicional.
- Huella de host **SHA256 obligatoria** y comparación en tiempo constante.
- Sin `AutoAddPolicy`, sin `look_for_keys`, sin agente SSH.
- Timeouts de conexión, autenticación, comandos y tamaño máximo de salida.
- Comandos estáticos del código, sin interpolar valores del usuario.
- El motor no ejecuta `sudo` ni comandos de escritura.
- No existe endpoint para ejecutar comandos libres.

### 2.5 IA

- LangChain + Ollama local; sin herramientas ni acceso a red desde el modelo.
- El prompt solo incluye control, sistema operativo, evidencia acotada, criterio y guías.
- El contenido de evidencia se trata como **datos no confiables** y se instruye al modelo a ignorar
  instrucciones embebidas.
- La salida se valida con Pydantic; una estructura inválida devuelve error y no se guarda.
- Escáner de comandos destructivos: `rm -rf /`, `mkfs`, `dd`, reinicios, vaciado de firewall, cierre
  de SSH, descarga y ejecución, cambios de cuentas, etc.
- Se marcan advertencias por cambios de `sshd_config` y firewall.
- Una propuesta `dangerous` **no puede aprobarse** por API.
- La aprobación no ejecuta nada; la plataforma no tiene endpoint de ejecución.
- Si Ollama está caído, las auditorías continúan.

### 2.6 Aplicación web

- CORS explícito; sin `*` en producción.
- `TrustedHostMiddleware`.
- Cabeceras de seguridad: `X-Content-Type-Options`, `X-Frame-Options: DENY`,
  `Referrer-Policy`, `Permissions-Policy`, CSP para API.
- HSTS en producción bajo HTTPS.
- Límite de cuerpo de 2 MB.
- Errores sin stack traces y con `request_id`.
- Validación Pydantic con `extra=forbid` en objetos sensibles.
- Los errores de validación no reflejan el valor de entrada.
- Consultas parametrizadas por SQLAlchemy; no hay SQL construido con input de usuario.
- Nginx sirve la SPA con CSP, `frame-ancestors 'none'` y proxy interno a la API.
- El token de acceso no se persiste en `localStorage`.

### 2.7 Bitácora

- `audit_logs` es append-only mediante trigger:
  - `BEFORE UPDATE OR DELETE` lanza excepción.
- No almacena secretos; `changes` se redacta y trunca.
- Registra usuario/API key, acción, módulo, recurso, resultado, IP, request ID y cambios.
- La aplicación no expone endpoints de modificación o borrado.
- Para auditoría legal, exporte periódicamente a almacenamiento WORM y restrinja el rol propietario
  de la base.

## 3. Límites conocidos

1. **No se validó SSH contra un host real** en este entorno. El bloqueo SSRF y el fallo cerrado sí se
   probaron; antes de producción haga una prueba controlada con un servidor de laboratorio.
2. **El rate limiting es en memoria.** Con varias réplicas, use Redis o el límite del proxy.
3. **El worker es en proceso.** Un reinicio puede dejar runs huérfanas; al arrancar se marcan como
   fallidas después de 2 horas. Para alta disponibilidad use una cola persistente.
4. **El trigger append-only no protege frente al superusuario de PostgreSQL.** Use roles
   restringidos y copias externas.
5. **El parser SSH es heurístico.** `Include`, PAM personalizado o contenedores sin `systemd` pueden
   producir `not_evaluated`; no se debe interpretar como incumplimiento.
6. **El modelo local puede alucinar.** La revisión humana es obligatoria y no se ejecutan comandos.
7. **La evaluación no cubre vulnerabilidades de aplicación**, parches de firmware, identidades cloud
   ni seguridad física.
8. **Credenciales sin passphrase.** El conector soporta claves Ed25519/ECDSA/RSA sin passphrase. Use
   una clave dedicada, de solo lectura y con restricciones en el servidor.

## 4. Endurecimiento de producción

- [ ] `ENVIRONMENT=production`, `DEBUG=false`, `COOKIE_SECURE=true`.
- [ ] HTTPS obligatorio; HSTS; certificados válidos.
- [ ] `CORS_ORIGINS` y `ALLOWED_HOSTS` exactos.
- [ ] `ENABLE_SIMULATED_CONNECTOR=false` (el arranque falla si está activo en producción).
- [ ] PostgreSQL no expuesto a Internet; usuario de aplicación con permisos mínimos.
- [ ] Backups cifrados de PostgreSQL y de `FERNET_KEY`/`SECRET_KEY`.
- [ ] `N8N_ENCRYPTION_KEY` respaldada; n8n detrás de autenticación.
- [ ] Ollama en red interna, sin exposición pública.
- [ ] Revisar `AUDIT_ALLOWED_CIDRS` y autorizaciones de servidores.
- [ ] Rotar API keys y contraseñas iniciales.
- [ ] Revisar la bitácora y las alertas de forma periódica.
- [ ] Probar restauración, no solo el backup.
- [ ] Revisar dependencias (`pip-audit`, `npm audit`) antes de cada release.

## 5. Respuesta a incidentes

1. Revocar API keys y sesiones de refresh.
2. Rotar `SECRET_KEY` (invalida sesiones) y, si hay sospecha de acceso a la base, rotar credenciales
   SSH de los servidores.
3. Aislar el backend y preservar `audit_logs`, reportes y logs del proxy.
4. Revisar `auth.login.failed`, `auth.refresh.reuse_detected`, `recommendations.*`,
   `servers.credential.update` y `automation.*`.
5. Restaurar desde un backup verificado y comparar checksums de reportes.
6. Documentar el incidente y las acciones.

## 6. Reporte de vulnerabilidades

No publique detalles explotables en un issue público. Entregue al responsable del despliegue:

- versión y commit;
- pasos de reproducción;
- impacto;
- evidencia sin secretos;
- propuesta de mitigación.

## 7. Referencias

- OWASP ASVS 4.0.
- CIS Ubuntu Linux 22.04 LTS Benchmark v1.0.0.
- NIST SP 800-53 (CM, AU, AC).
- Documentación de Paramiko, FastAPI, SQLAlchemy y n8n.
