from rest_framework import serializers
from .models import (
    Dispositivo, DispComputadora, DispImpresora, DispMonitor,
    DispPeriferico, DispRed, DispCamara, DispTelefono,
    BienBaja, BienBajaFoto,
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
