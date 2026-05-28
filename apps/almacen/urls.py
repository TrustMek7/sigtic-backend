from django.urls import path
from .views import StockConsumibleListView, StockConsumibleDetailView, MovimientoStockListView

urlpatterns = [
    path("stock/", StockConsumibleListView.as_view(), name="stock-list"),
    path("stock/<int:pk>/", StockConsumibleDetailView.as_view(), name="stock-detail"),
    path("movimientos/", MovimientoStockListView.as_view(), name="movimiento-list"),
]
