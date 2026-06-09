"""
Migración del inventario desde inventario_bd.json hacia SIGTIC.

Ejecutar desde sigtic-backend/:
    python manage.py shell --settings=config.settings.development < scripts/load_inventario.py

Carga en orden:
  1. Catálogo: SistemaOperativo, Procesador, MemoriaRam, Consumible, Marca, TipoDispositivo
  2. Organización: Sede, UnidadOrganica (area), Subgerencia, Dependencia
  3. Trabajadores → UserProfile
  4. Dispositivos: tbl_cpu, tbl_equipos, tbl_impresoras, tbl_telefonos, camaras
  5. Almacén: tbl_almacen → StockConsumible
  6. Bienes de baja: tbl_bienes_baja → BienBaja
  7. Usuarios demo: jefe_info / encargado_demo / tecnico_demo / tecnico2 / tecnico3 / usuario_demo
"""

import json
import datetime
import ipaddress
from pathlib import Path

# ── Cargar JSON ───────────────────────────────────────────────────────────────
from django.conf import settings as _dj_settings
# BASE_DIR apunta a sigtic-backend/; subir un nivel llega a la raíz del proyecto
_JSON_PATH = Path(_dj_settings.BASE_DIR).parent / "database_migration" / "inventario_bd.json"

if not _JSON_PATH.exists():
    raise FileNotFoundError(f"No se encontró el JSON en: {_JSON_PATH}")

with open(_JSON_PATH, encoding="utf-8") as _f:
    _raw = json.load(_f)

tables = {}
for _entry in _raw:
    if _entry.get("type") == "table":
        tables[_entry["name"]] = _entry.get("data", [])

print(f"Tablas JSON cargadas: {sorted(tables.keys())}")
print()

# ── Helpers ───────────────────────────────────────────────────────────────────

def s(v):
    """Limpia string; retorna ''  si None."""
    return (v or "").strip()

def i(v):
    """Convierte a int; retorna None si inválido."""
    try:
        return int(v) if v is not None and str(v).strip() else None
    except (ValueError, TypeError):
        return None

def ip_val(v):
    """Retorna IP válida o None."""
    v = s(v)
    if not v or v.upper() in ("WIFI", "USB", "S/N", "-", ""):
        return None
    # Eliminar sufijos como '-LAN-CLARO'
    v = v.split()[0].split("-LAN")[0]
    try:
        ipaddress.ip_address(v)
        return v
    except ValueError:
        return None

def mac_val(v):
    """Retorna MAC recortada a 17 chars."""
    v = s(v)
    return v[:17] if v else ""

def bool_si(v):
    """'SI' / '1' → True, resto → False."""
    return s(v).upper() in ("SI", "1")

# ── 1. Catálogo ───────────────────────────────────────────────────────────────
from apps.catalogo.models import TipoDispositivo, Marca, SistemaOperativo, Procesador, MemoriaRam, Consumible

# TipoDispositivo (seeds canónicos)
_tipos = [
    ("COMPUTADORA", "Computadora",    True),
    ("IMPRESORA",   "Impresora",      True),
    ("MONITOR",     "Monitor",        True),
    ("PERIFERICO",  "Periférico",     True),
    ("RED",         "Equipo de Red",  True),
    ("CAMARA",      "Cámara",         True),
    ("TELEFONO",    "Teléfono IP",    True),
]
tipo_map = {}
for _cod, _nom, _sub in _tipos:
    _t, _ = TipoDispositivo.objects.get_or_create(codigo=_cod, defaults={"nombre": _nom, "tiene_subtabla": _sub})
    tipo_map[_cod] = _t
print(f"TipoDispositivo : {len(tipo_map)}")

