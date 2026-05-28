from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated

from apps.users.permissions import EsInformatica
from .models import StockConsumible, MovimientoStock
from .serializers import StockConsumibleSerializer, MovimientoStockSerializer


class StockConsumibleListView(ListCreateAPIView):
    serializer_class = StockConsumibleSerializer
    permission_classes = [IsAuthenticated, EsInformatica]

    def get_queryset(self):
        qs = StockConsumible.objects.select_related("consumible", "marca")
        if self.request.query_params.get("bajo_minimo"):
            from django.db.models import F
            qs = qs.filter(stock_actual__lt=F("stock_minimo"))
        return qs


class StockConsumibleDetailView(RetrieveUpdateAPIView):
    serializer_class = StockConsumibleSerializer
    permission_classes = [IsAuthenticated, EsInformatica]
    queryset = StockConsumible.objects.select_related("consumible", "marca")
    http_method_names = ["get", "patch", "head", "options"]


class MovimientoStockListView(ListCreateAPIView):
    serializer_class = MovimientoStockSerializer
    permission_classes = [IsAuthenticated, EsInformatica]

    def get_queryset(self):
        qs = MovimientoStock.objects.select_related(
            "stock_consumible__consumible", "registrado_por", "dispositivo", "ticket"
        )
        params = self.request.query_params
        if params.get("tipo"):
            qs = qs.filter(tipo=params["tipo"].upper())
        if params.get("stock"):
            qs = qs.filter(stock_consumible_id=params["stock"])
        if params.get("ticket"):
            qs = qs.filter(ticket_id=params["ticket"])
        return qs.order_by("-fecha")
