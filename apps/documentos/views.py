import os
from django.core.files.base import ContentFile
from django.http import FileResponse
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer
from rest_framework import serializers as drf_serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.permissions import _get_profile, EsJefeOEncargado
from apps.tickets.models import Ticket, EstadoTicket
from .models import DocumentoOficial
from .pdf_generator import generar_pdf_ticket

ESTADOS_GENERABLES = {EstadoTicket.SOLUCIONADO, EstadoTicket.FINALIZADO}


@extend_schema(
    tags=["Documentos"],
    request=None,
    responses={
        200: inline_serializer("DocumentoGenerado", {"url": drf_serializers.URLField(), "numero_documento": drf_serializers.CharField()}),
        400: OpenApiResponse(description="Ticket no está en estado terminal."),
        404: OpenApiResponse(description="Ticket no encontrado."),
    },
    summary="Genera o recupera el PDF oficial del ticket",
)
class GenerarDocumentoView(APIView):
    """
    POST /tickets/{id}/documento/
    Genera PDF del ticket (solo en estado SOLUCIONADO o FINALIZADO).
    Si ya existe, lo reutiliza.
    """
    permission_classes = [IsAuthenticated, EsJefeOEncargado]

    def post(self, request, pk):
        profile = _get_profile(request)
        try:
            ticket = Ticket.objects.select_related(
                "dispositivo__tipo_dispositivo", "dispositivo__marca",
                "solicitante", "tecnico", "diagnostico__tecnico",
            ).prefetch_related("historial__usuario", "acciones__tecnico").get(pk=pk)
        except Ticket.DoesNotExist:
            return Response({"detail": "Ticket no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        if ticket.estado not in ESTADOS_GENERABLES:
            return Response(
                {"detail": f"Solo se generan documentos para tickets SOLUCIONADO o FINALIZADO. Estado actual: {ticket.estado}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Reutilizar si ya existe
        if hasattr(ticket, "documento_oficial"):
            doc = ticket.documento_oficial
        else:
            pdf_bytes = generar_pdf_ticket(ticket)
            numero_doc = f"DOC-{ticket.numero}-{timezone.now().strftime('%Y%m%d')}"

            doc = DocumentoOficial(
                ticket=ticket,
                numero_documento=numero_doc,
                generado_por=profile,
            )
            doc.archivo_pdf.save(
                f"{numero_doc}.pdf",
                ContentFile(pdf_bytes),
                save=True,
            )

        return Response({
            "id": doc.id,
            "numero_documento": doc.numero_documento,
            "fecha_generacion": doc.fecha_generacion,
            "url": request.build_absolute_uri(doc.archivo_pdf.url),
        })


@extend_schema(
    tags=["Documentos"],
    responses={200: OpenApiResponse(description="Archivo PDF (application/pdf).")},
    summary="Descarga el PDF oficial del ticket",
)
class DescargarDocumentoView(APIView):
    """
    GET /documentos/{id}/descargar/
    Descarga el PDF como adjunto.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            doc = DocumentoOficial.objects.select_related("ticket").get(pk=pk)
        except DocumentoOficial.DoesNotExist:
            return Response({"detail": "Documento no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        return FileResponse(
            doc.archivo_pdf.open("rb"),
            as_attachment=True,
            filename=os.path.basename(doc.archivo_pdf.name),
            content_type="application/pdf",
        )
