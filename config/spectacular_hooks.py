"""
Hooks de postprocesamiento para drf-spectacular.
Asigna tags por prefijo de URL y define el orden de secciones en Swagger.
"""

_PATH_TAG_MAP = [
    ("/api/v1/auth/login",       "Autenticación"),
    ("/api/v1/auth/logout",      "Autenticación"),
    ("/api/v1/auth/refresh",     "Autenticación"),
    ("/api/v1/auth/me",          "Autenticación"),
    ("/api/v1/auth/users",       "Usuarios"),
    ("/api/v1/auth/encargados",  "Usuarios"),
    ("/api/v1/tickets",          "Tickets"),
    ("/api/v1/inventario/dispositivos", "Inventario"),
    ("/api/v1/inventario/bajas", "Bajas"),
    ("/api/v1/almacen",          "Almacén"),
    ("/api/v1/catalogo",         "Catálogo"),
    ("/api/v1/organizacion",     "Organización"),
    ("/api/v1/documentos",       "Documentos"),
]

_TAG_ORDER = [
    "Autenticación",
    "Tickets",
    "Inventario",
    "Bajas",
    "Almacén",
    "Usuarios",
    "Organización",
    "Catálogo",
    "Documentos",
]

_TAG_DESCRIPTIONS = {
    "Autenticación": "Login, logout y renovación de tokens JWT (httpOnly cookies).",
    "Tickets":       "Ciclo de vida completo de tickets: creación, transiciones de estado, diagnóstico y generación de documentos PDF.",
    "Inventario":    "Gestión de dispositivos (PCs, impresoras, monitores, redes, cámaras, teléfonos) con subtablas por tipo.",
    "Bajas":         "Registro de bienes retirados del inventario, con soporte para dispositivos sin código de inventario.",
    "Almacén":       "Stock de consumibles (tóner, tinta, papel, cintas) y movimientos de ingreso/salida.",
    "Usuarios":      "Perfiles de usuario, asignación de roles y gestión de encargados temporales.",
    "Organización":  "Catálogo de sedes, unidades orgánicas, subgerencias y dependencias.",
    "Catálogo":      "Tablas maestras: marcas, tipos de dispositivo, sistemas operativos, procesadores, RAM, consumibles.",
    "Documentos":    "Descarga de documentos PDF oficiales generados a partir de tickets.",
}


def assign_tags_by_path(result, generator, **kwargs):
    """
    Postprocessing hook: asigna tags a cada operación según el prefijo de su path.
    Reemplaza cualquier tag inferido por drf-spectacular con el tag correcto.
    """
    paths = result.get("paths", {})
    for path, path_item in paths.items():
        tag = _resolve_tag(path)
        if not tag:
            continue
        for method_data in path_item.values():
            if isinstance(method_data, dict):
                method_data["tags"] = [tag]

    # Definir tags con descripción en el orden deseado
    result["tags"] = [
        {"name": name, "description": _TAG_DESCRIPTIONS.get(name, "")}
        for name in _TAG_ORDER
    ]
    return result


def _resolve_tag(path: str) -> str:
    for prefix, tag in _PATH_TAG_MAP:
        if path.startswith(prefix):
            return tag
    return ""
