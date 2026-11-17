# Fase 3 — Prueba con el modulo critico de la aplicacion (Dashboard)

**Fecha:** 17/11/2026
**Estado:** completada — **N = 80 usuarios simultaneos con 0 % de error**
**Plan:** `jmeter/plans/02-http-dashboard.jmx`
**Modulo evaluado:** `GET /api/v1/dashboard` (critico) + `GET /api/v1/findings` (secundario)

## 1. Objetivo

Esta es la prueba de la que sale **N: el maximo de usuarios simultaneos con
0 % de error** sobre el modulo mas critico de la aplicacion.

## 2. Estructura del plan

```
Test Plan: Practica JMeter - Modulo Dashboard (HTTP)
├─ HTTP Request Defaults ......... 127.0.0.1:8000
├─ HTTP Cookie Manager
├─ setUp Thread Group "Login unico"   (1 hilo, 1 iteracion)
│    └─ POST /api/v1/auth/login
│         ├─ Response Assertion 200
│         ├─ JSON Extractor  $.access_token -> ${token}
│         └─ JSR223 PostProcessor: publica el token como propiedad global
└─ Thread Group "Usuarios simultaneos - Dashboard"
     ├─ Header Manager  Authorization: Bearer ${__P(token)}
     ├─ GET /api/v1/dashboard   + assert 200 + assert "top_failures"
     ├─ GET /api/v1/findings?page=1&page_size=50  + assert 200
     ├─ Uniform Random Timer 1-3 s  (pausa de usuario real)
     ├─ Aggregate Report
     └─ Summary Report
```

Por que asi:

- **Login unico**: el login usa bcrypt y tiene rate limit (10 intentos por
  correo cada 5 min). Si cada hilo intentara loguearse, la prueba mediria el
  rate limiter, no el Dashboard. Un solo login en `setUp` y el token se
  comparte como propiedad global.
- **Pausa 1-3 s**: simula el tiempo que un usuario real mira la pantalla antes
  de pedir otra vista. Sin pausa, 100 hilos equivalen a miles de usuarios
  irreales.
- **Response Assertions**: el 0 % de error solo es valido si la respuesta es
  200 y trae el JSON del dashboard.

## 3. Como ejecutarla desde consola

```powershell
.\jmeter\scripts\run-http.ps1 -Threads 10  -RampUp 10 -Duration 60 -Label http_10h
.\jmeter\scripts\run-http.ps1 -Threads 50  -RampUp 10 -Duration 60 -Label http_50h
.\jmeter\scripts\run-http.ps1 -Threads 100 -RampUp 10 -Duration 60 -Label http_100h
```

El script:

1. verifica que el backend responda en `127.0.0.1:8000/api/v1/health`;
2. ejecuta el plan con el numero de usuarios indicado;
3. deja `jmeter/resultados/<etiqueta>.jtl` y `jmeter/reportes/<etiqueta>/index.html`;
4. imprime la tabla del escalon y el detalle por peticion (excluye el login).

## 4. Como ejecutarla desde la interfaz grafica (para las capturas)

1. Doble clic en `jmeter\scripts\abrir-jmeter.cmd`.
2. `File > Open` → `jmeter\plans\02-http-dashboard.jmx`.
3. En `Usuarios simultaneos - Dashboard` borrar `${__P(threads,10)}` y escribir
   el numero de usuarios (10, 25, 50, ...). Ramp-up 10, Duration 60.
4. Boton verde (`Ctrl+R`).
5. Clic en **Aggregate Report** y capturar la tabla.
6. Repetir cambiando solo el numero de usuarios.

## 5. Resultados

Condiciones de todos los escalones: ramp-up 10 s, duracion 60 s, pausa 1-3 s
entre iteraciones, backend reiniciado antes de cada escalon (ver nota 5.2).

