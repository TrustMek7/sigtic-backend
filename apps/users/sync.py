"""
Sincronización de cargos desde siggo.cargo hacia UserCargo en sigtic_db.
Solo SQL básico compatible con PostgreSQL 8.x.
"""
from apps.siggo_readonly.models import SiggoCargo, SiggoUnidadOrganica


def sync_cargos_from_siggo(profile) -> None:
    """
    Sincroniza los cargos activos del perfil desde siggo.cargo.
    Llama a esto al login; no bloquea si siggo no responde.
    """
    from apps.users.models import UserCargo

    # Cargos activos en siggo para esta persona
    cargos_siggo = list(
        SiggoCargo.objects.using("siggo").filter(
            per_ide=profile.per_ide_siggo,
            est_ado=1,
        )
    )

    if not cargos_siggo:
        return

    # Obtener nombres de unidades orgánicas en un solo query
    uni_ids = [c.uni_ide for c in cargos_siggo if c.uni_ide]
    uni_map = {
        u.uni_ide: u.uni_nom
        for u in SiggoUnidadOrganica.objects.using("siggo").filter(
            uni_ide__in=uni_ids
        )
    }

    # Marcar todos los cargos existentes como inactivos antes de sync
    UserCargo.objects.filter(user_profile=profile).update(activo=False)

    # Determinar cuál es el cargo principal (el de mayor car_pri)
    car_pri_max = max((c.car_pri or 0) for c in cargos_siggo)

    primer_principal = True
    for cargo in cargos_siggo:
        es_principal = (
            (cargo.car_pri or 0) == car_pri_max and primer_principal
        )
        if es_principal:
            primer_principal = False

        user_cargo, _ = UserCargo.objects.update_or_create(
            user_profile=profile,
            car_ide_siggo=cargo.car_ide,
            defaults={
                "uni_ide_siggo": cargo.uni_ide or 0,
                "uni_nombre_siggo": uni_map.get(cargo.uni_ide, ""),
                "cargo_descripcion": (cargo.car_des or "").strip(),
                "car_pri_siggo": cargo.car_pri or 0,
                "es_principal": es_principal,
                "activo": True,
            },
        )

    # Actualizar cargo_principal en el perfil
    principal = UserCargo.objects.filter(
        user_profile=profile, es_principal=True, activo=True
    ).first()
    if principal:
        UserProfile = profile.__class__
        UserProfile.objects.filter(pk=profile.pk).update(
            cargo_principal=principal
        )