# Mapeo denominacion_id → (codigo_tipo, subtipo_hint)
DENOM = {
    2:  ("RED",         "SERVIDOR"),
    26: ("COMPUTADORA", "DESKTOP"),
    23: ("COMPUTADORA", "LAPTOP"),
    27: ("IMPRESORA",   "LASER"),
    28: ("TELEFONO",    ""),
    13: ("CAMARA",      "DOMO"),
    14: ("RED",         "DVR"),
    15: ("PERIFERICO",  "OTRO"),
    30: ("MONITOR",     ""),
    16: ("RED",         "OTRO"),
    9:  ("RED",         "SWITCH"),
    10: ("RED",         "ROUTER"),
    47: ("RED",         "ROUTER"),
    5:  ("RED",         "SWITCH"),
    6:  ("RED",         "SWITCH"),
    7:  ("RED",         "SWITCH"),
    31: ("RED",         "SWITCH"),
    4:  ("RED",         "SWITCH"),
    3:  ("RED",         "SWITCH"),
    44: ("RED",         "SWITCH"),
    45: ("RED",         "SWITCH"),
    46: ("RED",         "SWITCH"),
    48: ("RED",         "OTRO"),
    50: ("RED",         "UPS"),
    51: ("RED",         "ESTABILIZADOR"),
    11: ("RED",         "ESTABILIZADOR"),
    8:  ("RED",         "OTRO"),
    17: ("PERIFERICO",  "OTRO"),
    19: ("PERIFERICO",  "MOUSE"),
    18: ("PERIFERICO",  "TECLADO"),
    22: ("PERIFERICO",  "LECTORA_QR"),
    29: ("PERIFERICO",  "BIOMETRICO"),
    49: ("PERIFERICO",  "TABLET"),
    24: ("PERIFERICO",  "OTRO"),
    25: ("PERIFERICO",  "OTRO"),
    20: ("PERIFERICO",  "OTRO"),
    21: ("PERIFERICO",  "OTRO"),
    12: ("PERIFERICO",  "OTRO"),
    41: ("IMPRESORA",   "PLOTTER"),
    42: ("IMPRESORA",   "TERMICA"),
    43: ("IMPRESORA",   "MULTIFUNCION"),
}

# SistemaOperativo
so_map = {}
for _r in tables.get("sistema_operativo", []):
    _nom = s(_r["nombre"])
    if _nom:
        _obj, _ = SistemaOperativo.objects.get_or_create(nombre=_nom)
        so_map[i(_r["id"])] = _obj
print(f"SistemaOperativo: {len(so_map)}")

# Procesador
proc_map = {}
for _r in tables.get("procesador", []):
    _nom = s(_r["nombre"])
    if _nom:
        _obj, _ = Procesador.objects.get_or_create(nombre=_nom)
        proc_map[i(_r["id"])] = _obj
print(f"Procesador      : {len(proc_map)}")

# MemoriaRam
ram_map = {}
for _r in tables.get("memoria_ram", []):
    _cap = s(_r["nombre"])
    if _cap:
        _obj, _ = MemoriaRam.objects.get_or_create(capacidad=_cap)
        ram_map[i(_r["id"])] = _obj
print(f"MemoriaRam      : {len(ram_map)}")

# Consumible (indexado por nombre lower y por id-string)
cons_by_name = {}
cons_by_id   = {}
for _r in tables.get("consumibles", []):
    _nom = s(_r["nombre"])
    if _nom:
        _obj, _ = Consumible.objects.get_or_create(nombre=_nom)
        cons_by_name[_nom.lower()] = _obj
        cons_by_id[str(_r["id"])]  = _obj
print(f"Consumible      : {len(cons_by_name)}")

# Marca (cache dinámico)
_marca_cache = {}
def get_marca(nombre):
    _n = s(nombre)
    if not _n or _n in ("-", "S/N"):
        return None
    _key = _n.upper()
    if _key not in _marca_cache:
        _obj, _ = Marca.objects.get_or_create(nombre=_n)
        _marca_cache[_key] = _obj
    return _marca_cache[_key]

print()

# ── 2. Organización ───────────────────────────────────────────────────────────
from apps.organizacion.models import Sede, UnidadOrganica, Subgerencia, Dependencia

# Sede
sede_map = {}
for _r in tables.get("sede", []):
    _id = i(_r["id"])
    _obj, _ = Sede.objects.get_or_create(
        sed_ide_siggo=_id,
        defaults={"nombre": s(_r["nombre"])},
    )
    sede_map[_id] = _obj
