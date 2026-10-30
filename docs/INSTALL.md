# Instalación y configuración

## 1. Requisitos

| Componente | Versión mínima | Notas |
| --- | --- | --- |
| Python | 3.11 | Probado con 3.11.9 |
| Node.js | 20 | Probado con 22.12 |
| PostgreSQL | 15 | Probado con 17.7 |
| n8n | 2.x | Opcional; los flujos se importaron con 2.8.4 |
| Ollama | actual | Opcional; modelo local |
| Docker | 24+ | Opcional, recomendado para despliegue |

## 2. Variables de entorno

```powershell
Copy-Item .env.example .env
```

Genere secretos reales:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Asigne, respectivamente, a `SECRET_KEY`, `FERNET_KEY` y `N8N_ENCRYPTION_KEY`.

Mínimos:

```dotenv
ENVIRONMENT=development
SECRET_KEY=<48+ caracteres>
FERNET_KEY=<clave Fernet base64>
DB_HOST=localhost
DB_PORT=5432
DB_NAME=27auditoria
DB_USER=postgres
DB_PASSWORD=<contraseña real>
FRONTEND_URL=http://localhost:5173
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
COOKIE_SECURE=false
AUDIT_ALLOW_PRIVATE_TARGETS=false
ENABLE_SIMULATED_CONNECTOR=false
AI_ENABLED=true
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.1:8b
```

No versione `.env`. `.env.example` no contiene credenciales reales.

### Secretos que no se pueden perder

- `FERNET_KEY`: sin ella no se pueden descifrar credenciales SSH.
- `SECRET_KEY`: invalida sesiones si cambia.
- `N8N_ENCRYPTION_KEY`: n8n no puede descifrar credenciales sin ella.

Guárdelos en un gestor de secretos y respáldelos por separado de PostgreSQL.

## 3. Instalación local

### 3.1 Base de datos

Cree la base vacía si no existe:

```powershell
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -c "CREATE DATABASE 27auditoria;"
```

El nombre empieza por número; si usa SQL manual, cite el identificador: `"27auditoria"`.

### 3.2 Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Compruebe:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
```

Salida esperada:

```json
{"status":"ok","version":"1.0.0","database":"ok"}
```

### 3.3 Frontend

```powershell
cd frontend
npm install
npm run dev
```

Vite publica `http://127.0.0.1:5173` y redirige `/api` a `127.0.0.1:8000`.

### 3.4 Primer arranque

1. Abra `http://127.0.0.1:5173`.
2. Cree organización, identificador, nombre, correo y contraseña del administrador.
3. La pantalla solo está disponible si no existe ningún usuario.
4. El setup crea el perfil inicial con los 14 controles.
5. No hay contraseña por defecto.

La contraseña debe tener 12+ caracteres y combinar al menos 3 de: minúsculas, mayúsculas, dígitos y
símbolos. Se almacena con bcrypt.

## 4. Docker Compose

### 4.1 Núcleo

```powershell
Copy-Item .env.example .env
# Complete DB_PASSWORD, SECRET_KEY, FERNET_KEY y N8N_ENCRYPTION_KEY
docker compose up -d --build
```

Servicios:

- `db`: PostgreSQL 17 con volumen persistente e init de la base `n8n`.
- `backend`: migra al iniciar y expone la API en `127.0.0.1:8000`.
- `frontend`: Nginx en `127.0.0.1:8080`.

Abra `http://127.0.0.1:8080` y realice el setup.

### 4.2 n8n

```powershell
docker compose --profile automation up -d n8n
```

n8n usa PostgreSQL, base `n8n`, y publica `127.0.0.1:5678`. El workflow usa
`http://host.docker.internal:8000/api/v1` como URL. En Linux, añada:

```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

al servicio `n8n` o cambie la URL a `http://backend:8000/api/v1`.

### 4.3 Ollama

```powershell
docker compose --profile ai up -d ollama
docker compose exec ollama ollama pull llama3.1:8b
```

El backend en Compose apunta por defecto a `http://ollama:11434`. Si usa Ollama en el host, cambie
`OLLAMA_BASE_URL` a `http://host.docker.internal:11434`.

### 4.4 Logs y estado

```powershell
docker compose ps
docker compose logs -f backend
docker compose logs -f frontend
```

## 5. n8n: importar flujos

1. Cree un token en **Configuración → Tokens de automatización** con los scopes necesarios.
2. En n8n, cree una credencial **Header Auth** llamada `CIS Hardening API Key`:
   - Header name: `X-API-Key`
   - Header value: el token `cisa_...`
