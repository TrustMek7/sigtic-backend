from django.db import models as django_models
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse, inline_serializer
from rest_framework import serializers as drf_serializers, status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from apps.users.permissions import EsInformatica, EsJefe, _get_profile
from .models import (
    Dispositivo, DispComputadora, DispImpresora, DispMonitor,
    DispPeriferico, DispRed, DispCamara, DispTelefono,
    BienBaja, BienBajaFoto, EstadoDispositivo,
    Traslado, EstadoTraslado,
)
from .serializers import (
    DispositivoListSerializer, DispositivoDetailSerializer, DispositivoWriteSerializer,
    DispComputadoraSerializer, DispImpresoraSerializer, DispMonitorSerializer,
    DispPeripericoSerializer, DispRedSerializer, DispCamaraSerializer, DispTelefonoSerializer,
    BienBajaSerializer, BienBajaFotoSerializer,
    TrasladoListSerializer, TrasladoDetailSerializer,
    TrasladoWriteSerializer, TrasladoEstadoSerializer,
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


@extend_schema_view(
    get=extend_schema(tags=["Inventario"], responses={200: OpenApiResponse(description="Datos de la subtabla segun el tipo de dispositivo (computadora, impresora, monitor, etc.).")}, summary="Obtiene la subtabla del dispositivo"),
    put=extend_schema(tags=["Inventario"], request=OpenApiResponse(description="Datos de la subtabla."), responses={200: OpenApiResponse(description="Subtabla actualizada.")}, summary="Reemplaza la subtabla del dispositivo"),
    patch=extend_schema(tags=["Inventario"], request=OpenApiResponse(description="Campos a actualizar."), responses={200: OpenApiResponse(description="Subtabla actualizada.")}, summary="Actualiza parcialmente la subtabla"),
)
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


@extend_schema(
    tags=["Bajas"],
    request=inline_serializer("FotoUpload", {"archivo": drf_serializers.ImageField(), "slot": drf_serializers.IntegerField()}),
    responses={201: OpenApiResponse(description="Foto adjuntada al bien de baja.")},
    summary="Sube una foto de un bien de baja",
)
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


# ── Traslados ─────────────────────────────────────────────────────────────────

class TrasladoListView(ListCreateAPIView):
    """Lista traslados y crea uno nuevo."""
    permission_classes = [IsAuthenticated, EsInformatica]

    def get_serializer_class(self):
        return TrasladoWriteSerializer if self.request.method == "POST" else TrasladoListSerializer

    def get_queryset(self):
        qs = Traslado.objects.select_related(
            "dispositivo__tipo_dispositivo",
            "sede_origen", "sede_destino",
            "area_origen", "area_destino",
            "solicitado_por",
        )
        params = self.request.query_params
        if params.get("estado"):
            qs = qs.filter(estado=params["estado"].upper())
        if params.get("dispositivo"):
            qs = qs.filter(dispositivo_id=params["dispositivo"])
        if params.get("sede_destino"):
            qs = qs.filter(sede_destino_id=params["sede_destino"])
        return qs

    def create(self, request, *args, **kwargs):
        serializer = TrasladoWriteSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        traslado = serializer.save()
        return Response(TrasladoDetailSerializer(traslado).data, status=status.HTTP_201_CREATED)


class TrasladoDetailView(APIView):
    """Detalle de un traslado y cambio de estado."""
    permission_classes = [IsAuthenticated, EsInformatica]

    def _get_traslado(self, pk):
        return get_object_or_404(
            Traslado.objects.select_related(
                "dispositivo__tipo_dispositivo", "dispositivo__marca",
                "sede_origen", "area_origen", "subger_origen", "depend_origen", "responsable_origen",
                "sede_destino", "area_destino", "subger_destino", "depend_destino", "responsable_destino",
                "solicitado_por", "aprobado_por",
            ),
            pk=pk,
        )

    def get(self, request, pk):
        return Response(TrasladoDetailSerializer(self._get_traslado(pk)).data)

    def patch(self, request, pk):
        traslado = self._get_traslado(pk)

        # Cambio de estado requiere ser jefe/admin
        if "estado" in request.data:
            if not (EsJefe().has_permission(request, self)):
                return Response({"detail": "Solo el Jefe de Informática puede cambiar el estado."}, status=status.HTTP_403_FORBIDDEN)

            ser = TrasladoEstadoSerializer(data=request.data)
            ser.is_valid(raise_exception=True)
            nuevo_estado = ser.validated_data["estado"]
            obs_extra    = ser.validated_data.get("observacion", "")
            profile      = _get_profile(request)

            if traslado.estado in (EstadoTraslado.EJECUTADO, EstadoTraslado.RECHAZADO):
                return Response({"detail": "El traslado ya está en estado terminal."}, status=status.HTTP_400_BAD_REQUEST)

            from django.utils import timezone
            if nuevo_estado == EstadoTraslado.APROBADO:
                traslado.estado = EstadoTraslado.APROBADO
                traslado.aprobado_por = profile
                traslado.fecha_aprobacion = timezone.now()
                if obs_extra:
                    traslado.observacion = (traslado.observacion + "\n" + obs_extra).strip()
                traslado.save(update_fields=["estado", "aprobado_por", "fecha_aprobacion", "observacion"])

            elif nuevo_estado == EstadoTraslado.EJECUTADO:
                traslado.ejecutar(aprobado_por=profile)

            elif nuevo_estado == EstadoTraslado.RECHAZADO:
                traslado.estado = EstadoTraslado.RECHAZADO
                if obs_extra:
                    traslado.observacion = (traslado.observacion + "\n" + obs_extra).strip()
                traslado.save(update_fields=["estado", "observacion"])

            return Response(TrasladoDetailSerializer(self._get_traslado(pk)).data)

        # Edición libre de motivo/observacion (solo si aún PENDIENTE)
        if traslado.estado != EstadoTraslado.PENDIENTE:
            return Response({"detail": "Solo se puede editar un traslado en estado PENDIENTE."}, status=status.HTTP_400_BAD_REQUEST)

        for field in ("motivo", "observacion"):
            if field in request.data:
                setattr(traslado, field, request.data[field])
        traslado.save(update_fields=["motivo", "observacion"])
        return Response(TrasladoDetailSerializer(self._get_traslado(pk)).data)


class TrasladoPDFView(APIView):
    """Genera el acta de traslado en PDF."""
    permission_classes = [IsAuthenticated, EsInformatica]

    def get(self, request, pk):
        traslado = get_object_or_404(
            Traslado.objects.select_related(
                "dispositivo__tipo_dispositivo", "dispositivo__marca",
                "sede_origen", "area_origen", "subger_origen", "depend_origen", "responsable_origen",
                "sede_destino", "area_destino", "subger_destino", "depend_destino", "responsable_destino",
                "solicitado_por", "aprobado_por",
            ),
            pk=pk,
        )
        from apps.documentos.pdf_generator import generar_pdf_traslado
        pdf_bytes = generar_pdf_traslado(traslado)
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="traslado-{traslado.numero}.pdf"'
        return response