print(f"Sedes           : {len(sede_map)}")

# Sede por nombre (para camaras que solo traen nombre de sede)
_sede_by_nombre = {_s.nombre.lower(): _s for _s in sede_map.values()}
def get_sede_by_nombre(nombre):
    _n = s(nombre).lower()
    for _k, _v in _sede_by_nombre.items():
        if _k in _n or _n in _k:
            return _v
    return None

# UnidadOrganica ← area (nivel más detallado)
area_map = {}
for _r in tables.get("area", []):
    _id = i(_r["id"])
    _obj, _ = UnidadOrganica.objects.get_or_create(
        uni_ide_siggo=_id,
        defaults={"nombre": s(_r["nombre"]), "nivel": 3},
    )
    area_map[_id] = _obj
print(f"Áreas (UO)      : {len(area_map)}")

# Raíz organizacional para anclar Subgerencia/Dependencia
_root_uni, _ = UnidadOrganica.objects.get_or_create(
    uni_ide_siggo=-9999,
    defaults={"nombre": "MUNICIPALIDAD", "nivel": 0},
)

# Subgerencia ← subgerencia JSON
subger_map = {}
for _r in tables.get("subgerencia", []):
    _id  = i(_r["id"])
    _nom = s(_r["nombre"])
    _obj, _ = Subgerencia.objects.get_or_create(
        nombre=_nom,
        defaults={"unidad_organica": _root_uni},
    )
    subger_map[_id] = _obj
print(f"Subgerencias    : {len(subger_map)}")

# Raíz Subgerencia para anclar Dependencia
_root_subger, _ = Subgerencia.objects.get_or_create(
    nombre="MUNICIPAL",
    defaults={"unidad_organica": _root_uni},
)

# Dependencia ← dependencia JSON
depend_map = {}
for _r in tables.get("dependencia", []):
    _id  = i(_r["id"])
    _nom = s(_r["nombre"])
    _obj, _ = Dependencia.objects.get_or_create(
        nombre=_nom,
        defaults={"subgerencia": _root_subger},
    )
    depend_map[_id] = _obj
print(f"Dependencias    : {len(depend_map)}")
print()

# ── 3. Trabajadores → UserProfile ─────────────────────────────────────────────
from apps.users.models import UserProfile, RolSigtic

JEFE_ID = 322  # LLAMOCA REQUENA DAVID ROSENDO

worker_map = {}
for _r in tables.get("trabajadores", []):
    _uid   = i(_r["id"])
    _nom   = s(_r["nombre"])
    _dni   = s(_r["dni"])
    _cargo = s(_r.get("cargo", "")).upper()

    if _uid == JEFE_ID or "JEFE UNIDAD INFORMATICA" in _cargo:
        _rol = RolSigtic.JEFE_INFO
    elif "INFORMATICA" in _cargo or "SISTEMAS" in _cargo or "SOPORTE" in _cargo:
        _rol = RolSigtic.TECNICO
    else:
        _rol = RolSigtic.USUARIO

    _profile, _ = UserProfile.objects.get_or_create(
        usu_ide_siggo=_uid,
        defaults={
            "per_ide_siggo": _uid,
            "dni":            _dni,
            "nombre_completo": _nom,
            "email":          "",
            "rol":            _rol,
            "activo":         True,
        },
    )
    worker_map[_uid] = _profile

print(f"UserProfiles (trabajadores): {len(worker_map)}")
print()

# ── 4. Dispositivos ───────────────────────────────────────────────────────────
from apps.inventario.models import (
    Dispositivo, EstadoDispositivo,
    DispComputadora, DispImpresora, DispMonitor,
    DispPeriferico, DispRed, DispCamara, DispTelefono,
)

_d_created = 0
_d_skipped = 0