| Usuarios | Error % | Dashboard prom. | Dashboard p95 | Findings prom. |
|---|---|---|---|---|
| 10 | **0,00 %** | 530 ms | 1 051 ms | 66 ms |
| 25 | **0,00 %** | 3 162 ms | 5 154 ms | 268 ms |
| 40 | **0,00 %** | 7 260 ms | 9 636 ms | 1 864 ms |
| 50 | **0,00 %** | 8 243 ms | 14 880 ms | 1 994 ms |
| 60 | **0,00 %** | 10 271 ms | 13 879 ms | 5 559 ms |
| 70 | **0,00 %** | 11 417 ms | 16 189 ms | 7 495 ms |
| 75 | **0,00 %** | 12 212 ms | 17 863 ms | 8 542 ms |
| **80** | **0,00 %** | 12 490 ms | 19 475 ms | 9 239 ms |
| 85 | 76,92 % | 22 338 ms | 30 016 ms | 28 509 ms |
| 90 | 69,80 % | 21 384 ms | 30 018 ms | 29 116 ms |
| 100 | 82,30 % | 23 864 ms | 30 017 ms | 28 776 ms |
| 125 | 83,89 % | 24 514 ms | 30 019 ms | 29 817 ms |
| 150 | 98,46 % | servicio caido | 30 007 ms | servicio caido |

### 5.1 Resultado: N = 80 usuarios simultaneos

**El maximo de usuarios simultaneos con 0 % de error es 80.**

- De 10 a 80 usuarios: **0 errores** en 2 781 peticiones contra
  `GET /api/v1/dashboard` y `GET /api/v1/findings`.
- A los **85** usuarios aparece el primer error (76,92 %): `SocketTimeoutException
  - Read timed out`.
- A los **150** el backend deja de aceptar conexiones: 1 961 muestras con
  `HttpHostConnectException` (servicio caido), 115 timeouts y solo 33 respuestas
  200. El proceso no se recupera.

**Las dos lecturas de N** (conviene decir las dos en la sustentacion):

| Criterio | N | Escalon que colapsa |
|---|---|---|
| **0 % de error** (criterio del docente) | **80** | 85 (76,92 %) |
| **p95 ≤ 3 s y throughput creciente** (criterio del plan, seccion 3) | **10** | 25 (p95 5,15 s) |

El criterio de error solo mide si el sistema responde; el de latencia mide si la
respuesta sirve. Con 80 usuarios el Dashboard responde en 12,5 s de promedio:
no falla, pero es inutilizable. Eso es exactamente lo que hay que explicar.

### 5.2 Por que los escalones se corren con el backend reiniciado

Un timeout del cliente **no cancela** el trabajo en el servidor. Si se corren dos
escalones seguidos, el segundo arranca con la cola del anterior todavia en
proceso y sus numeros salen inflados. En las primeras corridas eso produjo
errores falsos a los 60 y 70 usuarios (7 % y 26 %) que desaparecieron al
reiniciar el backend antes de cada escalon. Todos los datos de la tabla son de
corridas limpias.

### 5.3 Donde esta el cuello de botella

El throughput se estanca en **6,6 peticiones/s en total (3,3 del Dashboard)**
desde los 25 usuarios, mientras la latencia crece en linea recta con los
usuarios:

```
10 usuarios -> 0,53 s
25 usuarios -> 3,16 s
50 usuarios -> 8,24 s
80 usuarios -> 12,49 s
85 usuarios -> 30 s (timeout)  <-- colapso
```

Causas, en orden de impacto:

1. **1 solo worker de Uvicorn**: el Dashboard recorre 840 auditorias y 11 760
   checks en Python; el GIL serializa el trabajo. La capacidad real ronda las
   3 peticiones/s del Dashboard.
2. **Pool de base de datos de 30 conexiones** (`DB_POOL_SIZE=10` +
   `DB_MAX_OVERFLOW=20`): cuando se agota, cada peticion espera hasta 30 s y el
   cliente de JMeter corta a los 30 s. Eso explica el salto de 80 a 85 usuarios.
