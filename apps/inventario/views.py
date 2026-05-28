from django.db import models as django_models
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.permissions import EsInformatica, EsJefe
from .models import (
    Dispositivo, DispComputadora, DispImpresora, DispMonitor,
    DispPeriferico, DispRed, DispCamara, DispTelefono,
    BienBaja, BienBajaFoto, EstadoDispositivo,
)
from .serializers import (
    DispositivoListSerializer, DispositivoDetailSerializer, DispositivoWriteSerializer,
    DispComputadoraSerializer, DispImpresoraSerializer, DispMonitorSerializer,
    DispPeripericoSerializer, DispRedSerializer, DispCamaraSerializer, DispTelefonoSerializer,
    BienBajaSerializer, BienBajaFotoSerializer,
)

_SUBTABLA_MAP = {
    "COMPUTADORA": (DispComputadora, DispComputadoraSerializer),
    "IMPRESORA": (DispImpresora, DispImpresoraSerializer),
    "MONITOR": (DispMonitor, DispMonitorSerializer),
    "PERIFERICO": (DispPeriferico, DispPeripericoSerializer),
    "RED": (DispRed, DispRedSerializer),
    "CAMARA": (DispCamara, DispCamaraSerializer),
    "TELEFONO": (DispTelefono, DispTelefonoSerializer),
}


class DispositivoListView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, EsInformatica]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return DispositivoWriteSerializer
        return DispositivoListSerializer

    def get_queryset(self):
        qs = Dispositivo.objects.select_related(
            "tipo_dispositivo", "marca", "sede", "responsable"
        )
        params = self.request.query_params
        if params.get("tipo"):
            qs = qs.filter(tipo_dispositivo__codigo=params["tipo"].upper())
        if params.get("estado"):
            qs = qs.filter(estado=params["estado"].upper())
        if params.get("sede"):
            qs = qs.filter(sede_id=params["sede"])
        if params.get("activo"):
            qs = qs.filter(activo=params["activo"].lower() in ("true", "1"))
        if params.get("q"):
            q = params["q"]
            qs = qs.filter(
                django_models.Q(cod_inventario__icontains=q)
                | django_models.Q(serie__icontains=q)
                | django_models.Q(modelo__icontains=q)
            )
        return qs.order_by("cod_inventario")

    def create(self, request, *args, **kwargs):
        serializer = DispositivoWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dispositivo = serializer.save()
        return Response(
            DispositivoDetailSerializer(dispositivo).data,
            status=status.HTTP_201_CREATED,
        )


class DispositivoDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, EsInformatica]
    queryset = Dispositivo.objects.select_related(
        "tipo_dispositivo", "marca", "sede", "unidad_organica",
        "subgerencia", "dependencia", "responsable",
    ).prefetch_related(
        "computadora", "impresora", "monitor", "periferico",
        "red", "camara", "telefono",
    )
    http_method_names = ["get", "patch", "delete", "head", "options"]

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return DispositivoWriteSerializer
        return DispositivoDetailSerializer

    def destroy(self, request, *args, **kwargs):
        dispositivo = self.get_object()
        dispositivo.activo = False
        dispositivo.estado = EstadoDispositivo.DE_BAJA
        dispositivo.save(update_fields=["activo", "estado"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubtablaView(APIView):
    """GET/PUT/PATCH para la subtabla específica de un dispositivo."""
    permission_classes = [IsAuthenticated, EsInformatica]

    def _get_dispositivo(self, pk):
        try:
            return Dispositivo.objects.select_related("tipo_dispositivo").get(pk=pk)
        except Dispositivo.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound("Dispositivo no encontrado.")

    def _get_model_and_serializer(self, tipo_codigo):
        entry = _SUBTABLA_MAP.get(tipo_codigo)
        if not entry:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(f"Tipo '{tipo_codigo}' no tiene subtabla.")
        return entry

    def get(self, request, pk):
        disp = self._get_dispositivo(pk)
        modelo_cls, serializer_cls = self._get_model_and_serializer(disp.tipo_dispositivo.codigo)
        try:
            subtabla = modelo_cls.objects.get(dispositivo=disp)
        except modelo_cls.DoesNotExist:
            return Response({})
        return Response(serializer_cls(subtabla).data)

    def put(self, request, pk):
        disp = self._get_dispositivo(pk)
        modelo_cls, serializer_cls = self._get_model_and_serializer(disp.tipo_dispositivo.codigo)
        try:
            subtabla = modelo_cls.objects.get(dispositivo=disp)
            serializer = serializer_cls(subtabla, data=request.data)
        except modelo_cls.DoesNotExist:
            serializer = serializer_cls(data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save(dispositivo=disp)
        return Response(serializer.data)

    def patch(self, request, pk):
        disp = self._get_dispositivo(pk)
        modelo_cls, serializer_cls = self._get_model_and_serializer(disp.tipo_dispositivo.codigo)
        try:
            subtabla = modelo_cls.objects.get(dispositivo=disp)
        except modelo_cls.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound("Subtabla no encontrada. Use PUT para crearla.")

        serializer = serializer_cls(subtabla, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class BienBajaListView(ListCreateAPIView):
    serializer_class = BienBajaSerializer
    permission_classes = [IsAuthenticated, EsInformatica]

    def get_queryset(self):
        qs = BienBaja.objects.select_related("dispositivo", "registrado_por").prefetch_related("fotos")
        estado = self.request.query_params.get("estado")
        if estado:
            qs = qs.filter(estado=estado.upper())
        return qs


class BienBajaDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = BienBajaSerializer
    permission_classes = [IsAuthenticated, EsInformatica]
    queryset = BienBaja.objects.select_related("dispositivo", "registrado_por").prefetch_related("fotos")
    http_method_names = ["get", "patch", "head", "options"]


class BienBajaFotoView(APIView):
    """Subir foto a un bien de baja."""
    permission_classes = [IsAuthenticated, EsInformatica]

    def post(self, request, pk):
        try:
            bien_baja = BienBaja.objects.get(pk=pk)
        except BienBaja.DoesNotExist:
            return Response({"detail": "No encontrado."}, status=status.HTTP_404_NOT_FOUND)

        if bien_baja.fotos.count() >= 5:
            return Response(
                {"detail": "Máximo 5 fotos por baja."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        slot = bien_baja.fotos.count() + 1
        serializer = BienBajaFotoSerializer(
            data={"archivo": request.FILES.get("archivo"), "slot": slot}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(bien_baja=bien_baja)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
