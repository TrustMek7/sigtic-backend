from rest_framework import serializers
from .models import (
    Dispositivo, DispComputadora, DispImpresora, DispMonitor,
    DispPeriferico, DispRed, DispCamara, DispTelefono,
    BienBaja, BienBajaFoto, Traslado, EstadoTraslado,
)


class DispComputadoraSerializer(serializers.ModelSerializer):
    class Meta:
        model = DispComputadora
        exclude = ["dispositivo"]


class DispImpresoraSerializer(serializers.ModelSerializer):
    class Meta:
        model = DispImpresora
        exclude = ["dispositivo"]


class DispMonitorSerializer(serializers.ModelSerializer):
    class Meta:
        model = DispMonitor
        exclude = ["dispositivo"]


class DispPeripericoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DispPeriferico
        exclude = ["dispositivo"]


class DispRedSerializer(serializers.ModelSerializer):
    class Meta:
        model = DispRed
        exclude = ["dispositivo"]


class DispCamaraSerializer(serializers.ModelSerializer):
    class Meta:
        model = DispCamara
        exclude = ["dispositivo"]


class DispTelefonoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DispTelefono
        exclude = ["dispositivo"]


class DispositivoListSerializer(serializers.ModelSerializer):
    tipo_nombre = serializers.CharField(source="tipo_dispositivo.nombre", read_only=True)
    tipo_codigo = serializers.CharField(source="tipo_dispositivo.codigo", read_only=True)
    marca_nombre = serializers.CharField(source="marca.nombre", read_only=True, default="")
    sede_nombre = serializers.CharField(source="sede.nombre", read_only=True, default="")
    responsable_nombre = serializers.CharField(
        source="responsable.nombre_completo", read_only=True, default=""
    )

    class Meta:
        model = Dispositivo
        fields = [
            "id", "cod_inventario", "tipo_codigo", "tipo_nombre",
            "marca_nombre", "modelo", "serie", "estado",
            "sede_nombre", "responsable_nombre", "activo",
        ]


class DispositivoDetailSerializer(serializers.ModelSerializer):
    tipo_nombre = serializers.CharField(source="tipo_dispositivo.nombre", read_only=True)
    tipo_codigo = serializers.CharField(source="tipo_dispositivo.codigo", read_only=True)

    # Subtabla dinámica — solo la que corresponde al tipo
    computadora = DispComputadoraSerializer(read_only=True)
    impresora = DispImpresoraSerializer(read_only=True)
    monitor = DispMonitorSerializer(read_only=True)
    periferico = DispPeripericoSerializer(read_only=True)
    red = DispRedSerializer(read_only=True)
    camara = DispCamaraSerializer(read_only=True)
    telefono = DispTelefonoSerializer(read_only=True)

    class Meta:
        model = Dispositivo
        fields = [
            "id", "tipo_dispositivo", "tipo_codigo", "tipo_nombre",
            "marca", "modelo", "serie", "cod_inventario", "color", "estado",
            "sede", "unidad_organica", "subgerencia", "dependencia",
            "responsable", "dni_responsable", "proveedor", "orden_compra",
            "observacion", "activo", "fecha_registro",
            "computadora", "impresora", "monitor", "periferico",
            "red", "camara", "telefono",
        ]


class DispositivoWriteSerializer(serializers.ModelSerializer):
    """Para creación/edición del dispositivo base (sin subtabla)."""
    class Meta:
        model = Dispositivo
        fields = [
            "tipo_dispositivo", "marca", "modelo", "serie", "cod_inventario",
            "color", "estado", "sede", "unidad_organica", "subgerencia",
            "dependencia", "responsable", "dni_responsable",
            "proveedor", "orden_compra", "observacion", "activo",
        ]


class BienBajaFotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = BienBajaFoto
        fields = ["id", "archivo", "fecha", "slot"]


class BienBajaSerializer(serializers.ModelSerializer):
    fotos = BienBajaFotoSerializer(many=True, read_only=True)
    registrado_por_nombre = serializers.CharField(
        source="registrado_por.nombre_completo", read_only=True
    )
    dispositivo_cod = serializers.CharField(
        source="dispositivo.cod_inventario", read_only=True, default=""
    )

    class Meta:
        model = BienBaja
        fields = [
            "id", "dispositivo", "dispositivo_cod",
            "sin_registro", "sr_cod_inventario", "sr_descripcion",
            "sr_marca", "sr_modelo", "sr_serie",
            "cod_inventario_ref", "motivo", "estado", "fecha",
            "lugar_origen", "observacion",
            "registrado_por", "registrado_por_nombre", "fotos",
        ]
        read_only_fields = ["registrado_por", "fecha"]

    def validate(self, attrs):
        sin_registro = attrs.get("sin_registro", False)
        if not sin_registro and not attrs.get("dispositivo"):
            raise serializers.ValidationError(
                {"dispositivo": "Requerido cuando sin_registro es False."}
            )
        if sin_registro and not attrs.get("sr_descripcion"):
            raise serializers.ValidationError(
                {"sr_descripcion": "Requerido para dispositivos sin registro."}
            )
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        from apps.users.permissions import _get_profile
        validated_data["registrado_por"] = _get_profile(request)
        return super().create(validated_data)


# ── Traslados ─────────────────────────────────────────────────────────────────

