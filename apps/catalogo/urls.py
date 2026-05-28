from django.urls import path
from .views import (
    MarcaListView, MarcaDetailView,
    TipoDispositivoListView,
    SistemaOperativoListView,
    ProcesadorListView,
    MemoriaRamListView,
    ConsumibleListView, ConsumibleDetailView,
)

urlpatterns = [
    path("marcas/", MarcaListView.as_view(), name="marca-list"),
    path("marcas/<int:pk>/", MarcaDetailView.as_view(), name="marca-detail"),
    path("tipos-dispositivo/", TipoDispositivoListView.as_view(), name="tipo-dispositivo-list"),
    path("sistemas-operativos/", SistemaOperativoListView.as_view(), name="so-list"),
    path("procesadores/", ProcesadorListView.as_view(), name="procesador-list"),
    path("memorias-ram/", MemoriaRamListView.as_view(), name="memoria-list"),
    path("consumibles/", ConsumibleListView.as_view(), name="consumible-list"),
    path("consumibles/<int:pk>/", ConsumibleDetailView.as_view(), name="consumible-detail"),
]