def make_disp(cod_inv, denom_id, row, estado=EstadoDispositivo.OPERATIVO):
    global _d_created, _d_skipped
    _cod = s(cod_inv)
    if not _cod or _cod.upper() in ("S/N", "-", ""):
        _d_skipped += 1
        return None

    _info = DENOM.get(denom_id)
    if _info is None:
        _d_skipped += 1
        return None

    _tipo_cod, _hint = _info
    _disp, _created = Dispositivo.objects.get_or_create(
        cod_inventario=_cod,
        defaults={
            "tipo_dispositivo": tipo_map[_tipo_cod],
            "marca":            get_marca(row.get("marca")),
            "modelo":           s(row.get("modelo", "")),
            "estado":           estado,
            "sede":             sede_map.get(i(row.get("sede_id"))),
            "unidad_organica":  area_map.get(i(row.get("area_id"))),
            "subgerencia":      subger_map.get(i(row.get("subgerencia_id"))),
            "dependencia":      depend_map.get(i(row.get("dependencia_id"))),
            "responsable":      worker_map.get(i(row.get("responsable_id"))),
            "dni_responsable":  s(row.get("dni", "")),
            "proveedor":        s(row.get("proveedor", "")),
            "orden_compra":     s(row.get("orden_compra", "")),
            "observacion":      s(row.get("observacion", "")),
            "activo":           True,
        },
    )
    if _created:
        _d_created += 1
    return _disp, _hint

def estado_from_func(funcionamiento):
    return EstadoDispositivo.EN_MANTENIMIENTO if s(funcionamiento) == "0" else EstadoDispositivo.OPERATIVO

# ── 4a. tbl_cpu → COMPUTADORA / LAPTOP / SERVIDOR / RED(servidor) ─────────────
print("Cargando tbl_cpu ...")
for _r in tables.get("tbl_cpu", []):
    _denom = i(_r.get("denominacion_id"))
    _res = make_disp(s(_r.get("cod_inv_cpu", "")), _denom, _r)
    if _res is None:
        continue
    _disp, _hint = _res

    _tipo_pc = {"LAPTOP": "LAPTOP", "SERVIDOR": "SERVIDOR"}.get(_hint, "DESKTOP")
    DispComputadora.objects.get_or_create(
        dispositivo=_disp,
        defaults={
            "sistema_operativo": so_map.get(i(_r.get("sistema_operativo_id"))),
            "procesador":        proc_map.get(i(_r.get("procesador_id"))),
            "memoria_ram":       ram_map.get(i(_r.get("memoria_ram_id"))),
            "ip":                ip_val(_r.get("ip")),
            "mac":               mac_val(_r.get("mac")),
            "nombre_equipo":     s(_r.get("nombre_equipo", "")),
            "dominio":           s(_r.get("dominio", "")),
            "tipo_pc":           _tipo_pc,
            "cod_monitor":       s(_r.get("cod_inv_monitor", "")),
            "cod_teclado":       s(_r.get("cod_inv_teclado", "")),
            "licencia_office":   bool_si(_r.get("licencia_office", "NO")),
            "licencia_windows":  bool_si(_r.get("licencia_windows", "NO")),
            "antivirus":         _r.get("antivirus", "0") == "1",
        },
    )
print(f"  CPU: {_d_created} creados, {_d_skipped} omitidos")
_cpu_ok = _d_created; _d_created = 0; _d_skipped = 0

# ── 4b. tbl_equipos → RED / PERIFERICO / MONITOR / IMPRESORA ─────────────────
_RED_HINTS    = {"SWITCH", "ROUTER", "DVR", "UPS", "ESTABILIZADOR", "SERVIDOR", "OTRO"}
_PERI_HINTS   = {"MOUSE", "TECLADO", "BIOMETRICO", "TABLET", "LECTORA_QR", "OTRO"}

