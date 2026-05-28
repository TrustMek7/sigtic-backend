from django.contrib import admin
from .models import Marca, TipoDispositivo, SistemaOperativo, Procesador, MemoriaRam, Consumible

admin.site.register(Marca)
admin.site.register(TipoDispositivo)
admin.site.register(SistemaOperativo)
admin.site.register(Procesador)
admin.site.register(MemoriaRam)


@admin.register(Consumible)
class ConsumibleAdmin(admin.ModelAdmin):
    list_display = ["nombre", "tipo"]
    list_filter = ["tipo"]
