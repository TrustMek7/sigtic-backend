from django.contrib import admin
from .models import UserProfile, UserCargo, EncargadoActivo


class UserCargoInline(admin.TabularInline):
    model = UserCargo
    extra = 0
    readonly_fields = ["car_ide_siggo", "uni_ide_siggo", "uni_nombre_siggo", "car_pri_siggo"]
    fields = [
        "car_ide_siggo", "uni_nombre_siggo", "cargo_descripcion",
        "es_principal", "activo",
    ]


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = [
        "nombre_completo", "dni", "rol", "sede", "activo", "ultimo_sync_siggo"
    ]
    list_filter = ["rol", "activo", "sede"]
    search_fields = ["nombre_completo", "dni", "email"]
    readonly_fields = [
        "usu_ide_siggo", "per_ide_siggo", "dni", "nombre_completo",
        "email", "telefono", "ultimo_sync_siggo",
    ]
    fieldsets = (
        ("Identidad", {
            "fields": ("usu_ide_siggo", "per_ide_siggo", "dni", "nombre_completo", "email", "telefono")
        }),
        ("Rol y organización", {
            "fields": ("rol", "sede", "cargo_principal", "activo")
        }),
        ("Sync", {
            "fields": ("ultimo_sync_siggo",)
        }),
    )
    inlines = [UserCargoInline]


@admin.register(EncargadoActivo)
class EncargadoActivoAdmin(admin.ModelAdmin):
    list_display = ["encargado", "autorizado_por", "desde", "hasta", "activo"]
    list_filter = ["activo"]
    readonly_fields = ["desde"]
