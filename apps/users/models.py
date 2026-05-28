from django.db import models


class RolSigtic(models.TextChoices):
    ADMIN = "ADMIN", "Administrador"
    JEFE_INFO = "JEFE_INFO", "Jefe de Informática"
    ENCARGADO_INFO = "ENCARGADO_INFO", "Encargado de Informática"
    TECNICO = "TECNICO", "Técnico"
    USUARIO = "USUARIO", "Usuario"


class UserProfile(models.Model):
    """
    Perfil local sincronizado desde bdsiggo.
    Se crea/actualiza en cada login exitoso contra siggo.
    Permite que el sistema funcione en modo degradado si siggo cae.
    """
    # Referencias a siggo (para resync)
    usu_ide_siggo = models.IntegerField(unique=True, db_index=True)
    per_ide_siggo = models.IntegerField(db_index=True)

    # Datos personales (caché de sogem.persona)
    dni = models.CharField(max_length=20, db_index=True)
    nombre_completo = models.CharField(max_length=300)
    email = models.CharField(max_length=250, blank=True)
    telefono = models.CharField(max_length=15, blank=True)

    # Rol operativo dentro de SIGTIC (asignado por ADMIN/JEFE)
    rol = models.CharField(
        max_length=20,
        choices=RolSigtic.choices,
        default=RolSigtic.USUARIO,
    )

    # Sede y cargo principal (para display y filtros)
    sede = models.ForeignKey(
        "organizacion.Sede",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="usuarios",
    )
    cargo_principal = models.ForeignKey(
        "users.UserCargo",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    activo = models.BooleanField(default=True)
    ultimo_sync_siggo = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nombre_completo"]
        verbose_name = "Perfil de usuario"
        verbose_name_plural = "Perfiles de usuario"

    def __str__(self):
        return f"{self.nombre_completo} [{self.get_rol_display()}]"

    @property
    def es_informatica(self):
        return self.rol in {
            RolSigtic.ADMIN,
            RolSigtic.JEFE_INFO,
            RolSigtic.ENCARGADO_INFO,
            RolSigtic.TECNICO,
        }

    @property
    def puede_asignar_tickets(self):
        """True si el perfil tiene permisos de asignación ahora mismo."""
        if self.rol == RolSigtic.JEFE_INFO and self.activo:
            return True
        if self.rol == RolSigtic.ENCARGADO_INFO and self.activo:
            return self.encargados_activos.filter(activo=True).exists()
        return False


class UserCargo(models.Model):
    """
    Cargos de un usuario en siggo (puede tener varios).
    Snapshot sincronizado desde siggo.cargo WHERE per_ide = X AND est_ado = 1.
    """
    user_profile = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="cargos",
    )

    # Referencias originales de siggo
    car_ide_siggo = models.IntegerField(db_index=True)
    uni_ide_siggo = models.IntegerField()

    # Datos desnormalizados del cargo
    uni_nombre_siggo = models.CharField(max_length=300)
    cargo_descripcion = models.CharField(max_length=300, blank=True)

    # car_pri del siggo original (>0 = principal en siggo)
    car_pri_siggo = models.IntegerField(default=0)

    # Cuál es el cargo principal mostrado en SIGTIC (seteado en sync)
    es_principal = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["-es_principal", "-car_pri_siggo"]
        verbose_name = "Cargo de usuario"
        verbose_name_plural = "Cargos de usuario"

    def __str__(self):
        return f"{self.cargo_descripcion} — {self.uni_nombre_siggo}"


class EncargadoActivo(models.Model):
    """
    Registro de quién está a cargo de la asignación de tickets
    cuando el Jefe de Informática no está disponible.
    Solo puede haber uno activo a la vez (activo=True).
    """
    encargado = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="encargados_activos",
    )
    autorizado_por = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="encargados_autorizados",
    )
    desde = models.DateTimeField()
    hasta = models.DateTimeField(null=True, blank=True)
    motivo = models.TextField(blank=True)
    activo = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["-desde"]
        verbose_name = "Encargado activo"
        verbose_name_plural = "Encargados activos"

    def __str__(self):
        estado = "activo" if self.activo else "inactivo"
        return f"{self.encargado.nombre_completo} ({estado})"

    @classmethod
    def get_activo(cls):
        return cls.objects.filter(activo=True).select_related("encargado").first()
