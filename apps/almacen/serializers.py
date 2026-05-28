from rest_framework import serializers
from .models import StockConsumible, MovimientoStock


class StockConsumibleSerializer(serializers.ModelSerializer):
    consumible_nombre = serializers.CharField(source="consumible.nombre", read_only=True)
    consumible_tipo = serializers.CharField(source="consumible.tipo", read_only=True)
    marca_nombre = serializers.CharField(source="marca.nombre", read_only=True, default="")
    bajo_minimo = serializers.BooleanField(read_only=True)

    class Meta:
        model = StockConsumible
        fields = [
            "id", "consumible", "consumible_nombre", "consumible_tipo",
            "marca", "marca_nombre", "stock_actual", "stock_minimo",
            "bajo_minimo", "orden_compra", "costo_unitario",
            "fecha_actualizacion", "observaciones",
        ]
        read_only_fields = ["stock_actual", "fecha_actualizacion"]


class MovimientoStockSerializer(serializers.ModelSerializer):
    registrado_por_nombre = serializers.CharField(
        source="registrado_por.nombre_completo", read_only=True
    )
    consumible_nombre = serializers.CharField(
        source="stock_consumible.consumible.nombre", read_only=True
    )

    class Meta:
        model = MovimientoStock
        fields = [
            "id", "stock_consumible", "consumible_nombre",
            "tipo", "cantidad", "dispositivo", "ticket",
            "registrado_por", "registrado_por_nombre",
            "fecha", "referencia", "observacion",
        ]
        read_only_fields = ["registrado_por", "fecha"]

    def validate(self, attrs):
        if attrs.get("tipo") == MovimientoStock.SALIDA:
            stock = attrs.get("stock_consumible")
            if stock and attrs.get("cantidad", 0) > stock.stock_actual:
                raise serializers.ValidationError(
                    {"cantidad": f"Stock insuficiente. Disponible: {stock.stock_actual}"}
                )
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        from apps.users.permissions import _get_profile
        validated_data["registrado_por"] = _get_profile(request)
        return super().create(validated_data)