print("Cargando tbl_equipos ...")
for _r in tables.get("tbl_equipos", []):
    _denom = i(_r.get("denominacion_id"))
    _est   = estado_from_func(_r.get("funcionamiento", "1"))
    _res   = make_disp(s(_r.get("cod_inv_equipo", "")), _denom, _r, _est)
    if _res is None:
        continue
    _disp, _hint = _res
    _tipo_cod = DENOM.get(_denom, ("", ""))[0]

    if _tipo_cod == "RED":
        DispRed.objects.get_or_create(
            dispositivo=_disp,
            defaults={"subtipo": _hint if _hint in _RED_HINTS else "SWITCH"},
        )
    elif _tipo_cod == "PERIFERICO":
        DispPeriferico.objects.get_or_create(
            dispositivo=_disp,
            defaults={"subtipo": _hint if _hint in _PERI_HINTS else "OTRO"},
        )
    elif _tipo_cod == "MONITOR":
        DispMonitor.objects.get_or_create(dispositivo=_disp)
    elif _tipo_cod == "IMPRESORA":
        _tip = {"PLOTTER": "PLOTTER", "TERMICA": "TERMICA", "MULTIFUNCION": "MULTIFUNCION"}.get(_hint, "LASER")
        DispImpresora.objects.get_or_create(dispositivo=_disp, defaults={"tipo": _tip})

print(f"  Equipos: {_d_created} creados, {_d_skipped} omitidos")
_d_created = 0; _d_skipped = 0

# tipo_impre_id → tipo impresora Django
_TIPO_IMPRE = {1: "LASER", 2: "MULTIFUNCION", 3: "MULTIFUNCION", 4: "PLOTTER"}

# ── 4c. tbl_impresoras → IMPRESORA ───────────────────────────────────────────
print("Cargando tbl_impresoras ...")
for _r in tables.get("tbl_impresoras", []):
    _denom = i(_r.get("denominacion_id")) or 27
    _res   = make_disp(s(_r.get("cod_inv_impresora", "")), _denom, _r)
    if _res is None:
        continue
    _disp, _ = _res
    _tip = _TIPO_IMPRE.get(i(_r.get("tipo_impre_id")), "LASER")
    _cons = cons_by_id.get(str(_r.get("consumible_id", "")))
    DispImpresora.objects.get_or_create(
        dispositivo=_disp,
        defaults={
            "tipo":       _tip,
            "ip":         ip_val(_r.get("ip")),
            "consumible": _cons,
        },
    )
print(f"  Impresoras: {_d_created} creadas, {_d_skipped} omitidas")
_d_created = 0; _d_skipped = 0

# ── 4d. tbl_telefonos → TELEFONO ─────────────────────────────────────────────
print("Cargando tbl_telefonos ...")
for _r in tables.get("tbl_telefonos", []):
    _denom = i(_r.get("denominacion_id")) or 28
    _est   = estado_from_func(_r.get("funcionamiento", "1"))
    _res   = make_disp(s(_r.get("cod_inv_telefono", "")), _denom, _r, _est)
    if _res is None:
        continue
    _disp, _ = _res
    DispTelefono.objects.get_or_create(
        dispositivo=_disp,
        defaults={
            "extension": s(_r.get("anexo", "")),
            "ip":        ip_val(_r.get("ip")),
        },
    )
print(f"  Teléfonos: {_d_created} creados, {_d_skipped} omitidos")
_d_created = 0; _d_skipped = 0

# ── 4e. camaras → CAMARA ─────────────────────────────────────────────────────
_CAM_TIPO = {"domo": "DOMO", "bullet": "BULLET", "ptz": "PTZ"}

print("Cargando camaras ...")
for _r in tables.get("camaras", []):
    _cod = s(_r.get("cod_inv", ""))
    if not _cod or _cod == "-":
        _cod = f"CAM-{_r['id']}"

    _est = EstadoDispositivo.OPERATIVO if s(_r.get("estado", "")) == "activa" else EstadoDispositivo.EN_MANTENIMIENTO
    _sede_c = get_sede_by_nombre(_r.get("sede", ""))

    _disp, _created_c = Dispositivo.objects.get_or_create(
        cod_inventario=_cod,
        defaults={
            "tipo_dispositivo": tipo_map["CAMARA"],
            "marca":            get_marca(_r.get("marca")),
            "modelo":           s(_r.get("modelo", "")),
            "estado":           _est,
            "sede":             _sede_c,
            "responsable":      worker_map.get(JEFE_ID),
            "observacion":      s(_r.get("observaciones", "")),
            "activo":           True,
        },
    )
    if _created_c:
        _d_created += 1

    _tipo_cam = _CAM_TIPO.get(s(_r.get("tipo", "")).lower(), "DOMO")
    DispCamara.objects.get_or_create(
        dispositivo=_disp,
        defaults={
            "tipo_camara":   _tipo_cam,
            "ip":            ip_val(_r.get("ip")),
            "usuario_acceso": s(_r.get("usuario", "")),
            "clave_acceso":  s(_r.get("clave", "")),
        },
    )
