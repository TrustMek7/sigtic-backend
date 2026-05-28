from django.urls import path
from .views import (
    SedeListView, SedeDetailView,
    UnidadOrganicaListView, UnidadOrganicaDetailView,
    SubgerenciaListView, DependenciaListView,
)

urlpatterns = [
    path("sedes/", SedeListView.as_view(), name="sede-list"),
    path("sedes/<int:pk>/", SedeDetailView.as_view(), name="sede-detail"),
    path("unidades/", UnidadOrganicaListView.as_view(), name="unidad-list"),
    path("unidades/<int:pk>/", UnidadOrganicaDetailView.as_view(), name="unidad-detail"),
    path("subgerencias/", SubgerenciaListView.as_view(), name="subgerencia-list"),
    path("dependencias/", DependenciaListView.as_view(), name="dependencia-list"),
]
