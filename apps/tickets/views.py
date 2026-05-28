from django.utils import timezone
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.permissions import _get_profile, EsInformatica, EsJefeOEncargado
from apps.users.models import UserProfile, EncargadoActivo, RolSigtic
from .models import (
    Ticket, TicketDiagnostico, TicketAccion, TicketHistorial,
    TicketAdjunto, TicketTercerizado, EstadoTicket, TRANSICIONES, ESTADOS_TERMINALES,
)
from .serializers import (
    TicketListSerializer, TicketDetailSerializer, TicketCreateSerializer,
    TicketDiagnosticoSerializer, TicketAccionSerializer,
    TicketTercerizadoSerializer, TransicionSerializer,
    _get_client_ip,
)


class TicketListView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return TicketCreateSerializer
        return TicketListSerializer

    def get_queryset(self):
        profile = _get_profile(self.request)
        qs = Ticket.objects.select_related(
            "dispositivo__tipo_dispositivo", "solicitante", "tecnico"
        )

        # USUARIO solo ve sus propios tickets
        if profile and profile.rol == RolSigtic.USUARIO:
            qs = qs.filter(solicitante=profile)

        params = self.request.query_params
        if params.get("estado"):
            qs = qs.filter(estado=params["estado"].upper())
        if params.get("tecnico"):
            qs = qs.filter(tecnico_id=params["tecnico"])
        if params.get("dispositivo"):
            qs = qs.filter(dispositivo_id=params["dispositivo"])

        return qs.order_by("-fecha_creacion")

    def create(self, request, *args, **kwargs):
        serializer = TicketCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        ticket = serializer.save()

        # Validar IP: si hay computadora con IP distinta → ip_warning
        ip_warning = False
        try:
            comp = ticket.dispositivo.computadora
            ip_solicitante = ticket.ip_solicitante
            if comp.ip and ip_solicitante and str(comp.ip) != ip_solicitante:
                ip_warning = True
        except Exception:
            pass

        data = TicketDetailSerializer(ticket).data
        data["ip_warning"] = ip_warning
        return Response(data, status=status.HTTP_201_CREATED)


class TicketDetailView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TicketDetailSerializer

    def get_queryset(self):
        profile = _get_profile(self.request)
        qs = Ticket.objects.select_related(
            "dispositivo__tipo_dispositivo", "solicitante", "asignado_por", "tecnico",
            "responsable_snapshot", "diagnostico__tecnico",
        ).prefetch_related("acciones__tecnico", "historial__usuario", "adjuntos")

        if profile and profile.rol == RolSigtic.USUARIO:
            qs = qs.filter(solicitante=profile)
        return qs


