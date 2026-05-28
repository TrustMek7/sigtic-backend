from django.db import models
from django.utils import timezone


class EstadoTicket(models.TextChoices):
    ENVIADO = "ENVIADO", "Enviado"
    EN_REVISION = "EN_REVISION", "En Revisión"
    ASIGNADO = "ASIGNADO", "Asignado"
    EN_ATENCION = "EN_ATENCION", "En Atención"
    SOLUCIONADO = "SOLUCIONADO", "Solucionado"
    EN_MANTENIMIENTO = "EN_MANTENIMIENTO", "En Mantenimiento"
    TERCERIZADO = "TERCERIZADO", "Tercerizado"
    FINALIZADO = "FINALIZADO", "Finalizado"
    RECHAZADO = "RECHAZADO", "Rechazado"


ESTADOS_TERMINALES = {
    EstadoTicket.SOLUCIONADO,
    EstadoTicket.FINALIZADO,
    EstadoTicket.RECHAZADO,
}

# Transiciones válidas por rol
# (estado_origen, estado_destino): roles_permitidos
TRANSICIONES = {
    (EstadoTicket.ENVIADO, EstadoTicket.EN_REVISION): {"JEFE_INFO", "ENCARGADO_INFO", "ADMIN"},
    (EstadoTicket.EN_REVISION, EstadoTicket.ASIGNADO): {"JEFE_INFO", "ENCARGADO_INFO", "ADMIN"},
    (EstadoTicket.ASIGNADO, EstadoTicket.EN_ATENCION): {"TECNICO"},
    (EstadoTicket.EN_ATENCION, EstadoTicket.SOLUCIONADO): {"TECNICO"},
    (EstadoTicket.EN_ATENCION, EstadoTicket.EN_MANTENIMIENTO): {"TECNICO"},
    (EstadoTicket.EN_ATENCION, EstadoTicket.TERCERIZADO): {"TECNICO"},
    (EstadoTicket.EN_MANTENIMIENTO, EstadoTicket.FINALIZADO): {"TECNICO"},
    (EstadoTicket.TERCERIZADO, EstadoTicket.FINALIZADO): {"JEFE_INFO", "ENCARGADO_INFO", "ADMIN"},
    # Rechazo desde estados no terminales (excepto EN_ATENCION en adelante para USUARIO)
    (EstadoTicket.ENVIADO, EstadoTicket.RECHAZADO): {"JEFE_INFO", "ENCARGADO_INFO", "ADMIN", "USUARIO"},
    (EstadoTicket.EN_REVISION, EstadoTicket.RECHAZADO): {"JEFE_INFO", "ENCARGADO_INFO", "ADMIN", "USUARIO"},
    (EstadoTicket.ASIGNADO, EstadoTicket.RECHAZADO): {"JEFE_INFO", "ENCARGADO_INFO", "ADMIN"},
    (EstadoTicket.EN_ATENCION, EstadoTicket.RECHAZADO): {"JEFE_INFO", "ENCARGADO_INFO", "ADMIN"},
}


