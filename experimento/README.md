# Dataset de auditorías – CIS Hardening Auditor

Resultados **obtenidos ejecutando el motor real del proyecto** (`checks.py` con los 14 comandos de solo lectura, sus evaluadores y `scoring.py`), no escritos a mano.

## Diseño experimental
- **Flota:** 40 hosts Ubuntu 24.04 de prueba (4 áreas, 3 entornos), 4 arquetipos de endurecimiento (hardened 20 %, partial 30 %, default_install 30 %, neglected 20 %). Semilla: 20261104.
- **Rondas:** 6 auditorías consecutivas (cadencia semanal nominal). Entre rondas se corrigen incumplimientos (prob. por entorno: prod 30 %, staging 20 %, dev 10 %), hay regresiones (3 %) y parches/nuevas actualizaciones.
- **Ejecución:** cada comando de control se ejecuta con `bash` real dentro de un *mount namespace* con el `/etc` del host superpuesto (overlayfs). Los archivos leídos (`sshd_config`, `pwquality.conf`, `faillock.conf`, `pam.d/*`, `ufw`, `/etc/shadow` con su modo/propietario/grupo) son **archivos reales**; `stat` y `sysctl` son reales (ASLR montado por bind).
- **Emulado (`scripts/shim.py`):** solo `systemctl`, `sshd -T`, `apt-get -s upgrade`, y la presencia de `ufw/rsyslogd/auditctl`, porque el entorno no tiene systemd, sshd ni repositorios por host.
- **No se usó SSH real** (el conector `NamespaceConnector` implementa `run_command` localmente; la lógica SSH/huella/anti-SSRF no se ejerce). Debe declararse como limitación.
- **Fallas inyectadas:** 3 % de host-rondas inalcanzables y 0,5 % de timeouts por comando → `not_evaluated` (columna `injected_fault`).
- **Verdad esperada (`ground_truth`):** calculada por el generador a partir de la configuración sembrada y del criterio de cada control, independiente de los evaluadores. Se corrigió una vez tras la corrida piloto (FW-DEFAULT es N/A sin UFW).
- Los hosts son **sintéticos** (configuraciones sembradas); los resultados de auditoría y tiempos son medidos. Los nombres de áreas son etiquetas ficticias.

## Archivos
| Archivo | Filas | Contenido |
|---|---|---|
| servers.csv | 40 | host, área, entorno, arquetipo, OpenSSH instalado |
| controls.csv | 14 | catálogo (CIS ref., severidad, categoría, mapeo oficial) |
| audit_runs.csv | 240 | por auditoría: aprobados/incumplidos/N-A/no evaluados, % cumplimiento, cobertura, duración |
| check_results.csv | 3 360 | por control: `status`, `ground_truth`, `match`, `duration_ms`, valor observado |
| evidence.jsonl | 3 360 | salida real (stdout/stderr/exit) de cada comando |
| findings.csv | 369 | ciclo de vida derivado: ronda de detección/resolución, persistencia, reaperturas (regresiones) |

## Resultados de referencia (para verificar tras regenerar)
- Estados: 1 890 passed, 1 236 failed, 71 N/A, 163 no evaluados.
- Cumplimiento medio por ronda: 44,0 → 53,3 → 62,1 → 65,7 → 67,4 → 68,9 %.
- Concordancia con la verdad esperada (sin fallas inyectadas): 3 117/3 197 (97,5 %). Para hallazgos (`failed`): precisión 95,6 %, recall 97,9 %.
- Tiempo medio por control ≈ 99 ms; por auditoría ≈ 1,4 s.
- Hallazgos: 369 (199 resueltos, 170 abiertos, 64 reaperturas).

## Defectos reales del motor detectados (los 80 desacuerdos)
1. **SHADOW-PERMS (55 falsos positivos):** `stat -c %a` devuelve `0` para el modo 000, pero la configuración permite `"000"` → un `/etc/shadow` con modo 000 se marca como incumplido.
2. **AUTH-PWQUALITY (17) y AUTH-FAILLOCK (8) falsos negativos:** el `grep` no ignora líneas comentadas (`# ... pam_pwquality.so`, `# ... pam_faillock.so`), así que un módulo PAM comentado cuenta como presente.

## Regenerar
`PYTHONPATH=<proyecto>/backend python3 scripts/build_dataset.py <salida>` (requiere root, Linux con overlayfs/unshare y las dependencias del backend; ≈ 90 s).
