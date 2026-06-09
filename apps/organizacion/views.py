from rest_framework.generics import ListAPIView, ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated

from apps.users.permissions import EsInformatica, EsJefe
from .models import Sede, UnidadOrganica, Subgerencia, Dependencia
from .serializers import (
    SedeSerializer,
    UnidadOrganicaSerializer,
    UnidadOrganicaFlatSerializer,
    SubgerenciaSerializer,
    DependenciaSerializer,
)


class SedeListView(ListCreateAPIView):
    queryset = Sede.objects.all()
    serializer_class = SedeSerializer
    pagination_class = None

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAuthenticated(), EsJefe()]


class SedeDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Sede.objects.all()
    serializer_class = SedeSerializer
    permission_classes = [IsAuthenticated, EsJefe]


class UnidadOrganicaListView(ListCreateAPIView):
    serializer_class = UnidadOrganicaFlatSerializer
    pagination_class = None

    def get_queryset(self):
        return UnidadOrganica.objects.select_related("superior").all()

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAuthenticated(), EsJefe()]


class UnidadOrganicaDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = UnidadOrganicaSerializer
    permission_classes = [IsAuthenticated, EsJefe]
    queryset = UnidadOrganica.objects.prefetch_related("subgerencias__dependencias").all()


class SubgerenciaListView(ListCreateAPIView):
    serializer_class = SubgerenciaSerializer
    pagination_class = None

    def get_queryset(self):
        qs = Subgerencia.objects.select_related("unidad_organica")
        unidad_id = self.request.query_params.get("unidad_organica")
        if unidad_id:
            qs = qs.filter(unidad_organica_id=unidad_id)
        return qs

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAuthenticated(), EsJefe()]


class DependenciaListView(ListCreateAPIView):
    serializer_class = DependenciaSerializer
    pagination_class = None

    def get_queryset(self):
        qs = Dependencia.objects.select_related("subgerencia")
        subgerencia_id = self.request.query_params.get("subgerencia")
        if subgerencia_id:
            qs = qs.filter(subgerencia_id=subgerencia_id)
        return qs

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAuthenticated(), EsJefe()]
