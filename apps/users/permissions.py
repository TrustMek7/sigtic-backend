"""
Permisos de la aplicación basados en el rol del UserProfile.
"""
from rest_framework.permissions import BasePermission
from apps.users.models import RolSigtic, EncargadoActivo


def _get_profile(request):
    """Retorna el UserProfile del usuario autenticado o None."""
    if not request.user or not request.user.is_authenticated:
        return None

    # Cacheado por SiggoAuthBackend en la misma request de login
    cached = getattr(request.user, "_sigtic_profile", None)
    if cached:
        return cached

    # Superuser Django sin bdsiggo: perfil creado con ID negativo en LoginView
    if request.user.is_superuser:
        from apps.users.models import UserProfile
        return UserProfile.objects.filter(usu_ide_siggo=-(request.user.pk)).first()

    return None


class EsInformatica(BasePermission):
    """Permite acceso solo a usuarios del área de informática."""
    message = "Solo el personal de informática puede acceder."

    def has_permission(self, request, view):
        profile = _get_profile(request)
        return profile is not None and profile.es_informatica and profile.activo


class EsJefeOEncargado(BasePermission):
    """
    Permite acceso al Jefe de Informática, o al Encargado cuando
    encargado_activo.activo=True.
    """
    message = "Solo el jefe o encargado activo puede realizar esta acción."

    def has_permission(self, request, view):
        profile = _get_profile(request)
        if not profile or not profile.activo:
            return False
        if profile.rol == RolSigtic.JEFE_INFO:
            return True
        if profile.rol == RolSigtic.ENCARGADO_INFO:
            enc = EncargadoActivo.get_activo()
            return enc is not None and enc.encargado_id == profile.pk
        if profile.rol == RolSigtic.ADMIN:
            return True
        return False


class EsAdmin(BasePermission):
    message = "Solo administradores pueden realizar esta acción."

    def has_permission(self, request, view):
        profile = _get_profile(request)
        return profile is not None and profile.rol == RolSigtic.ADMIN and profile.activo


class EsJefe(BasePermission):
    message = "Solo el jefe de informática puede realizar esta acción."

    def has_permission(self, request, view):
        profile = _get_profile(request)
        return (
            profile is not None
            and profile.rol in {RolSigtic.JEFE_INFO, RolSigtic.ADMIN}
            and profile.activo
        )
