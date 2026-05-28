from django.db import models


class Marca(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Marca"
        verbose_name_plural = "Marcas"

    def __str__(self):
        return self.nombre


class TipoDispositivo(models.Model):
    COMPUTADORA = "COMPUTADORA"
    IMPRESORA = "IMPRESORA"
    MONITOR = "MONITOR"
    PERIFERICO = "PERIFERICO"
    RED = "RED"
    CAMARA = "CAMARA"
    TELEFONO = "TELEFONO"

    CODIGO_CHOICES = [
        (COMPUTADORA, "Computadora"),
        (IMPRESORA, "Impresora"),
        (MONITOR, "Monitor"),
        (PERIFERICO, "Periférico"),
        (RED, "Red"),
        (CAMARA, "Cámara"),
        (TELEFONO, "Teléfono"),
    ]

    codigo = models.CharField(max_length=20, unique=True, choices=CODIGO_CHOICES)
    nombre = models.CharField(max_length=100)
    tiene_subtabla = models.BooleanField(default=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Tipo de Dispositivo"
        verbose_name_plural = "Tipos de Dispositivo"

    def __str__(self):
        return self.nombre


class SistemaOperativo(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Sistema Operativo"
        verbose_name_plural = "Sistemas Operativos"

    def __str__(self):
        return self.nombre


class Procesador(models.Model):
    nombre = models.CharField(max_length=150, unique=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Procesador"
        verbose_name_plural = "Procesadores"

    def __str__(self):
        return self.nombre


class MemoriaRam(models.Model):
    capacidad = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ["capacidad"]
        verbose_name = "Memoria RAM"
        verbose_name_plural = "Memorias RAM"

    def __str__(self):
        return self.capacidad


class Consumible(models.Model):
    TONER = "TONER"
    TINTA = "TINTA"
    PAPEL = "PAPEL"
    RIBBON = "RIBBON"
    OTRO = "OTRO"

    TIPO_CHOICES = [
        (TONER, "Tóner"),
        (TINTA, "Tinta"),
        (PAPEL, "Papel"),
        (RIBBON, "Ribbon"),
        (OTRO, "Otro"),
    ]

    nombre = models.CharField(max_length=150, unique=True)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default=OTRO)

    class Meta:
        ordering = ["tipo", "nombre"]
        verbose_name = "Consumible"
        verbose_name_plural = "Consumibles"

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"
