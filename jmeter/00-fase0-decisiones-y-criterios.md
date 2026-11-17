# Fase 0 — Decisiones y criterios de la práctica JMeter

**Proyecto:** CIS Hardening Auditor
**Fecha de la decisión:** 17 / 11 / 2026
**Responsable:** Ricardo Velásquez

Este documento se cierra **antes** de la primera corrida. Los criterios no se
modifican después de ver los resultados; esa es la regla de la práctica.

---

## 1. Alcance

| Elemento | Decisión |
|---|---|
| Módulo crítico (objeto de N) | **Dashboard** — `GET /api/v1/dashboard` |
| Módulo secundario | **Hallazgos** — `GET /api/v1/findings?page=1&page_size=50` |
| Backend bajo prueba | FastAPI en `http://127.0.0.1:8000/api/v1` |
| Base de datos | PostgreSQL 17, base `27auditoria` |
| Fuera de alcance | Frontend React/Nginx (solo reenvía), Streamlit (WebSockets), auditorías SSH reales, n8n, Ollama |

**Justificación del módulo crítico:** el Dashboard es la pantalla de entrada y
la consulta más pesada de lectura. El endpoint carga en memoria todas las
auditorías completadas del periodo (30 días por defecto), agrega en Python y
además hace conteos por servidor dentro de un bucle. Ningún otro endpoint de
lectura combina ese volumen con esa cantidad de consultas.

---

## 2. Definiciones que se usarán en el informe

- **Usuario simultáneo:** un hilo de JMeter que ejecuta el flujo completo del
  módulo (Dashboard + Hallazgos) con un tiempo de espera de 1–3 s entre
  peticiones.
- **Error:** cualquier respuesta con código distinto de 200, o un 200 que no
  cumpla la aserción de contenido. Los 401, 403, 429 y 5xx cuentan como error.
- **N:** el mayor número de hilos con **0 % de error** que además cumple los
  umbrales de latencia y throughput definidos abajo.
- **p95:** percentil 95 del tiempo de respuesta del muestreo completo del
  escalón, leído del Aggregate Report o del reporte HTML.

---

## 3. Criterios de aceptación y de colapso

Un escalón **se acepta** solo si cumple los tres criterios a la vez:

| # | Criterio | Umbral |
|---|---|---|
| C1 | Porcentaje de error | **= 0 %** |
| C2 | p95 | **≤ 3 000 ms** |
| C3 | Throughput | **mayor** que el del escalón anterior |

Un escalón **colapsa** si falla cualquiera de los tres:

| # | Señal de colapso | Interpretación |
|---|---|---|
| F1 | Error > 0 % (aunque sea 0,1 %) | el sistema ya no atiende a todos |
| F2 | p95 > 3 000 ms | la latencia deja de ser usable |
| F3 | Throughput igual o menor que el escalón anterior | se saturó el recurso |

**Regla de N:** `N = último escalón aceptado`. El escalón inmediatamente
superior debe haber colapsado; si no colapsó, la búsqueda no terminó.

**Regla de confirmación:** el escalón que define N se repite 2 veces más. Si
alguna repetición falla, N baja al escalón anterior aceptado.

> Nota: el criterio del docente es **0 % de error**. Por eso no se usa el
> margen de 1–5 % del plan general; cualquier error descarta el escalón.

---

## 4. Plan de escalones (a refinar con los resultados)

| Escalón | Hilos | Ramp-up | Duración | Rol en la búsqueda |
|---|---|---|---|---|
| E1 | 10 | 10 s | 120 s | línea base |
| E2 | 25 | 25 s | 120 s | crecimiento |
| E3 | 50 | 50 s | 120 s | primer riesgo (pool de 30 conexiones) |
| E4 | 75 | 60 s | 120 s | zona probable de colapso |
| E5 | 100 | 60 s | 120 s | confirmación |
| E6 | 150 | 60 s | 120 s | techo |
| E7 | 200 | 60 s | 120 s | techo superior |

Reglas de ejecución:

1. Ascendente y con parada en el primer escalón que colapse.
2. Afinar entre el último aceptado y el primero que colapsó (pasos de 10–25
   hilos). Esos escalones intermedios son los que el docente quiere ver.
3. Un escalón = un `.jtl` + un reporte HTML + capturas del Aggregate Report.
4. Entre corridas, ~1 min de pausa. Si aparece 429, esperar 5 min.

**Ejemplo del entregable esperado:**

```
... 60 hilos  -> 0,00 % error  p95 1 820 ms  throughput 12,4/s   ACEPTADO
    70 hilos  -> 0,00 % error  p95 2 640 ms  throughput 13,1/s   ACEPTADO
    75 hilos  -> 1,10 % error  p95 4 310 ms  throughput 13,0/s   COLAPSO
N = 70 usuarios simultáneos
```

