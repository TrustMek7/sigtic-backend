# SIGTIC Backend

API REST del Sistema de Gestión de Tickets TI — Unidad de Informática Municipal.

**Stack:** Python 3.13 · Django 4.2 · Django REST Framework · PostgreSQL 15 · SimpleJWT (cookies httpOnly)

---

## Requisitos previos

| Herramienta | Versión mínima | Verificar |
|---|---|---|
| Python | 3.13 | `python --version` |
| PostgreSQL | 15 | `psql --version` |

> La conexión a **bdsiggo** (PostgreSQL ~8.x, base legada de SIGGO) es **opcional** en desarrollo. Sin ella el login funciona con usuarios Django creados por `createsuperuser`. Dejando `SIGGO_DB_HOST` vacío en `.env` la conexión queda deshabilitada.

---

## 1. Entorno virtual e instalación

```bash
cd sigtic-backend

# Crear y activar venv
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux / Mac

pip install -r requirements/development.txt
```

El venv ya está creado en `.venv/`. `psycopg2-binary 2.9.10` incluye wheel pre-compilado para Python 3.13 en Windows — no requiere Visual C++.

---

## 2. Base de datos PostgreSQL

Ejecuta en `psql` como superusuario (`postgres`):

```sql
CREATE USER sigtic WITH PASSWORD 'sigtic1234';
CREATE DATABASE sigtic_db
    WITH OWNER = sigtic
    ENCODING = 'UTF8'
    TEMPLATE = template0;
GRANT ALL PRIVILEGES ON DATABASE sigtic_db TO sigtic;
```

> **Windows:** si el locale `es_PE.UTF-8` no existe usa `TEMPLATE = template0` sin especificar LC_COLLATE.

---

## 3. Variables de entorno

```bash
cp .env.example .env
```

Edita `.env` con las credenciales de tu base de datos:

```ini
SECRET_KEY=dev-secret-key-cambia-en-produccion
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# sigtic_db — base principal
SIGTIC_DB_NAME=sigtic_db
SIGTIC_DB_USER=sigtic
SIGTIC_DB_PASSWORD=sigtic1234
SIGTIC_DB_HOST=localhost
SIGTIC_DB_PORT=5432

# bdsiggo — dejar HOST vacío para deshabilitar en desarrollo
SIGGO_DB_HOST=

CORS_ALLOWED_ORIGINS=http://localhost:4200
JWT_COOKIE_SECURE=False
JWT_COOKIE_SAMESITE=Lax
```

---

## 4. Migraciones

```bash
python manage.py makemigrations --settings=config.settings.development
python manage.py migrate --settings=config.settings.development
```

---

## 5. Superusuario

```bash
python manage.py createsuperuser --settings=config.settings.development
```

Este usuario se autentica con Django auth (no bdsiggo). Al hacer login por primera vez se crea automáticamente un `UserProfile` con rol **ADMIN**.

**Credenciales de demo:** si usaste `createsuperuser` con usuario `admin`, puedes resetear el password:

```bash
python manage.py shell --settings=config.settings.development -c "
from django.contrib.auth import get_user_model
U = get_user_model()
u = U.objects.get(username='admin')
u.set_password('admin123')
u.save()
print('Password: admin123')
"
```

---

## 6. Datos de demostración

```bash
# Cargar datos de prueba (catálogo, dispositivos, tickets, usuarios, stock)
python manage.py seed_demo --settings=config.settings.development

# Borrar todo y recargar limpio
python manage.py seed_demo --flush --settings=config.settings.development
```

Carga: 7 tipos de dispositivo, 12 marcas, 2 sedes, 7 perfiles con distintos roles, 15 dispositivos (PCs, impresoras, monitores, redes), 8 tickets en distintos estados con historial, 5 consumibles en stock y 2 bienes de baja.

---

## 7. Servidor de desarrollo

```bash
python manage.py runserver --settings=config.settings.development
```

Disponible en `http://localhost:8000`.

- **Admin Django:** `http://localhost:8000/admin/`
- **Swagger UI:** `http://localhost:8000/api/docs/`
- **OpenAPI schema:** `http://localhost:8000/api/schema/`

---

## 8. Estructura del proyecto

```
sigtic-backend/
├── config/
│   ├── settings/
│   │   ├── base.py            # JWT cookies, 2 DBs, CORS, DRF, paginación
│   │   ├── development.py     # DEBUG=True, CORS sin restricciones, django-extensions
│   │   └── production.py      # WhiteNoise, HTTPS, cookies Secure
│   └── urls.py                # Rutas raíz de la API
│
├── apps/
│   ├── siggo_readonly/        # Modelos managed=False de bdsiggo (solo lectura)
│   ├── users/
│   │   ├── backends.py        # SiggoAuthBackend — autentica contra bdsiggo
│   │   ├── sync.py            # sync_cargos_from_siggo() al login
│   │   ├── cookie_auth.py     # CookieJWTAuthentication (lee JWT de cookie)
│   │   ├── permissions.py     # EsInformatica, EsJefeOEncargado, EsJefe, EsAdmin
│   │   └── views.py           # Login, Logout, Refresh, Me, Users, Encargados
│   ├── organizacion/          # Sede, UnidadOrganica, Subgerencia, Dependencia
│   ├── catalogo/              # Marca, TipoDispositivo, SO, Procesador, RAM, Consumible
│   ├── inventario/            # Dispositivo + 7 subtablas (disp_*) + BienBaja
│   ├── almacen/               # StockConsumible, MovimientoStock
│   ├── tickets/
│   │   ├── models.py          # Ticket, TicketHistorial, Diagnostico, Tercerizado…
│   │   └── management/
│   │       └── commands/
│   │           └── seed_demo.py  # Datos de demostración
│   └── documentos/            # DocumentoOficial + generador PDF (ReportLab)
│
├── routers/
│   └── db_router.py           # SiggoRouter: siggo_readonly → bdsiggo, bloquea escrituras
│
├── scripts/
│   ├── seed_data.py           # Script inicial de datos (usar seed_demo en su lugar)
│   └── seed_fix.py            # Parche de datos (histórico)
│
├── requirements/
│   ├── base.txt               # Django, DRF, SimpleJWT, psycopg2, reportlab…
│   ├── development.txt        # + ipython, django-extensions
│   └── production.txt         # + gunicorn, whitenoise
│
├── .env.example               # Plantilla de variables de entorno
├── .gitignore
└── manage.py
```

