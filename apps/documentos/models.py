from django.db import models
from django.utils import timezone


class DocumentoOficial(models.Model):
    ticket = models.OneToOneField(
        "tickets.Ticket", on_delete=models.CASCADE, related_name="documento_oficial"
    )
    numero_documento = models.CharField(max_length=50, unique=True)
    archivo_pdf = models.FileField(upload_to="documentos/pdf/%Y/%m/")
    fecha_generacion = models.DateTimeField(default=timezone.now)
    generado_por = models.ForeignKey(
        "users.UserProfile", on_delete=models.PROTECT, related_name="documentos_generados"
    )

    class Meta:
        ordering = ["-fecha_generacion"]
        verbose_name = "Documento Oficial"
        verbose_name_plural = "Documentos Oficiales"

    def __str__(self):
        return f"Doc {self.numero_documento} — Ticket #{self.ticket.numero}"
