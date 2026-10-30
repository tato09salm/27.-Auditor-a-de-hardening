# Manual de usuario

## 1. Roles

| Rol | Uso principal |
| --- | --- |
| Administrador | Organización, usuarios, servidores, perfiles, automatización y configuración |
| Auditor | Perfiles, ejecución de auditorías, revisión de recomendaciones e informes |
| Analista | Hallazgos, análisis de incumplimientos y solicitud de propuestas IA |
| Observador | Consulta de dashboards, resultados e informes autorizados |

Los permisos se validan en el backend. Si una opción no aparece, el rol no la tiene o el recurso es de
otra organización.

## 2. Primer acceso

1. Abra la URL entregada por el responsable del despliegue.
2. Si es la primera instalación, complete **Crear la cuenta administradora**:
   - nombre de la organización;
   - identificador (solo minúsculas, números y guiones);
   - nombre, correo y contraseña robusta.
3. No existen credenciales de ejemplo. La contraseña debe tener 12+ caracteres y 3 tipos de
   caracteres.
4. Al ingresar, el perfil **Línea base CIS Ubuntu 22.04** queda disponible con 14 controles.
5. Si un administrador le creó una cuenta temporal, la aplicación exige cambiarla antes de continuar.

## 3. Dashboard

El dashboard muestra datos reales de PostgreSQL:

- servidores registrados, auditados y pendientes;
- cumplimiento promedio por última evaluación de cada servidor;
- cobertura de evaluación;
- hallazgos activos por severidad;
- auditorías del periodo;
- recomendaciones pendientes de revisión;
- tendencia semanal, controles con más fallos, servidores con mayor riesgo y actividad reciente.

Filtros: periodo, servidor, perfil, entorno y severidad. El botón **Limpiar** restablece los filtros.

> Un score alto no significa que el servidor sea seguro. Lea la cobertura y las limitaciones.

## 4. Registrar un servidor

**Servidores → Registrar servidor** (Administrador).

Complete:

1. **Identificación**: nombre, hostname, IP, versión de Ubuntu, entorno, área y perfil.
2. **Conexión**:
   - SSH de solo lectura o conector simulado (solo pruebas);
   - puerto, usuario técnico, método de autenticación;
   - huella de host SSH;
   - contraseña o clave privada.
3. **Autorización**:
   - confirme que tiene autorización del propietario;
   - marque objetivo privado solo si corresponde;
   - guarde.

### Obtener la huella SSH

En el servidor:

```bash
ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub -E sha256
```

Copie el valor completo `SHA256:...`. La plataforma rechaza un host con huella distinta.

### Credenciales

- La credencial se cifra antes de guardarse.
- No se muestra después de guardar.
- Use una cuenta técnica dedicada, idealmente con clave sin passphrase y permisos mínimos.
- El motor no usa `sudo`.

### Autorización y cambios

Cambiar IP, hostname, puerto, usuario, autenticación o huella revoca la autorización. Un
administrador debe confirmarla de nuevo desde el detalle del servidor.

### Conector simulado

Muestra la etiqueta **SIMULADO** en servidores, auditorías, dashboard y reportes. No contacta
infraestructura real; se usa para capacitación y pruebas.

## 5. Ejecutar una auditoría

1. **Auditorías → Nueva auditoría** o **Auditar ahora** en el servidor.
2. Seleccione servidor autorizado y perfil.
3. Confirme. La ejecución queda en cola.
4. La página de detalle se actualiza automáticamente.

La plataforma no permite dos ejecuciones simultáneas sobre el mismo servidor.

## 6. Leer resultados

- **Score**: aprobados / (aprobados + incumplidos) × 100.
- **Cobertura**: controles aplicables evaluados / total del perfil.
- **Aprobados**: evidencia conforme.
- **Incumplidos**: criterio no cumplido.
- **No aplicables**: excluidos del denominador.
- **No evaluados**: error de conexión, permiso o parser; no cuentan como aprobados.

Haga clic en una fila de control para ver:

