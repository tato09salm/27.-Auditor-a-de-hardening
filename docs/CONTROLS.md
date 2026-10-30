# Controles iniciales

## 1. Alcance y honestidad del mapeo

El catálogo inicial corresponde a **Ubuntu Linux 22.04 LTS**, con referencias contrastadas contra
**CIS Ubuntu Linux 22.04 LTS Benchmark v1.0.0**. Los identificadores oficiales se tomaron del
documento; no se inventaron.

Tres niveles se muestran en la aplicación:

| Marca | Significado |
| --- | --- |
| **CIS** | El identificador y el requisito se contrastaron con el benchmark v1.0.0 |
| **Interno** | Control propio inspirado en buenas prácticas; no es un mapeo oficial |
| **Preliminar** | El benchmark lo marca como Manual o el parser es una automatización propia; se documenta la limitación |

El motor se validó sobre Ubuntu 22.04/24.04 con OpenSSH y APT. Antes de usar otro Linux, revise
comandos, rutas y mapeos. El benchmark es un documento de CIS; esta plataforma **no está certificada
por CIS**.

## 2. Catálogo

| Código interno | CIS | Título | Severidad | Nivel | Tipo | Comprobación |
| --- | --- | --- | --- | --- | --- | --- |
| `SSH-ROOT` | 5.2.7 | Acceso SSH directo de root deshabilitado | Alta | 1 | Oficial | `sshd -T` o configuración; exige `PermitRootLogin no` |
| `SSH-MAXAUTH` | 5.2.18 | SSH limita intentos de autenticación | Media | 1 | Oficial | `MaxAuthTries <= 4` |
| `SSH-EMPTY` | 5.2.9 | SSH rechaza contraseñas vacías | Alta | 1 | Oficial | `PermitEmptyPasswords no` |
| `SSH-KEYONLY` | — | SSH prefiere clave pública | Media | — | Interno | `PasswordAuthentication no` y `PubkeyAuthentication` habilitado |
| `AUTH-PWQUALITY` | 5.4.1 | Requisitos de complejidad de contraseñas | Alta | 1 | Oficial | `minlen >= 14` y `pam_pwquality` presente |
| `AUTH-FAILLOCK` | 5.4.2 | Bloqueo por intentos fallidos | Alta | 1 | Oficial | `pam_faillock`, `deny <= 5`, `unlock_time >= 900` |
| `FW-ENABLED` | 3.5.1.3 | Firewall UFW habilitado | Alta | 1 | Oficial | Servicio activo, habilitado y `ENABLED=yes` |
| `FW-DEFAULT` | 3.5.1.7 | Política por defecto: denegar entrada | Alta | 1 | Oficial | `DEFAULT_INPUT_POLICY=DROP/REJECT` |
| `UPDATES` | 1.9 | Actualizaciones y parches instalados | Alta | 1 | Oficial / preliminar | `apt-get -s upgrade`; exige 0 paquetes pendientes |
| `SHADOW-PERMS` | 6.1.5 | Permisos restrictivos sobre `/etc/shadow` | Alta | 1 | Oficial | Modo 640/600/400 y propietario root |
| `LOGGING` | 4.2.2.2 | rsyslog habilitado y activo | Media | 1 | Oficial | Servicio activo, habilitado e instalado |
| `AUDITD` | 4.1.1.2 | auditd habilitado y activo | Media | 2 | Oficial | Servicio activo, habilitado e instalado |
| `ASLR` | 1.5.1 | Aleatorización del espacio de direcciones | Media | 1 | Oficial | `kernel.randomize_va_space = 2` |
| `SERVICES` | — | Servicios de red innecesarios | Media | — | Interno | Unidades habilitadas de una lista de riesgo |

### 2.1 `SSH-ROOT`

- **Requisito:** `PermitRootLogin no`.
- **Evidencia:** línea efectiva de `sshd -T` o `sshd_config`.
- **Decisión:** si no está definido, se considera incumplido (el valor por defecto no es `no`).
- **Corrección de referencia:** respaldar configuración, cambiar, `sshd -t`, conservar sesión abierta,
  recargar, validar con usuario nominativo y rollback.
- **Riesgo:** bloquear el acceso si no existe una cuenta con sudo funcional.

### 2.2 `SSH-MAXAUTH`

- **Requisito:** `MaxAuthTries <= 4`.
- **Evidencia:** configuración efectiva o valor por defecto (6) si no se define.
- **Limitación:** un `Match` posterior puede alterar el valor; el parser toma la última línea global.

### 2.3 `SSH-EMPTY`

- **Requisito:** `PermitEmptyPasswords no`.
- **Decisión:** ausencia del parámetro se considera conforme por el valor por defecto de OpenSSH,
  indicando `default-no` en la evidencia.

### 2.4 `SSH-KEYONLY`

- **Control interno.** CIS no exige deshabilitar contraseñas SSH en todos los perfiles.
- Exige `PasswordAuthentication no` y `PubkeyAuthentication` distinto de `no`.
- Antes de corregir, distribuya claves, pruebe acceso y defina recuperación.

### 2.5 `AUTH-PWQUALITY`

