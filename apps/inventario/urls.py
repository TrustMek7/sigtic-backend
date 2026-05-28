from django.urls import path
from .views import (
    DispositivoListView, DispositivoDetailView, SubtablaView,
    BienBajaListView, BienBajaDetailView, BienBajaFotoView,
)

urlpatterns = [
    path("dispositivos/", DispositivoListView.as_view(), name="dispositivo-list"),
    path("dispositivos/<int:pk>/", DispositivoDetailView.as_view(), name="dispositivo-detail"),
    path("dispositivos/<int:pk>/subtabla/", SubtablaView.as_view(), name="dispositivo-subtabla"),
    path("bajas/", BienBajaListView.as_view(), name="bienbaja-list"),
    path("bajas/<int:pk>/", BienBajaDetailView.as_view(), name="bienbaja-detail"),
    path("bajas/<int:pk>/fotos/", BienBajaFotoView.as_view(), name="bienbaja-foto"),
]
