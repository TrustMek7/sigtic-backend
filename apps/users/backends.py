"""
Backend de autenticación que valida credenciales contra bdsiggo (sogem.usuario).
Al autenticarse con éxito, crea/actualiza UserProfile en sigtic_db y sincroniza
los cargos del usuario desde siggo.cargo.

Compatibilidad: bdsiggo corre en PostgreSQL ~8.x — solo SQL básico.
"""
import hashlib
from django.conf import settings
from django.contrib.auth import get_user_model
from apps.siggo_readonly.models import SogemUsuario, SogemPersona

User = get_user_model()


def _check_password(raw_password: str, stored_hash: str) -> bool:
    algo = getattr(settings, "SIGGO_PASSWORD_ALGO", "md5").lower()
    if algo == "md5":
        return hashlib.md5(raw_password.encode()).hexdigest() == stored_hash.strip()
    if algo == "sha1":
        return hashlib.sha1(raw_password.encode()).hexdigest() == stored_hash.strip()
    if algo == "bcrypt":
        try:
            import bcrypt
            return bcrypt.checkpw(raw_password.encode(), stored_hash.encode())
        except ImportError:
            raise RuntimeError("Instala bcrypt: pip install bcrypt")
    raise ValueError(f"SIGGO_PASSWORD_ALGO desconocido: {algo}")


def _siggo_disponible() -> bool:
    """Verifica si la conexión a siggo está configurada."""
    from django.conf import settings
    host = settings.DATABASES.get("siggo", {}).get("HOST", "")
    return bool(host)


class SiggoAuthBackend:
    """
    1. Autentica contra sogem.usuario (bdsiggo).
    2. Obtiene datos de sogem.persona.
    3. Crea/actualiza User de Django + UserProfile en sigtic_db.
    4. Dispara sync de cargos en background (no bloquea el login).
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None

        if not _siggo_disponible():
            return None

        try:
            siggo_user = SogemUsuario.objects.using("siggo").get(
                usu_usu=username,
                usu_est=1,  # solo activos (integer en PG 8)
            )
        except SogemUsuario.DoesNotExist:
            return None

        if not _check_password(password, siggo_user.usu_pas):
            return None

        # Obtener persona para datos personales
        try:
            persona = SogemPersona.objects.using("siggo").get(
                per_ide=siggo_user.per_ide
            )
            nombre = persona.nombre_completo
            email = (persona.per_ema or "").strip()
            dni = (persona.per_doc or "").strip()
        except SogemPersona.DoesNotExist:
            nombre = siggo_user.usu_nom.strip()
            email = ""
            dni = ""

        # Crear o actualizar User de Django (requerido por SimpleJWT)
        user, _ = User.objects.update_or_create(
            username=username,
            defaults={
                "first_name": nombre[:150],
                "email": email,
                "is_active": True,
            },
        )

        # Crear o actualizar UserProfile
        _sync_profile(user, siggo_user, nombre, email, dni)

        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


def _sync_profile(user, siggo_user, nombre: str, email: str, dni: str):
    """Crea/actualiza UserProfile y sincroniza cargos."""
    from django.utils import timezone
    from apps.users.models import UserProfile
    from apps.users.sync import sync_cargos_from_siggo

    profile, created = UserProfile.objects.update_or_create(
        usu_ide_siggo=siggo_user.usu_ide,
        defaults={
            "per_ide_siggo": siggo_user.per_ide,
            "dni": dni,
            "nombre_completo": nombre,
            "email": email,
            "telefono": (siggo_user.telefono or "").strip(),
            "activo": True,
            "ultimo_sync_siggo": timezone.now(),
        },
    )

    # Sincronizar cargos (solo si siggo está disponible)
    try:
        sync_cargos_from_siggo(profile)
    except Exception:
        # No bloquear el login si la sync falla
        pass

    # Guardar referencia al profile en el User (acceso rápido en vistas)
    user._sigtic_profile = profile
