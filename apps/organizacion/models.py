from django.db import models


class Sede(models.Model):
    nombre = models.CharField(max_length=200)
    direccion = models.CharField(max_length=300, blank=True)
    sed_ide_siggo = models.IntegerField(unique=True, null=True, blank=True, db_index=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Sede"
        verbose_name_plural = "Sedes"

    def __str__(self):
        return self.nombre


class UnidadOrganica(models.Model):
    nombre = models.CharField(max_length=200)
    abreviatura = models.CharField(max_length=20, blank=True)
    nivel = models.IntegerField(default=1)
    superior = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="subordinadas",
    )
    uni_ide_siggo = models.IntegerField(unique=True, null=True, blank=True, db_index=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Unidad Orgánica"
        verbose_name_plural = "Unidades Orgánicas"

    def __str__(self):
        return self.nombre


class Subgerencia(models.Model):
    nombre = models.CharField(max_length=200)
    unidad_organica = models.ForeignKey(
        UnidadOrganica,
        on_delete=models.CASCADE,
        related_name="subgerencias",
    )

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Subgerencia"
        verbose_name_plural = "Subgerencias"

    def __str__(self):
        return self.nombre


class Dependencia(models.Model):
    nombre = models.CharField(max_length=200)
    subgerencia = models.ForeignKey(
        Subgerencia,
        on_delete=models.CASCADE,
        related_name="dependencias",
    )

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Dependencia"
        verbose_name_plural = "Dependencias"

    def __str__(self):
        return self.nombre
