# Automatización con n8n

## 1. Principio

n8n es el **orquestador**, no el motor de seguridad. Selecciona programaciones vencidas y llama a
endpoints autenticados. El backend:

- valida autorización y scopes;
- evita ejecuciones duplicadas con un índice único;
- ejecuta los checks de solo lectura;
- calcula score, guarda evidencia y actualiza hallazgos;
- registra todo en la bitácora.

n8n no recibe credenciales SSH ni acceso SQL.

## 2. Flujos incluidos

| Archivo | Disparador | Endpoint principal | Scope |
| --- | --- | --- | --- |
| `A_auditoria_programada.json` | Cada 15 minutos | `POST /automation/audits/run-due` | `automation:execute` |
| `B_recomendaciones_ia.json` | Diario 04:00 | `POST /automation/recommendations/refresh?limit=2` | `automation:recommendations` |
| `C_seguimiento_hallazgos.json` | Diario 05:00 | `POST /automation/findings/refresh?days=30` | `automation:execute` |
| `D_generacion_reportes.json` | Mensual día 1, 06:00 | `POST /automation/reports/batch` | `automation:reports` |

Los flujos se importaron correctamente con **n8n 2.8.4**. Cada archivo tiene un nodo Sticky con
instrucciones y un nodo `Configuración` con `apiBaseUrl`.

## 3. Preparación

### 3.1 Crear API key

En la consola:

1. **Configuración → Tokens de automatización → Crear token**.
2. Nombre: `n8n producción`.
3. Scopes:
   - flujo A/C: `automation:execute`;
   - flujo B: `automation:recommendations`;
   - flujo D: `automation:reports`.
4. Expiración acorde a la política.
5. Copie el token. No se vuelve a mostrar.

Si un flujo necesita varios alcances, cree un token con todos los necesarios o tokens separados.

### 3.2 Crear credencial HTTP Header Auth

En n8n:

- **Credentials → New → Header Auth**.
- Nombre: `CIS Hardening API Key`.
- Header Name: `X-API-Key`.
- Header Value: `cisa_...`.

Los workflows referencian esa credencial por nombre. Si n8n la importa sin ID, selecciónela en cada
nodo HTTP.

### 3.3 URL del backend

- n8n en el host: `http://127.0.0.1:8000/api/v1`.
- n8n en Docker Compose: `http://backend:8000/api/v1` (misma red) o
  `http://host.docker.internal:8000/api/v1`.
- Producción: `https://hardening.empresa.com/api/v1`.

Edite el nodo `Configuración` de cada workflow.

## 4. Importación

### Docker

```powershell
docker compose --profile automation up -d n8n
```

En la interfaz de n8n:

1. **Workflows → Import from File**.
2. Seleccione cada JSON de `n8n/workflows`.
3. Asocie la credencial.
4. Guarde y active.

También puede copiarlos dentro del contenedor:

```powershell
docker compose cp n8n/workflows/. n8n:/tmp/workflows/
docker compose exec n8n n8n import:workflow --input=/tmp/workflows/A_auditoria_programada.json
```

### CLI local

```powershell
n8n import:workflow --input="n8n/workflows/A_auditoria_programada.json"
n8n import:workflow --input="n8n/workflows/B_recomendaciones_ia.json"
n8n import:workflow --input="n8n/workflows/C_seguimiento_hallazgos.json"
n8n import:workflow --input="n8n/workflows/D_generacion_reportes.json"
```

## 5. Detalle de los flujos

### Flujo A — Auditoría programada

1. Schedule Trigger cada 15 minutos.
2. Set `apiBaseUrl`.
3. HTTP POST `/automation/audits/run-due`.
4. IF `runs_started > 0`.
5. Si hay ejecuciones, GET `/dashboard`.
6. Code con resumen (programaciones vencidas, runs, score, hallazgos).
7. Si no hay ejecuciones, NoOp.

El backend bloquea las filas de programaciones con `FOR UPDATE SKIP LOCKED` y adelanta
`next_run_at`. Si n8n reintenta, no crea una segunda run para la misma programación vencida. Además,
el índice único de run activa por servidor protege ante ejecuciones manuales concurrentes.

### Flujo B — Recomendaciones IA

1. Schedule diario.
2. HTTP POST `/automation/recommendations/refresh?limit=2`.
3. Code con resumen y estado `pendiente_de_revision_humana`.

No se aprueba ni ejecuta nada. Si Ollama no está disponible, el endpoint devuelve un resumen con
errores controlados y no crea propuestas inválidas. El tiempo de espera del nodo es alto porque un
modelo local puede tardar.

### Flujo C — Hallazgos persistentes

1. Schedule diario.
2. HTTP POST `/automation/findings/refresh?days=30`.
3. IF `total > 0`.
4. Set `Preparar alerta` con total, críticos/altos y detalle.
5. Conecte ese nodo a Slack, Teams, correo u otro canal.

El flujo no cambia estados. Un hallazgo persistente sigue siendo responsabilidad del analista.

### Flujo D — Reportes

1. Schedule mensual.
2. HTTP POST `/automation/reports/batch` con `{"format":"pdf"}`.
3. GET `/reports?page=1&page_size=20`.
4. Code con resumen y enlaces de descarga.

El backend limita el lote a 20 servidores. Para Word/Excel, cambie `format` en el cuerpo JSON.

## 6. Seguridad

- Use una API key por integración, no una cuenta de administrador.
- Rote tokens y revoque los antiguos.
- Mantenga n8n detrás de autenticación y HTTPS.
- No active `N8N_BLOCK_ENV_ACCESS_IN_NODE=false` para evitar exponer variables del contenedor.
- No pase credenciales SSH a n8n.
- No agregue nodos que consulten PostgreSQL directamente; use la API.
- Revise ejecuciones fallidas y alertas.
- Restrinja el acceso a la UI de n8n.
- Guarde `N8N_ENCRYPTION_KEY` en el gestor de secretos.

## 7. Manejo de errores y reintentos

- Los nodos HTTP de A y C tienen reintentos con espera.
- B no reintenta automáticamente para no duplicar generaciones costosas.
- D no reintenta para no generar reportes duplicados.
- Configure un **Error Workflow** de n8n para notificar fallos.
- El backend registra `automation.*` en la bitácora.
- Una ejecución fallida no cambia el estado de un hallazgo.

## 8. Prueba controlada

Antes de activar:

1. Cree un servidor simulado con autorización (solo entorno de pruebas).
2. Cree una programación con `next_run_at` vencido.
3. Ejecute manualmente el flujo A.
4. Verifique en la consola:
   - run creada;
   - checks y score;
   - hallazgos;
   - bitácora.
5. Ejecute de nuevo el flujo sin esperar: `runs_started` debe ser 0.
6. Ejecute B con Ollama activo y revise que la propuesta quede pendiente de revisión.
7. Ejecute D y descargue un reporte.

## 9. Problemas frecuentes

| Síntoma | Causa |
| --- | --- |
| 401 | Header mal configurado, token revocado o expirado |
| 403 | Scope insuficiente |
| 409 | Run activa o servidor no autorizado |
| `ECONNREFUSED` | `apiBaseUrl` incorrecto dentro de Docker |
| No se ejecuta nada | No hay programaciones vencidas o están pausadas |
| Se repite la ejecución | Revise `next_run_at` y el estado de la programación |
| B devuelve errores | Ollama no disponible o modelo no instalado |
| D falla | Periodo inválido o servidor sin datos |

## 10. Referencias

- [API](API.md)
- [Operación](OPERATIONS.md)
- [Seguridad](SECURITY.md)
- Documentación oficial de n8n: <https://docs.n8n.io/>