---

## 5. Condiciones del entorno (obligatorias)

| Condición | Valor / acción |
|---|---|
| Datos de prueba | BD con volumen representativo (decenas de miles de filas en `hardening_checks`). **Nunca datos reales.** |
| Autenticación | Un solo login en `setUp Thread Group`; token reutilizado por todos los hilos |
| Vigencia del token | 15 min → ningún escalón supera los 10 min |
| Host permitido | `ALLOWED_HOSTS` incluye `localhost` y `127.0.0.1`; JMeter corre en la misma máquina |
| Driver JDBC | `postgresql-42.x.jar` en `lib/` de JMeter, reiniciado después de copiarlo |
| Pool JDBC de JMeter | `Max Number of Connections` ≥ 30 |
| Listeners pesados | `View Results Tree` solo en la corrida de humo, luego desactivado |
| Tema visual | **JMeter y navegador en tema claro antes de la primera captura** |
| Registro de recursos | CPU y RAM medidos durante cada escalón (`docker stats` o Administrador de tareas) |

---

## 6. Evidencias comprometidas (fondo claro)

- [ ] Test Plan completo
- [ ] `JDBC Connection Configuration`
- [ ] `JDBC Request` con la consulta visible
- [ ] `setUp Thread Group` del login y el JSON Extractor
- [ ] Thread Group del módulo, con el número de hilos visible
- [ ] Aggregate Report del escalón base
- [ ] Aggregate Report de cada escalón intermedio
- [ ] Aggregate Report del **último escalón con 0 %**
- [ ] Aggregate Report del **primer escalón con error**
- [ ] Gráficas del reporte HTML (`-e -o`)
- [ ] CPU y RAM durante los escalones altos
- [ ] Tabla resumen escalón por escalón con N resaltado
- [ ] Prueba JDBC con su propio Aggregate Report

Convención de nombres: `resultados/r<NN>.jtl`, `reportes/r<NN>/`,
`capturas/<tema>-<NN>hilos.png` (por ejemplo `capturas/aggregate-70hilos.png`).

---

## 7. Lista de verificación para arrancar

**Estado al 17/11/2026:** entorno operativo y **base de datos ya sembrada**
(Fase 1 completada). El bloqueo por volumen de datos esta resuelto.

No se inicia la Fase 4 (escalones) hasta que el bloqueador esté resuelto. Un N
medido sobre una base vacía no es válido para la semana 14: el Dashboard
respondería en milisegundos y el sistema parecería soportar cualquier carga.

| Verificación | Estado | Nota |
|---|---|---|
| `docker compose up -d` y `/api/v1/health` responde 200 | ✅ | confirmado por el equipo |
| El Dashboard responde y el frontend funciona | ✅ | confirmado por el equipo |
| Carpeta `jmeter/resultados/`, `jmeter/reportes/`, `jmeter/capturas/` | ✅ | creadas |
| Criterios de la sección 3 definidos | ✅ | este documento |
| **La BD tiene volumen de datos y el Dashboard devuelve contenido no vacío** | ✅ | 840 auditorias, 60 servidores |
| **El Dashboard tarda un tiempo medible** (no es instantáneo) | ✅ | 206–405 ms por peticion |
| El login devuelve `access_token` y el Dashboard responde 200 con él | ✅ | `admin@demo.com` |
| Driver JDBC cargado y `JDBC Request` devuelve filas | ✅ | 0 % error, 200 OK |
| JMeter en tema claro | ✅ | `jmeter.laf` en `user.properties` |
| Equipo de medición de CPU/RAM listo | ⬜ | `docker stats` |

**Criterio de desbloqueo cumplido:** 11 760 filas en `hardening_checks` y
206–405 ms por peticion al Dashboard (medido el 17/11/2026).

---

## 8. Frase de sustentación (completada con los resultados)

> «El módulo **Dashboard** soporta como máximo **80** usuarios simultáneos con
> **0 %** de error, sobre un entorno con PostgreSQL **18**, 1 worker de Uvicorn y
> un pool de 30 conexiones. A partir de **85** usuarios el sistema presenta un
> **76,92 %** de error por timeout y a los **150** el backend deja de aceptar
> conexiones, lo que marca el colapso. La latencia usable (p95 ≤ 3 s) solo se
> sostiene hasta **10** usuarios, porque el throughput se estanca en 3,3
> peticiones/s del Dashboard: el cuello de botella es la aplicación, no la base.»

Resultados completos en `03-fase3-prueba-dashboard.md`.

### Comparación con el plan (sección 4)

El plan suponía colapso cerca de 75–100 hilos. El ensayo real encontró el primer
error a los 85 hilos y el servicio caído a los 150. La diferencia con lo previsto
obliga a **reemplazar el escalón 4** por la serie afinada 40/60/70/75/80/85/90.
