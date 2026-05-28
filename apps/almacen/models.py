from django.db import models
from django.utils import timezone


class StockConsumible(models.Model):
    consumible = models.ForeignKey(
        "catalogo.Consumible", on_delete=models.PROTECT, related_name="stocks"
    )
    marca = models.ForeignKey(
        "catalogo.Marca", null=True, blank=True, on_delete=models.SET_NULL
    )
    stock_actual = models.IntegerField(default=0)
    stock_minimo = models.IntegerField(default=0)
    orden_compra = models.CharField(max_length=100, blank=True)
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    fecha_actualizacion = models.DateField(auto_now=True)
    observaciones = models.TextField(blank=True)

    class Meta:
        ordering = ["consumible__nombre"]
        verbose_name = "Stock de Consumible"
        verbose_name_plural = "Stocks de Consumibles"
        unique_together = [["consumible", "marca"]]

    def __str__(self):
        marca = self.marca.nombre if self.marca_id else "Sin marca"
        return f"{self.consumible} — {marca} (stock: {self.stock_actual})"

    @property
    def bajo_minimo(self):
        return self.stock_actual < self.stock_minimo


class MovimientoStock(models.Model):
    INGRESO = "INGRESO"
    SALIDA = "SALIDA"
    TIPO_CHOICES = [(INGRESO, "Ingreso"), (SALIDA, "Salida")]

    stock_consumible = models.ForeignKey(
        StockConsumible, on_delete=models.PROTECT, related_name="movimientos"
    )
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, db_index=True)
    cantidad = models.PositiveIntegerField()
    dispositivo = models.ForeignKey(
        "inventario.Dispositivo", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="movimientos_consumible",
    )
    ticket = models.ForeignKey(
        "tickets.Ticket", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="movimientos_stock",
    )
    registrado_por = models.ForeignKey(
        "users.UserProfile", on_delete=models.PROTECT, related_name="movimientos_registrados"
    )
    fecha = models.DateTimeField(default=timezone.now)
    referencia = models.CharField(max_length=200, blank=True)
    observacion = models.TextField(blank=True)

    class Meta:
        ordering = ["-fecha"]
        verbose_name = "Movimiento de Stock"
        verbose_name_plural = "Movimientos de Stock"

    def __str__(self):
        return f"{self.get_tipo_display()} {self.cantidad}x {self.stock_consumible.consumible}"

    def save(self, *args, **kwargs):
        if not self.pk:
            # Actualizar stock al crear
            stock = self.stock_consumible
            if self.tipo == self.INGRESO:
                stock.stock_actual += self.cantidad
            else:
                stock.stock_actual -= self.cantidad
            stock.save(update_fields=["stock_actual", "fecha_actualizacion"])
        super().save(*args, **kwargs)