print(f"  Cámaras: {_d_created} creadas")
print()

# ── 5. Almacén → StockConsumible ─────────────────────────────────────────────
from apps.almacen.models import StockConsumible

_stk_ok = 0
for _r in tables.get("tbl_almacen", []):
    _nom = s(_r.get("consumible", ""))
    _stk = i(_r.get("stock")) or 0
    _obs = s(_r.get("observaciones", ""))

    # Obtener o crear consumible
    _cons = cons_by_name.get(_nom.lower())
    if not _cons:
        _cons, _ = Consumible.objects.get_or_create(nombre=_nom)
        cons_by_name[_nom.lower()] = _cons

    _marca = get_marca(_r.get("marca"))

    _stock, _created = StockConsumible.objects.get_or_create(
        consumible=_cons,
        marca=_marca,
        defaults={"stock_actual": _stk, "stock_minimo": 3, "observaciones": _obs},
    )
    if not _created:
        # Sincronizar stock con el JSON (fuente de verdad)
        _stock.stock_actual = _stk
        if _obs:
            _stock.observaciones = _obs
        _stock.save(update_fields=["stock_actual", "observaciones"])
    else:
        _stk_ok += 1

print(f"StockConsumible : {_stk_ok} creados, {StockConsumible.objects.count()} total")

# ── 6. Bienes de baja ─────────────────────────────────────────────────────────
from apps.inventario.models import BienBaja

_jefe = worker_map.get(JEFE_ID)
_baja_ok = 0

if _jefe:
    for _r in tables.get("tbl_bienes_baja", []):
        _cod    = s(_r.get("cod_inv", ""))
        _motivo = s(_r.get("motivo", "")) or "Sin motivo especificado."
        _obs    = s(_r.get("observacion", ""))
        _lugar  = s(_r.get("lugar_origen", ""))
        try:
            _fecha = datetime.date.fromisoformat(s(_r.get("fecha", "")))
        except ValueError:
            _fecha = datetime.date.today()

        _disp_baja = Dispositivo.objects.filter(cod_inventario=_cod).first() if _cod else None
        _sin_reg   = _disp_baja is None

        # Evitar duplicados por cod_inv
        if _cod and BienBaja.objects.filter(sr_cod_inventario=_cod).exists():
            continue
        if _disp_baja and BienBaja.objects.filter(dispositivo=_disp_baja).exists():
            continue

        BienBaja.objects.create(
            dispositivo=_disp_baja,
            sin_registro=_sin_reg,
            sr_cod_inventario=_cod if _sin_reg else "",
            sr_descripcion=s(_r.get("denominacion", "")) if _sin_reg else "",
            sr_marca=s(_r.get("marca", "")) if _sin_reg else "",
            sr_modelo=s(_r.get("modelo", "")) if _sin_reg else "",
            sr_serie=s(_r.get("serie", "")) if _sin_reg else "",
            motivo=_motivo,
            estado="APROBADO",
            lugar_origen=_lugar,
            observacion=_obs,
            registrado_por=_jefe,
        )
        _baja_ok += 1

print(f"Bienes de baja  : {_baja_ok} creados")
print()

# ── 7. Usuarios demo ──────────────────────────────────────────────────────────
from django.contrib.auth import get_user_model
User = get_user_model()

# sede principal (Palacio Municipal, sed_ide_siggo=1)
_sede_demo = sede_map.get(1) or (list(sede_map.values())[0] if sede_map else None)

