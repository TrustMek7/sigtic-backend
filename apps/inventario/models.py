from django.db import models


class EstadoDispositivo(models.TextChoices):
    OPERATIVO = "OPERATIVO", "Operativo"
    EN_MANTENIMIENTO = "EN_MANTENIMIENTO", "En Mantenimiento"
    DE_BAJA = "DE_BAJA", "De Baja"
    ALMACEN = "ALMACEN", "Almacén"


class Dispositivo(models.Model):
    tipo_dispositivo = models.ForeignKey(
        "catalogo.TipoDispositivo", on_delete=models.PROTECT, related_name="dispositivos"
    )
    marca = models.ForeignKey(
        "catalogo.Marca", null=True, blank=True, on_delete=models.SET_NULL
    )
    modelo = models.CharField(max_length=150, blank=True)
    serie = models.CharField(max_length=150, blank=True, db_index=True)
    cod_inventario = models.CharField(max_length=100, unique=True, db_index=True)
    color = models.CharField(max_length=50, blank=True)
    estado = models.CharField(
        max_length=20,
        choices=EstadoDispositivo.choices,
        default=EstadoDispositivo.OPERATIVO,
        db_index=True,
    )
    sede = models.ForeignKey(
        "organizacion.Sede", null=True, blank=True, on_delete=models.SET_NULL
    )
    unidad_organica = models.ForeignKey(
        "organizacion.UnidadOrganica", null=True, blank=True, on_delete=models.SET_NULL
    )
    subgerencia = models.ForeignKey(
        "organizacion.Subgerencia", null=True, blank=True, on_delete=models.SET_NULL
    )
    dependencia = models.ForeignKey(
        "organizacion.Dependencia", null=True, blank=True, on_delete=models.SET_NULL
    )
    responsable = models.ForeignKey(
        "users.UserProfile", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="dispositivos_a_cargo",
    )
    dni_responsable = models.CharField(max_length=20, blank=True)
    proveedor = models.CharField(max_length=200, blank=True)
    orden_compra = models.CharField(max_length=100, blank=True)
    observacion = models.TextField(blank=True)
    activo = models.BooleanField(default=True, db_index=True)
    fecha_registro = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ["cod_inventario"]
        verbose_name = "Dispositivo"
        verbose_name_plural = "Dispositivos"

    def __str__(self):
        return f"{self.cod_inventario} — {self.tipo_dispositivo}"


# ── Subtablas (PK = FK a dispositivo) ────────────────────────────────────────

class DispComputadora(models.Model):
    dispositivo = models.OneToOneField(
        Dispositivo, on_delete=models.CASCADE, primary_key=True,
        related_name="computadora",
    )
    sistema_operativo = models.ForeignKey(
        "catalogo.SistemaOperativo", null=True, blank=True, on_delete=models.SET_NULL
    )
    procesador = models.ForeignKey(
        "catalogo.Procesador", null=True, blank=True, on_delete=models.SET_NULL
    )
    memoria_ram = models.ForeignKey(
        "catalogo.MemoriaRam", null=True, blank=True, on_delete=models.SET_NULL
    )
    almacenamiento = models.CharField(max_length=100, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True, db_index=True)
    mac = models.CharField(max_length=17, blank=True)
    nombre_equipo = models.CharField(max_length=100, blank=True)
    dominio = models.CharField(max_length=100, blank=True)
    tipo_pc = models.CharField(
        max_length=20,
        choices=[
            ("DESKTOP", "Desktop"), ("LAPTOP", "Laptop"),
            ("ALL_IN_ONE", "All-in-One"), ("SERVIDOR", "Servidor"),
        ],
        blank=True,
    )
    cod_monitor = models.CharField(max_length=100, blank=True)
    cod_teclado = models.CharField(max_length=100, blank=True)
    licencia_office = models.BooleanField(default=False)
    licencia_windows = models.BooleanField(default=False)
    antivirus = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Computadora"
        verbose_name_plural = "Computadoras"


class DispImpresora(models.Model):
    dispositivo = models.OneToOneField(
        Dispositivo, on_delete=models.CASCADE, primary_key=True,
        related_name="impresora",
    )
    tipo = models.CharField(
        max_length=20,
        choices=[
            ("LASER", "Láser"), ("INKJET", "Inkjet"), ("MATRICIAL", "Matricial"),
            ("MULTIFUNCION", "Multifunción"), ("PLOTTER", "Plotter"), ("TERMICA", "Térmica"),
        ],
        blank=True,
    )
    ip = models.GenericIPAddressField(null=True, blank=True)
    mac = models.CharField(max_length=17, blank=True)
    nombre_red = models.CharField(max_length=100, blank=True)
    consumible = models.ForeignKey(
        "catalogo.Consumible", null=True, blank=True, on_delete=models.SET_NULL
    )

    class Meta:
        verbose_name = "Impresora"
        verbose_name_plural = "Impresoras"


class DispMonitor(models.Model):
    dispositivo = models.OneToOneField(
        Dispositivo, on_delete=models.CASCADE, primary_key=True,
        related_name="monitor",
    )
    tamanio_pulgadas = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    resolucion = models.CharField(max_length=30, blank=True)
    tipo_panel = models.CharField(
        max_length=10,
        choices=[("LCD", "LCD"), ("LED", "LED"), ("IPS", "IPS"), ("TN", "TN"), ("VA", "VA")],
        blank=True,
    )
    conexion = models.CharField(
        max_length=10,
        choices=[("HDMI", "HDMI"), ("VGA", "VGA"), ("DVI", "DVI"), ("DP", "DisplayPort")],
        blank=True,
    )

    class Meta:
        verbose_name = "Monitor"
        verbose_name_plural = "Monitores"