3. Importe los archivos:

```powershell
n8n import:workflow --input="n8n/workflows/A_auditoria_programada.json"
n8n import:workflow --input="n8n/workflows/B_recomendaciones_ia.json"
n8n import:workflow --input="n8n/workflows/C_seguimiento_hallazgos.json"
n8n import:workflow --input="n8n/workflows/D_generacion_reportes.json"
```

4. Ajuste el nodo `Configuración → apiBaseUrl` si corresponde.
5. Asocie la credencial a los nodos HTTP.
6. Active los flujos.

Más detalle en [N8N.md](N8N.md).

## 6. Configuración de red y SSH

### 6.1 Objetivos privados

Por defecto:

```dotenv
AUDIT_ALLOW_PRIVATE_TARGETS=false
```

Para auditar redes internas, habilite globalmente y marque el servidor con
`allow_private_target=true` y autorización explícita. Puede restringir aún más:

```dotenv
AUDIT_ALLOW_PRIVATE_TARGETS=true
AUDIT_ALLOWED_CIDRS=10.20.0.0/16,192.168.50.0/24
```

Loopback, link-local, multicast y metadatos cloud se bloquean siempre.

### 6.2 Huella SSH

En el servidor:

```bash
ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub -E sha256
```

Copie el valor `SHA256:...` en el formulario. La plataforma conecta a la IP registrada y compara la
huella durante el handshake. Una huella distinta rechaza la conexión.

### 6.3 Usuario técnico

Use una cuenta de servicio con acceso SSH restringido. El motor **no ejecuta `sudo`** y solo lanza
comandos de lectura del catálogo. Si un comando no puede leer la configuración, el control queda
`not_evaluated`; no se eleva privilegios.

### 6.4 Conector simulado

Solo para pruebas y demostraciones:

```dotenv
ENABLE_SIMULATED_CONNECTOR=true
```

En `ENVIRONMENT=production` la aplicación rechaza esta configuración al arrancar. Los servidores y
reportes simulados se etiquetan como tales.

## 7. Ollama

Instalación local fuera de Docker:

```powershell
ollama serve
ollama pull llama3.1:8b
```

`GET /api/v1/settings` informa disponibilidad y modelo. Si Ollama está desconectado:

- la auditoría, el dashboard, los hallazgos y los reportes siguen funcionando;
- la generación de recomendaciones devuelve `503 ai_unavailable`;
- no se guarda una propuesta vacía.

## 8. Producción

Checklist mínimo:

```dotenv
ENVIRONMENT=production
DEBUG=false
COOKIE_SECURE=true
COOKIE_SAMESITE=lax
ENABLE_SIMULATED_CONNECTOR=false
CORS_ORIGINS=https://hardening.empresa.com
ALLOWED_HOSTS=hardening.empresa.com
TRUSTED_PROXY_IPS=10.0.0.10/32
AUDIT_ALLOW_PRIVATE_TARGETS=true
AUDIT_ALLOWED_CIDRS=10.20.0.0/16
```

- Termine TLS en Nginx/Traefik y fuerce HTTPS.
- No exponga PostgreSQL ni el puerto 8000 directamente a Internet.
- Restrinja la consola de n8n.
- Use contraseñas únicas para la base y rote API keys.
- Configure backups y monitoreo (ver [OPERATIONS.md](OPERATIONS.md)).
- Deshabilite `/api/docs` (ya ocurre con `ENVIRONMENT=production`).

## 9. Problemas frecuentes

| Síntoma | Causa / solución |
| --- | --- |
| `SECRET_KEY debe tener al menos 32 caracteres` | Genere una clave real en `.env` |
| `FERNET_KEY inválida` | Use una clave Fernet base64 de 32 bytes |
| `No existe la base de datos` | Cree `27auditoria` o ajuste `DB_NAME` |
| No aparecen servidores | Verifique organización y `is_active` |
| `Las auditorías a redes privadas están deshabilitadas` | Active `AUDIT_ALLOW_PRIVATE_TARGETS` y autorización del servidor |
| `La huella del host SSH no coincide` | Verifique el servidor y actualice la huella; no la ignore |
| Control `not_evaluated` | Falta permiso de lectura, comando no disponible o `systemd` ausente |
| `503 ai_unavailable` | Inicie Ollama y descargue el modelo |
| 401 en consola | Sesión expirada o cambio de contraseña; vuelva a iniciar sesión |
| CORS bloqueado | Ajuste `CORS_ORIGINS` con el origen exacto |
| Migración bloqueada | Revise conexiones activas y permisos del usuario PostgreSQL |
