from django.contrib import admin
from .models import (
    Dispositivo, DispComputadora, DispImpresora, DispMonitor,
    DispPeriferico, DispRed, DispCamara, DispTelefono,
    BienBaja, BienBajaFoto,
)


class DispComputadoraInline(admin.StackedInline):
    model = DispComputadora
    extra = 0


class DispImpresoraInline(admin.StackedInline):
    model = DispImpresora
    extra = 0


class DispMonitorInline(admin.StackedInline):
    model = DispMonitor
    extra = 0


class DispPeripericoInline(admin.StackedInline):
    model = DispPeriferico
    extra = 0


class DispRedInline(admin.StackedInline):
    model = DispRed
    extra = 0


class DispCamaraInline(admin.StackedInline):
    model = DispCamara
    extra = 0
    fk_name = "dispositivo"


class DispTelefonoInline(admin.StackedInline):
    model = DispTelefono
    extra = 0


@admin.register(Dispositivo)
class DispositivoAdmin(admin.ModelAdmin):
    list_display = ["cod_inventario", "tipo_dispositivo", "marca", "modelo", "estado", "sede", "activo"]
    list_filter = ["tipo_dispositivo", "estado", "sede", "activo"]
    search_fields = ["cod_inventario", "serie", "modelo"]
    inlines = [
        DispComputadoraInline, DispImpresoraInline, DispMonitorInline,
        DispPeripericoInline, DispRedInline, DispCamaraInline, DispTelefonoInline,
    ]


class BienBajaFotoInline(admin.TabularInline):
    model = BienBajaFoto
    extra = 0


@admin.register(BienBaja)
class BienBajaAdmin(admin.ModelAdmin):
    list_display = ["id", "dispositivo", "sin_registro", "estado", "fecha", "registrado_por"]
    list_filter = ["estado", "sin_registro"]
    inlines = [BienBajaFotoInline]
