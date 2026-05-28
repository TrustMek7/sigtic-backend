from rest_framework import serializers
from .models import Marca, TipoDispositivo, SistemaOperativo, Procesador, MemoriaRam, Consumible


class MarcaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marca
        fields = ["id", "nombre"]


class TipoDispositivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoDispositivo
        fields = ["id", "codigo", "nombre", "tiene_subtabla"]


class SistemaOperativoSerializer(serializers.ModelSerializer):
    class Meta:
        model = SistemaOperativo
        fields = ["id", "nombre"]


class ProcesadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Procesador
        fields = ["id", "nombre"]


class MemoriaRamSerializer(serializers.ModelSerializer):
    class Meta:
        model = MemoriaRam
        fields = ["id", "capacidad"]


class ConsumibleSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)

    class Meta:
        model = Consumible
        fields = ["id", "nombre", "tipo", "tipo_display"]
