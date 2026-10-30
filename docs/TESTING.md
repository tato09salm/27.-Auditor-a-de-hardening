# Pruebas y validación

## 1. Entorno

| Elemento | Valor |
| --- | --- |
| Windows | 11 |
| Python | 3.11.9 |
| PostgreSQL | 17.7 |
| Node.js | 22.12.0 |
| n8n | 2.8.4 |
| Base de pruebas | `27auditoria_test`, recreada por la suite |
| Navegador UI | Chrome headless 1440×1000 y 390×844 |

La suite crea y migra una base separada. No usa la base de desarrollo para las pruebas.

## 2. Ejecutar

```powershell
$env:PYTHONPATH='backend'
python -m pytest backend/tests -q --disable-warnings
```

Variables opcionales:

```powershell
$env:TEST_DATABASE_URL='postgresql+psycopg://usuario:clave@localhost:5432/27auditoria_test'
```

Si no se define, `conftest.py` toma `DB_*` del `.env` local y crea `27auditoria_test`.

### Frontend

```powershell
cd frontend
npm run typecheck
npm run build
```

El build requiere que esbuild pueda lanzar su proceso. En entornos con sandbox, use el mecanismo de
permisos correspondiente.

## 3. Resultado actual

```text
.................                                                        [100%]
18 passed in 13.29s
```

| Verificación | Resultado |
| --- | --- |
| Pruebas backend | **18 passed** |
| TypeScript (`tsc -b`) | Sin errores |
| Build Vite | Correcto; bundle generado |
| Import n8n de 4 flujos | Correcto con n8n 2.8.4 |
| Configuración Docker Compose | `docker compose config` válido |
| UI desktop | Login, dashboard, servidores, detalle, auditorías, evidencia, hallazgos, recomendación, perfiles, programación, reportes, usuarios, bitácora y configuración renderizados |
| UI móvil | Dashboard a 390 px; navegación por drawer y filtros apilados |
| Reportes | PDF, DOCX y XLSX generados y descargados con firmas `%PDF`/`PK` |
| Ollama real | **No validado**: no había un modelo instalado. Se probó la ruta de indisponibilidad |
| SSH real | **No validado contra un host**: sí se probó el bloqueo SSRF y el fallo cerrado |

## 4. Matriz de pruebas backend

### `test_core.py`

| Prueba | Qué verifica |
| --- | --- |
| Scoring con no aplicables/no evaluados | Fórmula 2/3 = 66.67, cobertura 60% |
| Scoring sin aplicables | Devuelve `null`, no 100 |
| Política de contraseñas | Rechaza débiles y las que contienen el correo |
| Comandos IA destructivos | `rm -rf /`, `curl \| sh`, `mkfs` se marcan `dangerous` |
| Cambio de `sshd_config` | Se marca advertencia de posible bloqueo SSH |

### `test_api.py`

| Prueba | Qué verifica |
| --- | --- |
| Setup, login y RBAC | 401 sin token; observador no puede crear servidor ni ver bitácora |
| Autorización explícita | Servidor sin autorizar no audita ni testea; tras autorizar, sí |
| Auditoría simulada | Score 35.71, 5 aprobados, 9 fallos, 9 hallazgos |
| Historial de hallazgos | Segunda run no duplica; incrementa ocurrencias |
| Servidor conforme | Score 100; dashboard calcula promedio 67.86 |
| Bloqueo loopback | Test de conexión y run fallan cerrado; 14 no evaluados; score `null` |
| Ciclo de hallazgo | Transición inválida devuelve 409; transición válida registra evento |
| Bitácora append-only | UPDATE directo a `audit_logs` es rechazado por PostgreSQL |
| IA no disponible | Recomendación devuelve 503 y no rompe la auditoría |
| Detalle de recomendación | Incluye finding/servidor y revisiones |
| Revisión humana | Aprobar deja estado y review; no ejecuta comandos |
| Comando destructivo | Aprobación bloqueada con 422 `dangerous_commands` |
| Cambio de contraseña | Invalida el access token anterior y revoca sesiones |
| Contraseña temporal | Bloquea la API salvo cambio/me/logout y permite cambiarla |

### `test_reports_automation.py`

| Prueba | Qué verifica |
| --- | --- |
| Reportes PDF/Word/Excel | 201, descarga 200 y firma de archivo |
| Reporte ejecutivo | Generación y descarga |
| Nombre de reporte simulado | Prefijo `simulado_` |
| Automatización n8n | API key con scope, schedule vencida, run creada, no duplicada al repetir |
| Trigger de schedule | `trigger_type=schedule` y `next_run_at` actualizado |

## 5. Pruebas manuales de interfaz

Se recorrió la aplicación con Chrome headless y una cuenta de demostración temporal:

1. Login y persistencia de sesión.
2. Dashboard con datos reales.
3. Servidores y filtros.
4. Detalle de servidor, autorización y credencial.
5. Auditorías y detalle de evidencia expandible.
6. Hallazgos y ciclo de vida.
7. Recomendación con comandos, advertencias y revisión.
8. Perfiles, programación, reportes, usuarios, bitácora y configuración.
9. Dashboard móvil a 390 px.

Se detectaron y corrigieron:

- avatar sin contraste por una clase Tailwind inexistente;
- error 500 en el detalle de recomendación por un argumento duplicado;
- formularios de edición de usuarios que conservaban estado anterior;
- selección de controles de perfil que se reiniciaba al desmarcar todos.

Los datos de demostración se eliminaron de la base de desarrollo al finalizar. El producto entrega
la pantalla de primer arranque, sin usuarios ni credenciales.

## 6. Pruebas no ejecutadas

No se debe afirmar que estas pruebas se superaron:

- Conexión SSH real contra un servidor Ubuntu.
- Interpretación de salidas reales de `sshd -T`, `systemd`, `ufw`, `apt` y PAM en un host vivo.
- Generación real de LangChain/Ollama, por ausencia de modelo en el entorno.
- Carga concurrente con múltiples réplicas.
- Prueba de penetración formal o revisión ASVS completa.
- Accesibilidad WCAG automatizada.
- Restauración de backup desde un volumen de producción.
- Build de imágenes Docker (solo se validó la configuración y los Dockerfiles).

## 7. Datos de prueba

- Las pruebas usan `ENABLE_SIMULATED_CONNECTOR=true` y una base exclusiva.
- Los servidores simulados se identifican con `is_simulated`.
- La IA se desactiva (`AI_ENABLED=false`) en la suite; las pruebas de recomendación insertan
  estructuras directamente para validar presentación/revisión sin simular una llamada al modelo.
- Los reportes de prueba llevan el prefijo `simulado_`.
