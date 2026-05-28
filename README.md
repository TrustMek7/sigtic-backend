# SIGTIC Backend

API REST del Sistema de Gestión de Tickets TI — Unidad de Informática Municipal.

**Stack:** Python 3.13 · Django 4.2 · Django REST Framework · PostgreSQL 15 · SimpleJWT (cookies httpOnly)

---

## Requisitos previos

| Herramienta | Versión mínima | Verificar |
|---|---|---|
| Python | 3.11 | `python --version` |
| PostgreSQL | 15 | `psql --version` |
| pip | última | `pip --version` |

> La conexión a **bdsiggo** (PostgreSQL ~8.x, base legada de SIGGO) es **opcional** para desarrollo local. Sin ella el backend funciona, pero el login solo acepta usuarios creados directamente con `createsuperuser`.

---

## 1. Entorno virtual e instalación

```bash
# Desde la carpeta sigtic-backend/
python -m venv .venv

# Activar — Windows
.venv\Scripts\activate
# Activar — Linux / Mac
source .venv/bin/activate

pip install -r requirements/development.txt
```

> **Windows + Python 3.13:** el venv ya está creado en `.venv/`. Solo actívalo y ejecuta el pip install.
> `psycopg2-binary 2.9.10` incluye wheel pre-compilado para Python 3.13 en Windows, no necesita Visual C++.

---

## 2. Base de datos PostgreSQL

Abre `psql` como superusuario (`postgres`) y ejecuta:

```sql
-- Crear usuario del sistema
CREATE USER sigtic WITH PASSWORD 'sigtic1234';

-- Crear la base de datos principal
CREATE DATABASE sigtic_db
    WITH OWNER = sigtic
    ENCODING = 'UTF8'
    LC_COLLATE = 'es_PE.UTF-8'   -- ajusta según tu SO
    LC_CTYPE   = 'es_PE.UTF-8'
    TEMPLATE   = template0;

-- Dar privilegios
GRANT ALL PRIVILEGES ON DATABASE sigtic_db TO sigtic;
```

> **Windows:** si el locale `es_PE.UTF-8` no existe usa `Spanish_Peru.1252` o directamente `'C'`.

---

## 3. Variables de entorno

Copia el ejemplo y edítalo:

```bash
cp .env.example .env
```

Contenido mínimo para desarrollo local **sin** bdsiggo:

```ini
SECRET_KEY=dev-secret-key-cambia-en-produccion
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# sigtic_db
SIGTIC_DB_NAME=sigtic_db
SIGTIC_DB_USER=sigtic
SIGTIC_DB_PASSWORD=sigtic1234
SIGTIC_DB_HOST=localhost
SIGTIC_DB_PORT=5432

# bdsiggo — dejar HOST vacío para deshabilitar la conexión en dev
SIGGO_DB_NAME=bdsiggo
SIGGO_DB_USER=
SIGGO_DB_PASSWORD=
SIGGO_DB_HOST=
SIGGO_DB_PORT=5432

SIGGO_PASSWORD_ALGO=md5

CORS_ALLOWED_ORIGINS=http://localhost:4200

JWT_ACCESS_TOKEN_LIFETIME_MINUTES=60
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7
JWT_COOKIE_SECURE=False
JWT_COOKIE_SAMESITE=Lax
```

Cuando `SIGGO_DB_HOST` está vacío el router bloquea la conexión a bdsiggo y el backend usa solo `sigtic_db`.

---

## 4. Migraciones

```bash
# Solo la base principal (sigtic_db)
python manage.py migrate

# Si bdsiggo está configurado, verifica que el router funcione
python manage.py check --database=default
```

Las migraciones de `apps.siggo_readonly` tienen `managed = False` — no crean tablas, solo definen los modelos de lectura.

### Estructura de migraciones por app

| App | Nota |
|---|---|
| `users` | Crea `user_profile`, `user_cargo`, `encargado_activo` |
| `organizacion` | Crea `sede`, `unidad_organica`, `subgerencia`, `dependencia` |
| `catalogo` | Crea tablas de catálogos + fixtures iniciales |
| `inventario` | Crea `dispositivo` y las 7 subtablas (`disp_*`), `bien_baja` |
| `almacen` | Crea `stock_consumible`, `movimiento_stock` |
| `tickets` | Crea la secuencia PostgreSQL + todas las tablas de tickets |
| `documentos` | Crea `documento_oficial` + carpeta `mediafiles/documentos/` |

---

## 5. Superusuario de administración

```bash
python manage.py createsuperuser
```

Accede al panel Django Admin en: `http://localhost:8000/admin/`

Este usuario se autentica con Django auth (no bdsiggo), útil para gestión inicial de datos.

---

## 6. Datos iniciales (fixtures)

```bash
# Tipos de dispositivo, marcas base, SO comunes, etc.
python manage.py loaddata catalogo_inicial
```

> Si el fixture no existe aún, puedes cargar datos manualmente desde el admin o la API.

---

## 7. Levantar el servidor de desarrollo

```bash
python manage.py runserver
```

El servidor queda disponible en `http://localhost:8000`.

### Endpoints principales

| Endpoint | Descripción |
|---|---|
| `GET /api/v1/auth/me/` | Perfil del usuario autenticado |
| `POST /api/v1/auth/login/` | Login (setea cookies httpOnly) |
| `POST /api/v1/auth/logout/` | Logout (borra cookies) |
| `POST /api/v1/auth/refresh/` | Renovar token de acceso |
| `GET /api/v1/tickets/` | Listado de tickets (filtros por estado) |
| `POST /api/v1/tickets/` | Crear ticket |
| `POST /api/v1/tickets/{id}/transicion/` | Cambiar estado del ticket |
| `POST /api/v1/tickets/{id}/diagnostico/` | Registrar diagnóstico técnico |
| `POST /api/v1/tickets/{id}/documento/` | Generar PDF oficial |
| `GET /api/v1/inventario/dispositivos/` | Listado de dispositivos |
| `GET /api/v1/almacen/stock/` | Stock de consumibles |
| `GET /api/v1/almacen/movimientos/` | Historial de movimientos |
| `GET /api/v1/auth/users/` | Listado de usuarios (solo IT) |
| `GET /api/v1/auth/encargados/` | Encargados activos |

