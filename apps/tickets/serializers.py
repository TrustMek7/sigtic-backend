from rest_framework import serializers
from .models import (
    Ticket, TicketDiagnostico, TicketAccion,
    TicketHistorial, TicketAdjunto, TicketTercerizado,
    EstadoTicket, TRANSICIONES,
)


class TicketListSerializer(serializers.ModelSerializer):
    solicitante_nombre = serializers.CharField(
        source="solicitante.nombre_completo", read_only=True
    )
    tecnico_nombre = serializers.CharField(
        source="tecnico.nombre_completo", read_only=True, default=""
    )
    dispositivo_cod = serializers.CharField(
        source="dispositivo.cod_inventario", read_only=True
    )
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)

    class Meta:
        model = Ticket
        fields = [
            "id", "numero", "estado", "estado_display",
            "dispositivo", "dispositivo_cod",
            "solicitante_nombre", "tecnico_nombre",
            "tipo_mantenimiento", "fecha_creacion",
        ]


class TicketDiagnosticoSerializer(serializers.ModelSerializer):
    tecnico_nombre = serializers.CharField(
        source="tecnico.nombre_completo", read_only=True
    )

    class Meta:
        model = TicketDiagnostico
        fields = [
            "id", "tipo_falla", "detalle_tecnico", "tipo_resultado",
            "tiempo_estimado", "fecha_registro", "tecnico", "tecnico_nombre",
        ]
        read_only_fields = ["tecnico", "fecha_registro"]


class TicketAccionSerializer(serializers.ModelSerializer):
    tecnico_nombre = serializers.CharField(
        source="tecnico.nombre_completo", read_only=True
    )

    class Meta:
        model = TicketAccion
        fields = ["id", "tipo_accion", "detalle", "tecnico", "tecnico_nombre", "fecha_registro"]
        read_only_fields = ["tecnico", "fecha_registro"]


class TicketHistorialSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(
        source="usuario.nombre_completo", read_only=True
    )
    estado_anterior_display = serializers.SerializerMethodField()
    estado_nuevo_display = serializers.SerializerMethodField()

    class Meta:
        model = TicketHistorial
        fields = [
            "id", "estado_anterior", "estado_anterior_display",
            "estado_nuevo", "estado_nuevo_display",
            "comentario", "usuario_nombre", "fecha",
        ]

    def get_estado_anterior_display(self, obj):
        return EstadoTicket(obj.estado_anterior).label if obj.estado_anterior else ""

    def get_estado_nuevo_display(self, obj):
        try:
            return EstadoTicket(obj.estado_nuevo).label
        except ValueError:
            return obj.estado_nuevo


class TicketTercerizadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketTercerizado
        fields = [
            "id", "empresa", "contacto", "fecha_entrega_est",
            "presupuesto", "estado_tercerizado", "observacion", "registrado_por",
        ]
        read_only_fields = ["registrado_por"]


class TicketDetailSerializer(serializers.ModelSerializer):
    solicitante_nombre = serializers.CharField(
        source="solicitante.nombre_completo", read_only=True
    )
    tecnico_nombre = serializers.CharField(
        source="tecnico.nombre_completo", read_only=True, default=""
    )
    asignado_por_nombre = serializers.CharField(
        source="asignado_por.nombre_completo", read_only=True, default=""
    )
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    dispositivo_cod = serializers.CharField(
        source="dispositivo.cod_inventario", read_only=True
    )
    dispositivo_tipo = serializers.CharField(
        source="dispositivo.tipo_dispositivo.nombre", read_only=True
    )
    diagnostico = TicketDiagnosticoSerializer(read_only=True)
    acciones = TicketAccionSerializer(many=True, read_only=True)
    historial = TicketHistorialSerializer(many=True, read_only=True)
    tercerizado = TicketTercerizadoSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = [
            "id", "numero", "estado", "estado_display",
            "dispositivo", "dispositivo_cod", "dispositivo_tipo",
            "solicitante", "solicitante_nombre",
            "asignado_por", "asignado_por_nombre",
            "tecnico", "tecnico_nombre",
            "tipo_mantenimiento", "detalle_falla",
            "ip_solicitante",
            "responsable_snapshot", "nombre_responsable_snapshot", "cargo_responsable_snapshot",
            "fecha_creacion", "fecha_asignacion", "fecha_inicio", "fecha_cierre",
            "observaciones",
            "diagnostico", "acciones", "historial", "tercerizado",
        ]


class TicketCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ["dispositivo", "tipo_mantenimiento", "detalle_falla", "observaciones"]

    def create(self, validated_data):
        from apps.users.permissions import _get_profile
        from django.utils import timezone

        request = self.context["request"]
        profile = _get_profile(request)
        dispositivo = validated_data["dispositivo"]

        # Snapshot del responsable actual
        responsable = dispositivo.responsable
        nombre_snap = responsable.nombre_completo if responsable else dispositivo.dni_responsable
        cargo_snap = ""
        if responsable and responsable.cargo_principal:
            cargo_snap = responsable.cargo_principal.cargo_descripcion

        # Captura de IP del solicitante
        ip_solicitante = _get_client_ip(request)

        ticket = Ticket.objects.create(
            **validated_data,
            solicitante=profile,
            estado=EstadoTicket.ENVIADO,
            ip_solicitante=ip_solicitante,
            responsable_snapshot=responsable,
            nombre_responsable_snapshot=nombre_snap,
            cargo_responsable_snapshot=cargo_snap,
        )

        TicketHistorial.objects.create(
            ticket=ticket,
            usuario=profile,
            estado_anterior="",
            estado_nuevo="ENVIADO",
            comentario="Ticket creado.",
        )

        return ticket


def _get_client_ip(request) -> str:
    """Extrae la IP real del cliente considerando proxies."""
    x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded:
        return x_forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


class TransicionSerializer(serializers.Serializer):
    nuevo_estado = serializers.ChoiceField(choices=EstadoTicket.choices)
    comentario = serializers.CharField(required=False, allow_blank=True, default="")
    tecnico_id = serializers.IntegerField(required=False, allow_null=True)