class Ticket(models.Model):
    numero = models.CharField(max_length=20, unique=True, db_index=True, editable=False)
    dispositivo = models.ForeignKey(
        "inventario.Dispositivo", on_delete=models.PROTECT, related_name="tickets"
    )
    solicitante = models.ForeignKey(
        "users.UserProfile", on_delete=models.PROTECT, related_name="tickets_creados"
    )
    asignado_por = models.ForeignKey(
        "users.UserProfile", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="tickets_asignados",
    )
    tecnico = models.ForeignKey(
        "users.UserProfile", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="tickets_atendidos",
    )
    tipo_mantenimiento = models.CharField(
        max_length=15,
        choices=[("PREVENTIVO", "Preventivo"), ("CORRECTIVO", "Correctivo")],
        default="CORRECTIVO",
    )
    detalle_falla = models.TextField()
    estado = models.CharField(
        max_length=20,
        choices=EstadoTicket.choices,
        default=EstadoTicket.ENVIADO,
        db_index=True,
    )
    ip_solicitante = models.GenericIPAddressField(null=True, blank=True)

    # Snapshot del responsable al momento de crear el ticket
    responsable_snapshot = models.ForeignKey(
        "users.UserProfile", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="tickets_como_responsable_snapshot",
    )
    nombre_responsable_snapshot = models.CharField(max_length=300, blank=True)
    cargo_responsable_snapshot = models.CharField(max_length=300, blank=True)

    fecha_creacion = models.DateTimeField(default=timezone.now, db_index=True)
    fecha_asignacion = models.DateTimeField(null=True, blank=True)
    fecha_inicio = models.DateTimeField(null=True, blank=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    observaciones = models.TextField(blank=True)

    class Meta:
        ordering = ["-fecha_creacion"]
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"

    def __str__(self):
        return f"Ticket #{self.numero}"

    def save(self, *args, **kwargs):
        if not self.pk and not self.numero:
            self.numero = self._generar_numero()
        super().save(*args, **kwargs)

    @staticmethod
    def _generar_numero() -> str:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT nextval('tickets_ticket_numero_seq')")
            seq = cursor.fetchone()[0]
        return f"TKT-{seq:06d}"

    def puede_transicionar(self, nuevo_estado: str, rol: str) -> bool:
        if self.estado in ESTADOS_TERMINALES:
            return False
        clave = (self.estado, nuevo_estado)
        roles_permitidos = TRANSICIONES.get(clave, set())
        return rol in roles_permitidos


class TicketDiagnostico(models.Model):
    MENOR = "MENOR"
    MAYOR = "MAYOR"
    TERCERIZADO = "TERCERIZADO"

    RESULTADO_CHOICES = [
        (MENOR, "Menor — solución inmediata"),
        (MAYOR, "Mayor — requiere mantenimiento"),
        (TERCERIZADO, "Tercerizado — empresa externa"),
    ]

    ticket = models.OneToOneField(Ticket, on_delete=models.CASCADE, related_name="diagnostico")
    tipo_falla = models.CharField(max_length=200)
    detalle_tecnico = models.TextField()
    tipo_resultado = models.CharField(max_length=15, choices=RESULTADO_CHOICES)
    tiempo_estimado = models.CharField(max_length=100, blank=True)
    fecha_registro = models.DateTimeField(default=timezone.now)
    tecnico = models.ForeignKey(
        "users.UserProfile", on_delete=models.PROTECT, related_name="diagnosticos"
    )

    class Meta:
        verbose_name = "Diagnóstico"
        verbose_name_plural = "Diagnósticos"


class TicketAccion(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="acciones")
    tipo_accion = models.CharField(max_length=100)
    detalle = models.TextField()
    tecnico = models.ForeignKey(
        "users.UserProfile", on_delete=models.PROTECT, related_name="acciones_realizadas"
    )
    fecha_registro = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["fecha_registro"]
        verbose_name = "Acción de Ticket"
        verbose_name_plural = "Acciones de Ticket"


class TicketHistorial(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="historial")
    usuario = models.ForeignKey(
        "users.UserProfile", on_delete=models.PROTECT, related_name="historial_acciones"
    )
    estado_anterior = models.CharField(max_length=20, blank=True, null=True)
    estado_nuevo = models.CharField(max_length=20)
    comentario = models.TextField(blank=True)
    fecha = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["fecha"]
        verbose_name = "Historial de Ticket"
        verbose_name_plural = "Historial de Tickets"


class TicketAdjunto(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="adjuntos")
    archivo = models.FileField(upload_to="tickets/adjuntos/%Y/%m/")
    nombre_original = models.CharField(max_length=255)
    fecha = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["fecha"]
        verbose_name = "Adjunto de Ticket"
        verbose_name_plural = "Adjuntos de Ticket"


class TicketTercerizado(models.Model):
    ENVIADO = "ENVIADO"
    RECIBIDO = "RECIBIDO"
    REPARADO = "REPARADO"
    NO_REPARABLE = "NO_REPARABLE"

    ESTADO_CHOICES = [
        (ENVIADO, "Enviado a empresa"),
        (RECIBIDO, "Recibido por empresa"),
        (REPARADO, "Reparado"),
        (NO_REPARABLE, "No reparable"),
    ]

    ticket = models.OneToOneField(Ticket, on_delete=models.CASCADE, related_name="tercerizado")
    empresa = models.CharField(max_length=200)
    contacto = models.CharField(max_length=200, blank=True)
    fecha_entrega_est = models.DateField(null=True, blank=True)
    presupuesto = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    estado_tercerizado = models.CharField(
        max_length=15, choices=ESTADO_CHOICES, default=ENVIADO
    )
    observacion = models.TextField(blank=True)
    registrado_por = models.ForeignKey(
        "users.UserProfile", on_delete=models.PROTECT, related_name="tercerizados_registrados"
    )

    class Meta:
        verbose_name = "Ticket Tercerizado"
        verbose_name_plural = "Tickets Tercerizados"