**Documentación interactiva (Swagger):** `http://localhost:8000/api/schema/swagger-ui/`

---

## 8. Estructura del proyecto

```
sigtic-backend/
├── config/
│   ├── settings/
│   │   ├── base.py          # configuración común
│   │   ├── development.py   # DEBUG=True, logs
│   │   └── production.py    # WhiteNoise, HTTPS, etc.
│   └── urls.py              # rutas raíz
│
├── apps/
│   ├── siggo_readonly/      # modelos managed=False de bdsiggo (solo lectura)
│   ├── users/               # UserProfile, auth backend SIGGO, cookies JWT
│   │   ├── backends.py      # SiggoAuthBackend — autentica contra bdsiggo
│   │   ├── sync.py          # sync_cargos_from_siggo()
│   │   └── cookie_auth.py   # CookieJWTAuthentication
│   ├── organizacion/        # Sede, UnidadOrganica, Subgerencia, Dependencia
│   ├── catalogo/            # Marca, TipoDispositivo, SO, Procesador, MemoriaRam, Consumible
│   ├── inventario/          # Dispositivo + 7 subtablas + BienBaja
│   ├── almacen/             # StockConsumible, MovimientoStock
│   ├── tickets/             # Ticket, Historial, Diagnostico, Tercerizado...
│   └── documentos/          # DocumentoOficial + generador PDF (ReportLab)
│
├── routers/
│   └── db_router.py         # SiggoRouter — dirige siggo_readonly a bdsiggo, bloquea escrituras
│
├── requirements/
│   ├── base.txt
│   ├── development.txt      # + django-debug-toolbar
│   └── production.txt       # + gunicorn, whitenoise
│
├── .env.example
└── manage.py
```

---

## 9. Flujo de autenticación

```
Angular POST /api/v1/auth/login/
    ↓
SiggoAuthBackend.authenticate()
    ├── Busca usu_usu en sogem.usuario (bdsiggo) — si HOST vacío, salta
    ├── Verifica hash MD5/SHA1/bcrypt del password
    ├── Obtiene nombre/DNI de sogem.persona
    ├── Crea/actualiza User Django + UserProfile en sigtic_db
    └── Sincroniza cargos desde siggo.cargo
    ↓
LoginView._set_tokens_in_cookies()
    └── Set-Cookie: sigtic_access (httpOnly, SameSite=Lax)
    └── Set-Cookie: sigtic_refresh (httpOnly, SameSite=Lax)
    ↓
Response 200 { id, nombre_completo, rol, rol_display }
```

**Sin bdsiggo configurado:** el backend usa `django.contrib.auth.backends.ModelBackend` como fallback, que autentica contra la tabla `auth_user` de Django (solo funciona con usuarios creados por `createsuperuser`).

---

## 10. Conexión a bdsiggo (producción)

Cuando tengas acceso al servidor PostgreSQL ~8.x del SIGGO, completa estas variables en `.env`:

```ini
SIGGO_DB_HOST=192.168.x.x      # IP del servidor bdsiggo
SIGGO_DB_USER=lector_sigtic     # usuario con SELECT en sogem y siggo
SIGGO_DB_PASSWORD=password
SIGGO_PASSWORD_ALGO=md5         # verificar contra la base real
```

**Notas de compatibilidad PG 8.x:**
- No usar `default_transaction_read_only` — no soportado en PG 8
- El router Django bloquea toda escritura a `siggo` a nivel ORM
- Solo SQL básico: sin `RETURNING`, sin CTEs, sin `json_agg`, sin `LATERAL`
- Encoding del servidor puede ser `LATIN1` — psycopg2 lo convierte automáticamente

---

## 11. Comandos de referencia rápida

```bash
# Activar entorno
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux/Mac

# Crear/aplicar migraciones
python manage.py makemigrations
python manage.py migrate

# Servidor desarrollo
python manage.py runserver

# Shell interactivo
python manage.py shell

# Ver rutas registradas
python manage.py show_urls      # requiere django-extensions

# Verificar configuración
python manage.py check

# Colectar estáticos (producción)
python manage.py collectstatic --no-input
```

---

## 12. Roles del sistema

| Rol | Descripción |
|---|---|
| `ADMIN` | Acceso total, gestión de usuarios |
| `JEFE_INFO` | Asigna tickets, gestiona encargados temporales |
| `ENCARGADO_INFO` | Asigna tickets mientras el jefe está ausente |
| `TECNICO` | Atiende tickets asignados, registra diagnósticos |
| `USUARIO` | Solo crea y ve sus propios tickets |

El rol se asigna en `UserProfile.rol` desde el admin o el endpoint `PATCH /api/v1/auth/users/{id}/`.

---

## 13. Máquina de estados de tickets

```
ENVIADO → EN_REVISION → ASIGNADO → EN_ATENCION
                                        ├─ MENOR      → SOLUCIONADO   [terminal]
                                        ├─ MAYOR      → EN_MANTENIMIENTO → FINALIZADO [terminal]
                                        └─ TERCERIZADO → TERCERIZADO  → FINALIZADO [terminal]

Desde cualquier estado no terminal:
  → RECHAZADO (solo JEFE_INFO / ENCARGADO_INFO activo)  [terminal]
```
