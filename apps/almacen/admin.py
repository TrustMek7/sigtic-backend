from django.contrib import admin
from .models import StockConsumible, MovimientoStock


@admin.register(StockConsumible)
class StockConsumibleAdmin(admin.ModelAdmin):
    list_display = ["consumible", "marca", "stock_actual", "stock_minimo", "bajo_minimo"]
    list_filter = ["consumible__tipo"]

    @admin.display(boolean=True)
    def bajo_minimo(self, obj):
        return obj.bajo_minimo


@admin.register(MovimientoStock)
class MovimientoStockAdmin(admin.ModelAdmin):
    list_display = ["stock_consumible", "tipo", "cantidad", "registrado_por", "fecha"]
    list_filter = ["tipo"]
    readonly_fields = ["fecha"]
