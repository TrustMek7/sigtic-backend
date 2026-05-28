from django.urls import path
from .views import (
    TicketListView, TicketDetailView,
    TicketTransicionView, TicketDiagnosticoView,
    TicketAccionView, TicketTercerizadoView, TicketAdjuntoView,
)

urlpatterns = [
    # Included under api/v1/tickets/
    path("", TicketListView.as_view(), name="ticket-list"),
    path("<int:pk>/", TicketDetailView.as_view(), name="ticket-detail"),
    path("<int:pk>/transicion/", TicketTransicionView.as_view(), name="ticket-transicion"),
    path("<int:pk>/diagnostico/", TicketDiagnosticoView.as_view(), name="ticket-diagnostico"),
    path("<int:pk>/acciones/", TicketAccionView.as_view(), name="ticket-accion"),
    path("<int:pk>/tercerizado/", TicketTercerizadoView.as_view(), name="ticket-tercerizado"),
    path("<int:pk>/adjuntos/", TicketAdjuntoView.as_view(), name="ticket-adjunto"),
]
