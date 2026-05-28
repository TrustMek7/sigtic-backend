from rest_framework import serializers
from .models import Sede, UnidadOrganica, Subgerencia, Dependencia


class SedeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sede
        fields = ["id", "nombre", "direccion", "sed_ide_siggo"]


class DependenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dependencia
        fields = ["id", "nombre", "subgerencia"]


class SubgerenciaSerializer(serializers.ModelSerializer):
    dependencias = DependenciaSerializer(many=True, read_only=True)

    class Meta:
        model = Subgerencia
        fields = ["id", "nombre", "unidad_organica", "dependencias"]


class UnidadOrganicaSerializer(serializers.ModelSerializer):
    subgerencias = SubgerenciaSerializer(many=True, read_only=True)

    class Meta:
        model = UnidadOrganica
        fields = ["id", "nombre", "abreviatura", "nivel", "superior", "uni_ide_siggo", "subgerencias"]


class UnidadOrganicaFlatSerializer(serializers.ModelSerializer):
    """Versión sin anidación para dropdowns."""
    class Meta:
        model = UnidadOrganica
        fields = ["id", "nombre", "abreviatura", "nivel", "superior"]