---

## 9. Endpoints principales

| Método | Endpoint | Descripción | Roles |
|---|---|---|---|
| POST | `/api/v1/auth/login/` | Login → setea cookies JWT | Todos |
| POST | `/api/v1/auth/logout/` | Cierra sesión, borra cookies | Autenticado |
| POST | `/api/v1/auth/refresh/` | Renueva access token desde cookie | Todos |
| GET | `/api/v1/auth/me/` | Perfil del usuario autenticado | Autenticado |
| GET/PATCH | `/api/v1/auth/users/` | Lista y actualiza roles | IT |
| GET/POST | `/api/v1/auth/encargados/` | Encargados temporales | JEFE/ADMIN |
| GET/POST | `/api/v1/tickets/` | Lista y crea tickets | Autenticado |
| GET | `/api/v1/tickets/{id}/` | Detalle de ticket | Autenticado |
| POST | `/api/v1/tickets/{id}/transicion/` | Cambia estado del ticket | IT |
| POST | `/api/v1/tickets/{id}/diagnostico/` | Registra diagnóstico técnico | TECNICO+ |
| POST | `/api/v1/tickets/{id}/documento/` | Genera PDF oficial | JEFE/ADMIN |
| GET/POST | `/api/v1/inventario/dispositivos/` | Inventario de dispositivos | IT |
| GET/PATCH | `/api/v1/inventario/dispositivos/{id}/` | Detalle y edición | IT |
| GET/POST | `/api/v1/inventario/bajas/` | Bienes de baja | IT |
| GET/POST | `/api/v1/almacen/stock/` | Stock de consumibles | IT |
| GET/POST | `/api/v1/almacen/movimientos/` | Movimientos de stock | IT |
| GET | `/api/v1/organizacion/sedes/` | Catálogo de sedes | IT |
| GET | `/api/v1/catalogo/tipos-dispositivo/` | Tipos de dispositivo | IT |

---

## 10. Flujo de autenticación

```
Frontend POST /api/v1/auth/login/
    ↓
SiggoAuthBackend.authenticate()
    ├── Si SIGGO_DB_HOST vacío → pasa a ModelBackend (Django users)
    ├── Verifica hash en sogem.usuario (MD5/SHA1/bcrypt según .env)
    ├── Crea/actualiza UserProfile en sigtic_db
    └── Sincroniza cargos desde siggo.cargo
    ↓
LoginView → crea JWT → Set-Cookie: sigtic_access + sigtic_refresh (httpOnly)
    ↓
Response 200 { id, nombre_completo, rol, rol_display }
```

---

## 11. Máquina de estados de tickets

```
ENVIADO → EN_REVISION → ASIGNADO → EN_ATENCION
                                        ├─ MENOR       → SOLUCIONADO      [terminal]
                                        ├─ MAYOR       → EN_MANTENIMIENTO → FINALIZADO [terminal]
                                        └─ TERCERIZADO → TERCERIZADO      → FINALIZADO [terminal]

Desde cualquier estado no terminal:
    → RECHAZADO  (solo JEFE_INFO / ENCARGADO_INFO activo)              [terminal]
```

---

## 12. Conexión a bdsiggo en producción

Cuando tengas acceso al servidor PostgreSQL ~8.x de SIGGO, configura en `.env`:

```ini
SIGGO_DB_HOST=192.168.x.x
SIGGO_DB_USER=lector_sigtic
SIGGO_DB_PASSWORD=password
SIGGO_PASSWORD_ALGO=md5
```

**Notas de compatibilidad PG 8.x:**
- El router Django bloquea toda escritura a nivel ORM (`RuntimeError` en `db_for_write`)
- No se usa `default_transaction_read_only` (no soportado en PG 8)
- Solo SQL básico: sin `RETURNING`, sin CTEs, sin funciones JSON

---

## 13. Comandos de referencia rápida

```bash
# Activar entorno
.venv\Scripts\activate                          # Windows
source .venv/bin/activate                       # Linux/Mac

# Migraciones
python manage.py makemigrations --settings=config.settings.development
python manage.py migrate --settings=config.settings.development

# Datos de demo
python manage.py seed_demo --flush --settings=config.settings.development

# Servidor
python manage.py runserver --settings=config.settings.development

# Shell interactivo
python manage.py shell --settings=config.settings.development

# Verificar configuración
python manage.py check --settings=config.settings.development

# Estáticos (producción)
python manage.py collectstatic --no-input --settings=config.settings.production
```