_demo_users = [
    # (username,         password,        nombre_completo,                  dni,       rol)
    ("jefe_info",      "Jefe123!",      "LLAMOCA REQUENA DAVID ROSENDO",  "29491643", RolSigtic.JEFE_INFO),
    ("encargado_demo", "Encargado123!", "ENCARGADO DEMO SIGTIC",           "00000003", RolSigtic.ENCARGADO_INFO),
    ("tecnico_demo",   "Tecnico123!",   "TECNICO DEMO SIGTIC",            "00000001", RolSigtic.TECNICO),
    ("tecnico2",       "Tecnico2!",     "GARCIA QUISPE JOSE LUIS",        "00000004", RolSigtic.TECNICO),
    ("tecnico3",       "Tecnico3!",     "MAMANI FLORES CARLOS ALBERTO",   "00000005", RolSigtic.TECNICO),
    ("usuario_demo",   "Usuario123!",   "USUARIO DEMO SIGTIC",            "00000002", RolSigtic.USUARIO),
]

print("Usuarios demo:")
for _uname, _pwd, _nombre, _dni, _rol in _demo_users:
    # Django User (superuser para que LoginView cree/encuentre el perfil)
    _user, _created = User.objects.get_or_create(
        username=_uname,
        defaults={
            "first_name": _nombre[:150],
            "is_active":     True,
            "is_staff":      True,
            "is_superuser":  True,
        },
    )
    _user.set_password(_pwd)
    _user.save()

    # UserProfile pre-creado con usu_ide_siggo negativo (= -user.pk)
    # LoginView lo encontrará con get_or_create y NO sobreescribirá el rol
    _profile, _pcreated = UserProfile.objects.get_or_create(
        usu_ide_siggo=-(_user.pk),
        defaults={
            "per_ide_siggo":  0,
            "dni":             _dni,
            "nombre_completo": _nombre,
            "email":           f"{_uname}@sigtic.local",
            "rol":             _rol,
            "activo":          True,
            "sede":            _sede_demo,
        },
    )
    # Si ya existía con otro rol, corregirlo
    if _profile.rol != _rol:
        UserProfile.objects.filter(pk=_profile.pk).update(rol=_rol, nombre_completo=_nombre)

    _tag = "nuevo" if _created else "existente"
    print(f"  {_uname:<15} [{_tag}]  rol: {_rol:<12}  pass: {_pwd}")

# ── Resumen ───────────────────────────────────────────────────────────────────
from apps.inventario.models import DispComputadora, DispImpresora, DispTelefono, DispCamara

print()
print("=" * 55)
print("MIGRACIÓN COMPLETADA")
print("=" * 55)
print(f"Sedes                : {Sede.objects.count()}")
print(f"Unidades orgánicas   : {UnidadOrganica.objects.count()}")
print(f"Subgerencias         : {Subgerencia.objects.count()}")
print(f"Dependencias         : {Dependencia.objects.count()}")
print(f"UserProfiles total   : {UserProfile.objects.count()}")
print(f"  JEFE_INFO          : {UserProfile.objects.filter(rol='JEFE_INFO').count()}")
print(f"  TECNICO            : {UserProfile.objects.filter(rol='TECNICO').count()}")
print(f"  USUARIO            : {UserProfile.objects.filter(rol='USUARIO').count()}")
print(f"Dispositivos total   : {Dispositivo.objects.count()}")
print(f"  Computadoras       : {DispComputadora.objects.count()}")
print(f"  Impresoras         : {DispImpresora.objects.count()}")
print(f"  Teléfonos          : {DispTelefono.objects.count()}")
print(f"  Cámaras            : {DispCamara.objects.count()}")
print(f"Stock consumibles    : {StockConsumible.objects.count()}")
print(f"Bienes de baja       : {BienBaja.objects.count()}")
print()
print("CREDENCIALES DEMO:")
print(f"  {'USUARIO':<15} {'CONTRASEÑA':<14} ROL")
print(f"  {'-'*15} {'-'*13} {'-'*20}")
for _u, _p, _, _, _r in _demo_users:
    print(f"  {_u:<15} {_p:<14} {_r}")
print()