class DispPeriferico(models.Model):
    dispositivo = models.OneToOneField(
        Dispositivo, on_delete=models.CASCADE, primary_key=True,
        related_name="periferico",
    )
    subtipo = models.CharField(
        max_length=20,
        choices=[
            ("TECLADO", "Teclado"), ("MOUSE", "Mouse"), ("WEBCAM", "Webcam"),
            ("BIOMETRICO", "Biométrico"), ("TABLET", "Tablet"),
            ("LECTORA_QR", "Lectora QR"), ("OTRO", "Otro"),
        ],
        blank=True,
    )
    conexion = models.CharField(
        max_length=15,
        choices=[
            ("USB", "USB"), ("BLUETOOTH", "Bluetooth"),
            ("PS2", "PS/2"), ("INALAMBRICO", "Inalámbrico"),
        ],
        blank=True,
    )

    class Meta:
        verbose_name = "Periférico"
        verbose_name_plural = "Periféricos"


class DispRed(models.Model):
    dispositivo = models.OneToOneField(
        Dispositivo, on_delete=models.CASCADE, primary_key=True,
        related_name="red",
    )
    subtipo = models.CharField(
        max_length=20,
        choices=[
            ("SWITCH", "Switch"), ("ROUTER", "Router"), ("AP", "Access Point"),
            ("NVR", "NVR"), ("DVR", "DVR"), ("UPS", "UPS"),
            ("ESTABILIZADOR", "Estabilizador"), ("SERVIDOR", "Servidor"),
        ],
        blank=True,
    )
    ip = models.GenericIPAddressField(null=True, blank=True)
    mac = models.CharField(max_length=17, blank=True)
    nombre_red = models.CharField(max_length=100, blank=True)
    puertos = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = "Equipo de Red"
        verbose_name_plural = "Equipos de Red"


class DispCamara(models.Model):
    dispositivo = models.OneToOneField(
        Dispositivo, on_delete=models.CASCADE, primary_key=True,
        related_name="camara",
    )
    tipo_camara = models.CharField(
        max_length=10,
        choices=[("DOMO", "Domo"), ("BULLET", "Bullet"), ("PTZ", "PTZ")],
        blank=True,
    )
    ip = models.GenericIPAddressField(null=True, blank=True)
    mac = models.CharField(max_length=17, blank=True)
    usuario_acceso = models.CharField(max_length=100, blank=True)
    clave_acceso = models.CharField(max_length=200, blank=True)
    nvr = models.ForeignKey(
        Dispositivo, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="camaras_conectadas",
    )

    class Meta:
        verbose_name = "Cámara"
        verbose_name_plural = "Cámaras"


class DispTelefono(models.Model):
    dispositivo = models.OneToOneField(
        Dispositivo, on_delete=models.CASCADE, primary_key=True,
        related_name="telefono",
    )
    extension = models.CharField(max_length=20, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    mac = models.CharField(max_length=17, blank=True)

    class Meta:
        verbose_name = "Teléfono"
        verbose_name_plural = "Teléfonos"


# ── Bienes de Baja ────────────────────────────────────────────────────────────

class EstadoBaja(models.TextChoices):
    PENDIENTE = "PENDIENTE", "Pendiente"
    APROBADO = "APROBADO", "Aprobado"
    PROCESADO = "PROCESADO", "Procesado"


class BienBaja(models.Model):
    # Dispositivo registrado (nullable para dispositivos sin registro)
    dispositivo = models.ForeignKey(
        Dispositivo, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="bajas",
    )
    # Dispositivos no registrados en inventario
    sin_registro = models.BooleanField(default=False)
    sr_cod_inventario = models.CharField(max_length=100, blank=True)
    sr_descripcion = models.CharField(max_length=300, blank=True)
    sr_marca = models.CharField(max_length=100, blank=True)
    sr_modelo = models.CharField(max_length=150, blank=True)
    sr_serie = models.CharField(max_length=150, blank=True)

    cod_inventario_ref = models.CharField(max_length=100, blank=True)
    motivo = models.TextField()
    estado = models.CharField(
        max_length=10,
        choices=EstadoBaja.choices,
        default=EstadoBaja.PENDIENTE,
        db_index=True,
    )
    fecha = models.DateField(auto_now_add=True)
    lugar_origen = models.CharField(max_length=200, blank=True)
    observacion = models.TextField(blank=True)
    registrado_por = models.ForeignKey(
        "users.UserProfile", on_delete=models.PROTECT, related_name="bajas_registradas"
    )

    class Meta:
        ordering = ["-fecha"]
        verbose_name = "Bien de Baja"
        verbose_name_plural = "Bienes de Baja"

    def __str__(self):
        if self.dispositivo_id:
            return f"Baja {self.dispositivo.cod_inventario}"
        return f"Baja sin registro — {self.sr_cod_inventario or self.sr_descripcion}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if not self.sin_registro and self.dispositivo is None:
            raise ValidationError("Debe indicar el dispositivo o marcar como sin registro.")
        if self.sin_registro and not self.sr_descripcion:
            raise ValidationError("Debe ingresar descripción para dispositivos sin registro.")


class BienBajaFoto(models.Model):
    bien_baja = models.ForeignKey(BienBaja, on_delete=models.CASCADE, related_name="fotos")
    archivo = models.ImageField(upload_to="bajas/fotos/%Y/%m/")
    fecha = models.DateField(auto_now_add=True)
    slot = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["slot"]
        verbose_name = "Foto de Baja"
        verbose_name_plural = "Fotos de Baja"
