from django.contrib import admin
from .models import Ticket, TicketDiagnostico, TicketAccion, TicketHistorial, TicketTercerizado


class TicketHistorialInline(admin.TabularInline):
    model = TicketHistorial
    extra = 0
    readonly_fields = ["usuario", "estado_anterior", "estado_nuevo", "comentario", "fecha"]
    can_delete = False


class TicketAccionInline(admin.TabularInline):
    model = TicketAccion
    extra = 0
    readonly_fields = ["tecnico", "tipo_accion", "detalle", "fecha_registro"]
    can_delete = False


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = [
        "numero", "estado", "tipo_mantenimiento",
        "dispositivo", "solicitante", "tecnico", "fecha_creacion",
    ]
    list_filter = ["estado", "tipo_mantenimiento"]
    search_fields = ["numero", "dispositivo__cod_inventario", "solicitante__nombre_completo"]
    readonly_fields = [
        "numero", "ip_solicitante", "responsable_snapshot",
        "nombre_responsable_snapshot", "cargo_responsable_snapshot",
        "fecha_creacion",
    ]
    inlines = [TicketHistorialInline, TicketAccionInline]


@admin.register(TicketDiagnostico)
class DiagnosticoAdmin(admin.ModelAdmin):
    list_display = ["ticket", "tipo_resultado", "tipo_falla", "tecnico", "fecha_registro"]
    list_filter = ["tipo_resultado"]