class TicketTransicionView(APIView):
    """
    POST /tickets/{id}/transicion/
    Valida la transición de estado según el rol del usuario.
    """
    permission_classes = [IsAuthenticated]

    def _get_ticket(self, pk, profile):
        try:
            qs = Ticket.objects.select_related("tecnico", "solicitante", "dispositivo")
            if profile.rol == RolSigtic.USUARIO:
                qs = qs.filter(solicitante=profile)
            return qs.get(pk=pk)
        except Ticket.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound("Ticket no encontrado.")

    def post(self, request, pk):
        profile = _get_profile(request)
        if not profile or not profile.activo:
            return Response({"detail": "Sin acceso."}, status=status.HTTP_403_FORBIDDEN)

        ticket = self._get_ticket(pk, profile)

        serializer = TransicionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        nuevo_estado = serializer.validated_data["nuevo_estado"]
        comentario = serializer.validated_data.get("comentario", "")
        tecnico_id = serializer.validated_data.get("tecnico_id")

        # Validar encargado activo si aplica
        rol = profile.rol
        if rol == RolSigtic.ENCARGADO_INFO:
            enc = EncargadoActivo.get_activo()
            if not enc or enc.encargado_id != profile.pk:
                return Response(
                    {"detail": "No eres el encargado activo actualmente."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        # Validar transición
        clave = (ticket.estado, nuevo_estado)
        roles_permitidos = TRANSICIONES.get(clave, set())
        if rol not in roles_permitidos:
            return Response(
                {
                    "detail": f"Transición '{ticket.estado}' → '{nuevo_estado}' no permitida para tu rol.",
                    "transicion": f"{ticket.estado} → {nuevo_estado}",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        estado_anterior = ticket.estado
        ticket.estado = nuevo_estado

        # Asignación de técnico
        if nuevo_estado == EstadoTicket.ASIGNADO:
            if not tecnico_id:
                return Response(
                    {"detail": "Se requiere tecnico_id para asignar."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                tecnico = UserProfile.objects.get(pk=tecnico_id, rol=RolSigtic.TECNICO, activo=True)
            except UserProfile.DoesNotExist:
                return Response(
                    {"detail": "Técnico no válido o inactivo."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            ticket.tecnico = tecnico
            ticket.asignado_por = profile
            ticket.fecha_asignacion = timezone.now()

        if nuevo_estado == EstadoTicket.EN_ATENCION:
            ticket.fecha_inicio = timezone.now()

        if nuevo_estado in ESTADOS_TERMINALES:
            ticket.fecha_cierre = timezone.now()

        ticket.save()

        TicketHistorial.objects.create(
            ticket=ticket,
            usuario=profile,
            estado_anterior=estado_anterior,
            estado_nuevo=nuevo_estado,
            comentario=comentario,
        )

        return Response(TicketDetailSerializer(ticket).data)


class TicketDiagnosticoView(APIView):
    """POST crea diagnóstico y dispara la transición de estado automática."""
    permission_classes = [IsAuthenticated, EsInformatica]

    def post(self, request, pk):
        profile = _get_profile(request)
        try:
            ticket = Ticket.objects.get(pk=pk, tecnico=profile, estado=EstadoTicket.EN_ATENCION)
        except Ticket.DoesNotExist:
            return Response(
                {"detail": "Ticket no encontrado o no está en tu atención."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if hasattr(ticket, "diagnostico"):
            return Response(
                {"detail": "Este ticket ya tiene diagnóstico."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = TicketDiagnosticoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tipo_resultado = serializer.validated_data["tipo_resultado"]
        diagnostico = serializer.save(ticket=ticket, tecnico=profile)

        # Transición automática según resultado
        estado_anterior = ticket.estado
        if tipo_resultado == TicketDiagnostico.MENOR:
            ticket.estado = EstadoTicket.SOLUCIONADO
            ticket.fecha_cierre = timezone.now()
        elif tipo_resultado == TicketDiagnostico.MAYOR:
            ticket.estado = EstadoTicket.EN_MANTENIMIENTO
        elif tipo_resultado == TicketDiagnostico.TERCERIZADO:
            ticket.estado = EstadoTicket.TERCERIZADO

        ticket.save(update_fields=["estado", "fecha_cierre"])

        TicketHistorial.objects.create(
            ticket=ticket,
            usuario=profile,
            estado_anterior=estado_anterior,
            estado_nuevo=ticket.estado,
            comentario=f"Diagnóstico registrado: {tipo_resultado}",
        )

        return Response(TicketDiagnosticoSerializer(diagnostico).data, status=status.HTTP_201_CREATED)


class TicketAccionView(APIView):
    """Registro de acciones realizadas durante la atención."""
    permission_classes = [IsAuthenticated, EsInformatica]

    def post(self, request, pk):
        profile = _get_profile(request)
        try:
            ticket = Ticket.objects.get(pk=pk, tecnico=profile)
        except Ticket.DoesNotExist:
            return Response({"detail": "Ticket no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        serializer = TicketAccionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(ticket=ticket, tecnico=profile)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TicketTercerizadoView(APIView):
    """Registra o actualiza el info de tercerización."""
    permission_classes = [IsAuthenticated, EsJefeOEncargado]

    def post(self, request, pk):
        profile = _get_profile(request)
        try:
            ticket = Ticket.objects.get(pk=pk, estado=EstadoTicket.TERCERIZADO)
        except Ticket.DoesNotExist:
            return Response({"detail": "Ticket no encontrado o no está en estado TERCERIZADO."}, status=status.HTTP_404_NOT_FOUND)

        if hasattr(ticket, "tercerizado"):
            serializer = TicketTercerizadoSerializer(ticket.tercerizado, data=request.data, partial=True)
        else:
            serializer = TicketTercerizadoSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save(ticket=ticket, registrado_por=profile)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TicketAdjuntoView(APIView):
    """Subir adjunto a un ticket."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        profile = _get_profile(request)
        qs = Ticket.objects.all()
        if profile.rol == RolSigtic.USUARIO:
            qs = qs.filter(solicitante=profile)
        try:
            ticket = qs.get(pk=pk)
        except Ticket.DoesNotExist:
            return Response({"detail": "Ticket no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        archivo = request.FILES.get("archivo")
        if not archivo:
            return Response({"detail": "Se requiere archivo."}, status=status.HTTP_400_BAD_REQUEST)

        adjunto = TicketAdjunto.objects.create(
            ticket=ticket,
            archivo=archivo,
            nombre_original=archivo.name,
        )
        return Response({"id": adjunto.id, "nombre_original": adjunto.nombre_original}, status=status.HTTP_201_CREATED)
