from django.urls import path
from .views import (
    DispositivoListView, DispositivoDetailView, SubtablaView,
    BienBajaListView, BienBajaDetailView, BienBajaFotoView,
    TrasladoListView, TrasladoDetailView, TrasladoPDFView,
)

urlpatterns = [
    path("dispositivos/", DispositivoListView.as_view(), name="dispositivo-list"),
    path("dispositivos/<int:pk>/", DispositivoDetailView.as_view(), name="dispositivo-detail"),
    path("dispositivos/<int:pk>/subtabla/", SubtablaView.as_view(), name="dispositivo-subtabla"),
    path("bajas/", BienBajaListView.as_view(), name="bienbaja-list"),
    path("bajas/<int:pk>/", BienBajaDetailView.as_view(), name="bienbaja-detail"),
    path("bajas/<int:pk>/fotos/", BienBajaFotoView.as_view(), name="bienbaja-foto"),
    # Traslados
    path("traslados/", TrasladoListView.as_view(), name="traslado-list"),
    path("traslados/<int:pk>/", TrasladoDetailView.as_view(), name="traslado-detail"),
    path("traslados/<int:pk>/pdf/", TrasladoPDFView.as_view(), name="traslado-pdf"),
]