3. **PostgreSQL, Uvicorn y JMeter en la misma maquina**: comparten CPU, asi que
   el generador de carga tambien compite con el sistema medido.

La comparacion con la prueba JDBC es la conclusion tecnica del informe: la base
aguanta 100 conexiones con 0 % de error, pero el modulo Dashboard solo 80
usuarios porque el costo esta en la capa de aplicacion, no en PostgreSQL.

### 5.4 Validacion de estabilidad

Se repitio el escalon de 50 usuarios con duration 120 s (`http_50h_120s`):
**0,00 % de error**, 6,7 s de promedio y p95 de 11,9 s. El resultado se mantiene,
o sea que el 0 % no depende de la ventana de 60 s.

### 5.5 Escalon invalido (se descarta)

Los 13 escalones iniciales corridos sin reiniciar el backend mostraron errores a
los 60, 70 y 75 usuarios que luego desaparecieron con el backend limpio. Esos
datos se reemplazaron y no se usan en el informe.

## 6. Evidencias a capturar (fondo claro)

- [ ] Arbol del Test Plan completo (setUp + Thread Group)
- [ ] `setUp Thread Group` con el `POST /auth/login` y el JSON Extractor
- [ ] Header Manager con `Authorization: Bearer ${__P(token)}`
- [ ] `GET /dashboard` con sus dos aserciones visibles
- [ ] Thread Group con el numero de hilos (80)
- [ ] Aggregate Report de 10, 25, 50, 60, 70 y 75 (ensayo y error)
- [ ] Aggregate Report de **80** (ultimo con 0 %)
- [ ] Aggregate Report de **85** (primer escalon con error)
- [ ] Aggregate Report de **150** (servicio caido)
- [ ] Reportes HTML: `jmeter\reportes\http_80h\index.html` y `http_85h`

## 7. Guion de sustentacion (lealo tal cual)

> "Segunda prueba: el modulo mas critico de la aplicacion, el Dashboard, sobre
> FastAPI con 1 worker de Uvicorn y un pool de 30 conexiones a PostgreSQL 18.
> El plan hace un solo login en setUp Thread Group, guarda el token en una
> propiedad global y todos los hilos lo reutilizan; cada usuario pide el
> Dashboard y Hallazgos con una pausa de 1 a 3 segundos, como una persona real.
>
> Empece con 10 usuarios: 0 % de error, 530 ms. Subí a 25, 40, 50, 60, 70 y 75:
> siempre 0 % de error, pero la latencia crecia en linea recta hasta 12 segundos.
> Con 80 usuarios segui en 0 % de error: ese es el N. Con 85 aparecio el primer
> error, 76,92 %, por timeout de lectura a los 30 segundos; y con 150 el backend
> dejo de aceptar conexiones.
>
> La conclusion es que el sistema no falla por la base de datos sino por la capa
> de aplicacion: el throughput se estanca en 3,3 peticiones por segundo del
> Dashboard aunque se le den mas usuarios, porque un solo worker de Python
> procesa el Dashboard en serie. Por eso con 80 usuarios responde, pero en 12
> segundos: soporta la concurrencia, no la velocidad."

## 8. Comparacion con la prueba de base de datos

| Prueba | Modulo | N con 0 % de error | Primer error | Causa |
|---|---|---|---|---|
| 1 (JDBC) | consulta JOIN + GROUP BY sobre PostgreSQL | 100 conexiones | 150 (0,05 %) | pool JDBC de 30, espera de 10 s |
| 2 (HTTP) | `GET /api/v1/dashboard` | **80 usuarios** | 85 (76,92 %) | 1 worker + pool de 30, espera de 30 s |

La base tolera mas concurrencia que la aplicacion: el cuello de botella esta en
Python (GIL, un worker) y en la espera por conexion del pool, no en PostgreSQL.
