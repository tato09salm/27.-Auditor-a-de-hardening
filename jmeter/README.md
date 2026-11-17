# Práctica JMeter — CIS Hardening Auditor

Material de la práctica de pruebas de carga (semana 14). No se modificó el
código de la aplicación: todo lo nuevo vive en esta carpeta.

## Resultado

| Prueba | Objeto | N con 0 % de error |
|---|---|---|
| 1 — JDBC | consulta JOIN + GROUP BY sobre PostgreSQL | **100 conexiones** |
| 2 — HTTP | `GET /api/v1/dashboard` (módulo crítico) | **80 usuarios simultáneos** |

## Contenido

| Ruta | Qué es |
|---|---|
| `00-fase0-decisiones-y-criterios.md` | criterios, alcance y frase de sustentación |
| `01-fase1-preparar-entorno.md` | siembra de datos, credenciales y entorno |
| `02-fase2-prueba-jdbc.md` | prueba de base de datos y tabla de escalones |
| `03-fase3-prueba-dashboard.md` | prueba HTTP del Dashboard, N y causas del colapso |
| `plans/01-jdbc-hardening.jmx` | plan JDBC (pool 30, consulta compleja) |
| `plans/02-http-dashboard.jmx` | plan HTTP (login único, token global, dashboard + hallazgos) |
| `scripts/run-jdbc.ps1` | ejecuta un escalón JDBC y genera JTL + reporte HTML |
| `scripts/run-http.ps1` | ejecuta un escalón HTTP y calcula la tabla |
| `scripts/abrir-jmeter.cmd` | abre la GUI con el password de la BD cargado |
| `sql/` | siembra, verificación, consultas y limpieza de datos de prueba |
| `resultados/escalones.csv` | tabla final escalón por escalón (sí se versiona) |

## Reportes HTML versionados (cuentan la historia)

| Reporte | Serie | Qué muestra |
|---|---|---|
| `reportes/http_10h/` | HTTP | línea base: 0 % error, 530 ms |
| `reportes/http_50h/` | HTTP | 0 % error, latencia ya en 8,2 s |
| `reportes/http_80h/` | HTTP | **N = 80 usuarios con 0 % de error** |
| `reportes/http_85h/` | HTTP | primer error: 76,92 % (timeout) |
| `reportes/http_150h/` | HTTP | servicio caído (connection refused) |
| `reportes/jdbc2_100h/` | JDBC | **N = 100 conexiones con 0 % de error** |
| `reportes/jdbc2_150h/` | JDBC | primer error: 0,05 % |
| `reportes/jdbc2_1000h/` | JDBC | colapso: 14,61 % de error |

Los demás escalones quedan en disco (ignorados por Git) para no duplicar 2,85 MB
de jQuery/Bootstrap por reporte.

## Generar de nuevo los reportes

Los `.jtl` y los reportes HTML **no se versionan** (pesan decenas de MB y se
regeneran). Para volver a producirlos:

```powershell
# requiere PostgreSQL arriba, backend en 127.0.0.1:8000
.\jmeter\scripts\run-http.ps1 -Threads 80 -RampUp 10 -Duration 60 -Label http_80h
.\jmeter\scripts\run-jdbc.ps1 -Threads 100 -RampUp 10 -Duration 45 -Label jdbc2_100h
```

Cada corrida deja `resultados/<etiqueta>.jtl` y `reportes/<etiqueta>/index.html`.

> **Reiniciar el backend entre escalones HTTP.** Un timeout del cliente no
> cancela el trabajo del servidor; si no se reinicia, el escalón siguiente
> hereda la cola del anterior y los números salen inflados.