class TrasladoListSerializer(serializers.ModelSerializer):
    dispositivo_cod  = serializers.CharField(source="dispositivo.cod_inventario", read_only=True)
    dispositivo_tipo = serializers.CharField(source="dispositivo.tipo_dispositivo.nombre", read_only=True)
    dispositivo_modelo = serializers.CharField(source="dispositivo.modelo", read_only=True)
    sede_origen_nombre   = serializers.CharField(source="sede_origen.nombre",   default="—", read_only=True)
    sede_destino_nombre  = serializers.CharField(source="sede_destino.nombre",  default="—", read_only=True)
    area_origen_nombre   = serializers.CharField(source="area_origen.nombre",   default="—", read_only=True)
    area_destino_nombre  = serializers.CharField(source="area_destino.nombre",  default="—", read_only=True)
    solicitado_por_nombre = serializers.CharField(source="solicitado_por.nombre_completo", read_only=True)
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)

    class Meta:
        model = Traslado
        fields = [
            "id", "numero", "estado", "estado_display",
            "dispositivo", "dispositivo_cod", "dispositivo_tipo", "dispositivo_modelo",
            "sede_origen_nombre", "area_origen_nombre",
            "sede_destino_nombre", "area_destino_nombre",
            "solicitado_por_nombre", "fecha_solicitud",
        ]


class TrasladoDetailSerializer(serializers.ModelSerializer):
    # Origen
    sede_origen_nombre    = serializers.CharField(source="sede_origen.nombre",        default="—", read_only=True)
    area_origen_nombre    = serializers.CharField(source="area_origen.nombre",        default="—", read_only=True)
    subger_origen_nombre  = serializers.CharField(source="subger_origen.nombre",      default="—", read_only=True)
    depend_origen_nombre  = serializers.CharField(source="depend_origen.nombre",      default="—", read_only=True)
    resp_origen_nombre    = serializers.CharField(source="responsable_origen.nombre_completo", default="—", read_only=True)
    # Destino
    sede_destino_nombre   = serializers.CharField(source="sede_destino.nombre",       default="—", read_only=True)
    area_destino_nombre   = serializers.CharField(source="area_destino.nombre",       default="—", read_only=True)
    subger_destino_nombre = serializers.CharField(source="subger_destino.nombre",     default="—", read_only=True)
    depend_destino_nombre = serializers.CharField(source="depend_destino.nombre",     default="—", read_only=True)
    resp_destino_nombre   = serializers.CharField(source="responsable_destino.nombre_completo", default="—", read_only=True)
    # Personas
    solicitado_por_nombre = serializers.CharField(source="solicitado_por.nombre_completo", read_only=True)
    aprobado_por_nombre   = serializers.CharField(source="aprobado_por.nombre_completo",  default="—", read_only=True)
    estado_display        = serializers.CharField(source="get_estado_display", read_only=True)
    # Dispositivo básico
    dispositivo_cod       = serializers.CharField(source="dispositivo.cod_inventario", read_only=True)
    dispositivo_tipo      = serializers.CharField(source="dispositivo.tipo_dispositivo.nombre", read_only=True)
    dispositivo_modelo    = serializers.CharField(source="dispositivo.modelo", read_only=True)
    dispositivo_marca     = serializers.CharField(source="dispositivo.marca.nombre", default="—", read_only=True)
    dispositivo_serie     = serializers.CharField(source="dispositivo.serie", read_only=True)

    class Meta:
        model = Traslado
        fields = [
            "id", "numero", "estado", "estado_display",
            "dispositivo", "dispositivo_cod", "dispositivo_tipo",
            "dispositivo_modelo", "dispositivo_marca", "dispositivo_serie",
            # Origen
            "sede_origen", "sede_origen_nombre",
            "area_origen", "area_origen_nombre",
            "subger_origen", "subger_origen_nombre",
            "depend_origen", "depend_origen_nombre",
            "responsable_origen", "resp_origen_nombre",
            # Destino
            "sede_destino", "sede_destino_nombre",
            "area_destino", "area_destino_nombre",
            "subger_destino", "subger_destino_nombre",
            "depend_destino", "depend_destino_nombre",
            "responsable_destino", "resp_destino_nombre",
            # Meta
            "motivo", "observacion",
            "solicitado_por", "solicitado_por_nombre",
            "aprobado_por", "aprobado_por_nombre",
            "fecha_solicitud", "fecha_aprobacion", "fecha_ejecucion",
        ]
        read_only_fields = [
            "numero", "estado", "solicitado_por",
            "fecha_solicitud", "fecha_aprobacion", "fecha_ejecucion",
        ]


class TrasladoWriteSerializer(serializers.ModelSerializer):
    """Para crear un traslado. El origen se captura automáticamente del dispositivo."""
    class Meta:
        model = Traslado
        fields = [
            "dispositivo",
            "sede_destino", "area_destino", "subger_destino",
            "depend_destino", "responsable_destino",
            "motivo", "observacion",
        ]

    def validate_dispositivo(self, dispositivo):
        if not dispositivo.activo:
            raise serializers.ValidationError("El dispositivo está dado de baja.")
        return dispositivo

    def create(self, validated_data):
        from apps.users.permissions import _get_profile
        request = self.context["request"]
        disp = validated_data["dispositivo"]

        traslado = Traslado(
            **validated_data,
            # Snapshot del origen
            sede_origen        = disp.sede,
            area_origen        = disp.unidad_organica,
            subger_origen      = disp.subgerencia,
            depend_origen      = disp.dependencia,
            responsable_origen = disp.responsable,
            solicitado_por     = _get_profile(request),
        )
        traslado.numero = Traslado._generar_numero()
        traslado.save()
        return traslado


class TrasladoEstadoSerializer(serializers.Serializer):
    """Para cambiar el estado de un traslado (APROBADO / EJECUTADO / RECHAZADO)."""
    estado      = serializers.ChoiceField(choices=["APROBADO", "EJECUTADO", "RECHAZADO"])
    observacion = serializers.CharField(required=False, allow_blank=True)