- **Requisito:** `pam_pwquality` cargado y `minlen >= 14`.
- **Evidencia:** `/etc/security/pwquality.conf` y `/etc/pam.d/common-password`.
- **Limitación:** PAM personalizado o configuración en otros archivos puede dar falso negativo.

### 2.6 `AUTH-FAILLOCK`

- **Requisito:** `pam_faillock` en `common-auth`/`common-account`, `deny <= 5`,
  `unlock_time >= 900`.
- **Decisión:** si no se declaran umbrales, se considera incumplido; no se asumen valores por defecto.
- **Limitación:** `pam_tally2` legado se detecta pero no se evalúa como equivalente completo.

### 2.7 `FW-ENABLED`

- **Requisito:** UFW instalado, servicio activo y habilitado, `ENABLED=yes`.
- **Evidencia:** `systemctl is-active/is-enabled`, `/etc/ufw/ufw.conf`.
- **Riesgo de corrección:** habilitar UFW sin permitir SSH puede cortar el acceso. Revise reglas y
  mantenga sesión abierta.

### 2.8 `FW-DEFAULT`

- **Requisito:** `DEFAULT_INPUT_POLICY` en `DROP` o `REJECT`.
- **Decisión:** si UFW no está instalado, el control queda **no aplicable**; `FW-ENABLED` ya refleja
  el fallo.
- **Limitación:** no evalúa reglas por puerto ni IPv6 por separado.

### 2.9 `UPDATES`

- **Requisito:** cero paquetes actualizables en la simulación de APT.
- **Evidencia:** `apt-get -s -o Debug::NoLocking=1 upgrade`.
- **Mapeo:** CIS 1.9 está marcado como **Manual**; esta es una automatización propia.
- **Limitación:** no distingue parches de seguridad de actualizaciones funcionales ni valida el
  reinicio pendiente. No sustituye un ciclo de gestión de parches.

### 2.10 `SHADOW-PERMS`

- **Requisito:** `/etc/shadow` con modo 640/600/400 y propietario root, grupo shadow o root.
- **Evidencia:** `stat -c '%a %U %G %n'`.
- **Limitación:** no evalúa ACL extendidas ni otros archivos (`shadow-`, `gshadow`) para la decisión.

### 2.11 `LOGGING`

- **Requisito:** rsyslog instalado, activo y habilitado.
- **Evidencia:** `systemctl`, presencia de `rsyslogd`.
- **Limitación:** no verifica destino remoto ni retención.

### 2.12 `AUDITD`

- **Requisito:** auditd instalado, activo y habilitado. Nivel 2 del benchmark.
- **Evidencia:** `systemctl`, presencia de `auditctl`.
- **Limitación:** no valida reglas de auditoría ni el parámetro de arranque.

### 2.13 `ASLR`

- **Requisito:** `kernel.randomize_va_space = 2`.
- **Evidencia:** `sysctl -n`.
- **Limitación:** no comprueba persistencia tras reinicio; la guía de corrección recomienda sysctl.d.

### 2.14 `SERVICES`

- **Control interno** inspirado en CIS 2.4.
- Lista de riesgo inicial: telnet, rsh, rlogin, rexec, vsftpd, xinetd, tftp, avahi, cups.
- **Decisión:** cualquier unidad habilitada de la lista produce incumplimiento.
- **Limitación:** la lista puede tener falsos positivos si el servicio es necesario. Requiere
  validación del propietario antes de deshabilitar.

## 3. Estados de un control

| Estado | Significado | ¿Cuenta en score? |
| --- | --- | --- |
| `passed` | Criterio verificado y evidencia disponible | Numerador |
| `failed` | Criterio incumplido o no demostrable | Denominador |
| `not_applicable` | El control no aplica al sistema | No |
| `not_evaluated` | No se pudo ejecutar/leer la evidencia | No; se informa cobertura |

El score nunca es 100 si no hay controles aplicables evaluados; en ese caso es `null`.

## 4. Ejecución y evidencias

- Comandos estáticos en `backend/app/services/checks.py`.
- Sin argumentos del usuario en la shell.
- Sin `sudo`.
- Timeout por comando y tamaño máximo de salida.
- La evidencia se trunca a 8 KB en la vista estándar y se guarda con estado de truncado.
- El comando se muestra en la consola para auditoría; no contiene secretos.
- La fecha de evaluación y la duración se guardan por control.

## 5. Cómo ampliar el catálogo

1. Verifique el texto exacto del benchmark y la versión.
2. Cree un nuevo `CisControl` en una migración de datos, no modifique ejecuciones históricas.
3. Registre la comprobación en `CHECKS` con un comando de solo lectura y un parser explícito.
4. Añada pruebas con salidas reales buenas, malas y truncadas.
5. Documente falsos positivos/negativos y el nivel de confianza.
6. No marque `is_official_mapping=true` sin contraste documental.

## 6. Fuente

- CIS Ubuntu Linux 22.04 LTS Benchmark v1.0.0.
- Página oficial: <https://www.cisecurity.org/benchmark/ubuntu_linux>
- Documentación de OpenSSH, PAM, UFW y sysctl de Ubuntu.

Los controles internos están etiquetados en la API (`is_official_mapping=false`) y en la interfaz.
