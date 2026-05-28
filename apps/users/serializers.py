from rest_framework import serializers
from .models import UserProfile, UserCargo, EncargadoActivo, RolSigtic


class UserCargoSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserCargo
        fields = [
            "id", "car_ide_siggo", "uni_ide_siggo",
            "uni_nombre_siggo", "cargo_descripcion",
            "es_principal", "activo",
        ]


class UserProfileSerializer(serializers.ModelSerializer):
    cargos = UserCargoSerializer(many=True, read_only=True)
    rol_display = serializers.CharField(source="get_rol_display", read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "id", "dni", "nombre_completo", "email", "telefono",
            "rol", "rol_display", "sede", "activo",
            "ultimo_sync_siggo", "cargos",
        ]
        read_only_fields = [
            "dni", "nombre_completo", "email", "telefono",
            "ultimo_sync_siggo", "cargos",
        ]


class UserProfileListSerializer(serializers.ModelSerializer):
    rol_display = serializers.CharField(source="get_rol_display", read_only=True)
    cargo_descripcion = serializers.CharField(
        source="cargo_principal.cargo_descripcion",
        read_only=True,
        default="",
    )

    class Meta:
        model = UserProfile
        fields = [
            "id", "dni", "nombre_completo", "rol", "rol_display",
            "cargo_descripcion", "activo",
        ]


class EncargadoActivoSerializer(serializers.ModelSerializer):
    encargado_nombre = serializers.CharField(
        source="encargado.nombre_completo", read_only=True
    )
    autorizado_por_nombre = serializers.CharField(
        source="autorizado_por.nombre_completo", read_only=True
    )

    class Meta:
        model = EncargadoActivo
        fields = [
            "id", "encargado", "encargado_nombre",
            "autorizado_por", "autorizado_por_nombre",
            "desde", "hasta", "motivo", "activo",
        ]

    def validate(self, attrs):
        # Solo puede haber un encargado activo a la vez
        if attrs.get("activo", True):
            existente = EncargadoActivo.objects.filter(activo=True)
            if self.instance:
                existente = existente.exclude(pk=self.instance.pk)
            if existente.exists():
                raise serializers.ValidationError(
                    "Ya existe un encargado activo. Desactívalo primero."
                )
        return attrs


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})


class RolUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["rol"]

    def validate_rol(self, value):
        # Solo ADMIN puede asignar rol ADMIN
        request = self.context.get("request")
        if value == RolSigtic.ADMIN:
            from apps.users.permissions import _get_profile
            profile = _get_profile(request)
            if not profile or profile.rol != RolSigtic.ADMIN:
                raise serializers.ValidationError(
                    "Solo un ADMIN puede asignar el rol ADMIN."
                )
        return value
