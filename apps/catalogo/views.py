from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated

from apps.users.permissions import EsInformatica
from .models import Marca, TipoDispositivo, SistemaOperativo, Procesador, MemoriaRam, Consumible
from .serializers import (
    MarcaSerializer, TipoDispositivoSerializer, SistemaOperativoSerializer,
    ProcesadorSerializer, MemoriaRamSerializer, ConsumibleSerializer,
)


def _catalogo_permissions(request):
    if request.method == "GET":
        return [IsAuthenticated()]
    return [IsAuthenticated(), EsInformatica()]


class MarcaListView(ListCreateAPIView):
    queryset = Marca.objects.all()
    serializer_class = MarcaSerializer
    pagination_class = None

    def get_permissions(self):
        return _catalogo_permissions(self.request)


class MarcaDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Marca.objects.all()
    serializer_class = MarcaSerializer
    permission_classes = [IsAuthenticated, EsInformatica]


class TipoDispositivoListView(ListCreateAPIView):
    queryset = TipoDispositivo.objects.all()
    serializer_class = TipoDispositivoSerializer
    pagination_class = None

    def get_permissions(self):
        return _catalogo_permissions(self.request)


class SistemaOperativoListView(ListCreateAPIView):
    queryset = SistemaOperativo.objects.all()
    serializer_class = SistemaOperativoSerializer
    pagination_class = None

    def get_permissions(self):
        return _catalogo_permissions(self.request)


class ProcesadorListView(ListCreateAPIView):
    queryset = Procesador.objects.all()
    serializer_class = ProcesadorSerializer
    pagination_class = None

    def get_permissions(self):
        return _catalogo_permissions(self.request)


class MemoriaRamListView(ListCreateAPIView):
    queryset = MemoriaRam.objects.all()
    serializer_class = MemoriaRamSerializer
    pagination_class = None

    def get_permissions(self):
        return _catalogo_permissions(self.request)


class ConsumibleListView(ListCreateAPIView):
    serializer_class = ConsumibleSerializer
    pagination_class = None

    def get_queryset(self):
        qs = Consumible.objects.all()
        tipo = self.request.query_params.get("tipo")
        if tipo:
            qs = qs.filter(tipo=tipo.upper())
        q = self.request.query_params.get("q")
        if q:
            qs = qs.filter(nombre__icontains=q)
        return qs

    def get_permissions(self):
        return _catalogo_permissions(self.request)


class ConsumibleDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Consumible.objects.all()
    serializer_class = ConsumibleSerializer
    permission_classes = [IsAuthenticated, EsInformatica]