- resultado observado;
- salida técnica;
- comando de solo lectura ejecutado;
- evidencia estructurada;
- guía de corrección de referencia;
- notas de mapeo CIS/interno.

Si la ejecución falla por conexión, el score queda vacío y los controles se marcan `not_evaluated`.

## 7. Gestionar hallazgos

**Hallazgos** muestra incumplimientos activos. Cada uno tiene severidad, estado, responsable,
vencimiento, ocurrencias y evidencia.

### Ciclo de vida

```text
Detectado → En revisión → Corrección planificada → Corregido pendiente de validación → Resuelto
```

Ramas:

- **Riesgo aceptado temporalmente**: requiere fecha futura y justificación. Debe revisarse al vencer.
- **Falso positivo documentado**: requiere explicación.
- **Reapertura**: un hallazgo resuelto puede volver a detectado.

### Cierre

- El cierre normal ocurre cuando una nueva auditoría evalúa el control como aprobado.
- Un administrador puede cerrar sin comprobación solo con una justificación documentada de al menos
  20 caracteres.
- El cierre y todos los cambios quedan en el historial y la bitácora.

## 8. Recomendaciones IA

1. Abra un hallazgo activo.
2. Pulse **Generar recomendación IA** (Analista/Administrador).
3. Espere; si Ollama no está disponible verá un mensaje y la auditoría no se afecta.
4. La propuesta incluye problema, riesgo, recomendación, comandos sugeridos, explicación, impacto,
   requisitos, riesgo de interrupción, validación, rollback y referencias.
5. Los comandos aparecen con advertencias si el validador detecta riesgo.
6. Un Auditor/Administrador revisa y **aprueba o rechaza** con un comentario.

Reglas:

- Ningún comando se ejecuta desde la plataforma.
- Aprobar no aplica cambios.
- Una propuesta con comandos destructivos no puede aprobarse.
- Si el modelo indica información insuficiente, no se muestran comandos inventados.
- La confianza del modelo no es una garantía; la revisión humana es obligatoria.

## 9. Reportes

**Reportes → Generar reporte** (Auditor/Administrador/Analista).

- **Técnico**: requiere una auditoría completada; incluye resultados, evidencias, hallazgos y
  recomendaciones aprobadas.
- **Ejecutivo**: consolida un periodo, compara con el periodo anterior, muestra riesgos y acciones.

Formatos: PDF, Word y Excel. El archivo se descarga y queda en el histórico con checksum SHA-256.

Los reportes:

- no contienen contraseñas, claves ni tokens;
- muestran limitaciones;
- indican si incluyen datos simulados.

## 10. Programación

**Programación → Nueva programación** (Auditor/Administrador).

- Nombre.
- Servidor autorizado.
- Perfil.
- Frecuencia (cron de cinco campos) y zona horaria.
- Estado habilitado/pausado.

n8n consulta las programaciones vencidas. Si n8n está detenido, no se ejecutan, pero no se duplican al
reintentar. Pausar una programación no borra su historial.

## 11. Usuarios y seguridad

**Usuarios y roles** (Administrador):

- crear usuario con roles;
- exigir cambio de contraseña;
- editar nombre, roles y estado;
- restablecer contraseña y revocar sesiones.

**Cambiar contraseña** está en el menú de usuario. Al cambiarla se revocan todas las sesiones.

## 12. Bitácora

**Bitácora** (Administrador/Auditor) muestra accesos, cambios de servidores, ejecuciones, reportes,
revisiones y automatización.

- Los registros no se pueden editar ni borrar desde la consola.
- Los secretos aparecen redactados.
- Puede expandir los cambios de cada evento.

## 13. Buenas prácticas

- Use cuentas nominativas; no comparta credenciales.
- Revise la cobertura antes de interpretar un score.
- Priorice hallazgos críticos/altos y servidores de producción.
- No acepte riesgos sin fecha de revisión.
- Trate las propuestas IA como borradores técnicos.
- Pruebe los cambios en un entorno controlado y mantenga rollback.
- Revise la bitácora tras cambios de roles o credenciales.
- Cierre hallazgos con una nueva auditoría, no solo con una nota.
