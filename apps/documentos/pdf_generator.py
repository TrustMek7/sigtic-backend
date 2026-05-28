"""
Generador de PDF para documentos oficiales de tickets.
Usa datos del snapshot guardado en el ticket, nunca datos en tiempo real.
"""
import io
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)


_W, _H = A4
AZUL_INSTITUCIONAL = colors.HexColor("#1F4E79")
AZUL_CLARO = colors.HexColor("#2E75B6")
GRIS_FONDO = colors.HexColor("#F2F2F2")


def generar_pdf_ticket(ticket) -> bytes:
    """
    Genera el PDF del ticket usando los datos de snapshot.
    Retorna bytes del PDF.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=f"Ticket {ticket.numero}",
    )

    styles = getSampleStyleSheet()
    style_titulo = ParagraphStyle(
        "titulo",
        parent=styles["Heading1"],
        fontSize=14,
        textColor=AZUL_INSTITUCIONAL,
        spaceAfter=4,
    )
    style_subtitulo = ParagraphStyle(
        "subtitulo",
        parent=styles["Heading2"],
        fontSize=11,
        textColor=AZUL_CLARO,
        spaceBefore=10,
        spaceAfter=4,
    )
    style_normal = styles["Normal"]
    style_normal.fontSize = 9

    story = []

    # Encabezado
    story.append(Paragraph("MUNICIPALIDAD", style_titulo))
    story.append(Paragraph("Unidad de Informática y Sistemas", style_subtitulo))
    story.append(HRFlowable(width="100%", thickness=2, color=AZUL_INSTITUCIONAL))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph(f"<b>REPORTE DE TICKET DE MANTENIMIENTO</b>", style_subtitulo))
    story.append(Spacer(1, 0.3 * cm))

    # Datos del ticket
    datos_ticket = [
        ["N° Ticket", ticket.numero, "Estado", ticket.get_estado_display()],
        ["Tipo", ticket.get_tipo_mantenimiento_display(), "Fecha creación",
         ticket.fecha_creacion.strftime("%d/%m/%Y %H:%M") if ticket.fecha_creacion else "—"],
        ["Fecha cierre",
         ticket.fecha_cierre.strftime("%d/%m/%Y %H:%M") if ticket.fecha_cierre else "—",
         "", ""],
    ]
    t_ticket = Table(datos_ticket, colWidths=[3.5 * cm, 6 * cm, 3.5 * cm, 4 * cm])
    t_ticket.setStyle(_estilo_tabla_info())
    story.append(t_ticket)
    story.append(Spacer(1, 0.5 * cm))

    # Dispositivo
    story.append(Paragraph("Dispositivo", style_subtitulo))
    disp = ticket.dispositivo
    datos_disp = [
        ["Código inventario", disp.cod_inventario, "Tipo", disp.tipo_dispositivo.nombre],
        ["Marca", disp.marca.nombre if disp.marca else "—", "Modelo", disp.modelo or "—"],
        ["Serie", disp.serie or "—", "Estado", disp.get_estado_display()],
    ]
    story.append(Table(datos_disp, colWidths=[3.5 * cm, 6 * cm, 3.5 * cm, 4 * cm]))
    story[-1].setStyle(_estilo_tabla_info())
    story.append(Spacer(1, 0.5 * cm))

    # Responsable (snapshot — nunca cambia)
    story.append(Paragraph("Responsable al momento del reporte", style_subtitulo))
    datos_resp = [
        ["Nombre", ticket.nombre_responsable_snapshot or "—"],
        ["Cargo", ticket.cargo_responsable_snapshot or "—"],
    ]
    story.append(Table(datos_resp, colWidths=[3.5 * cm, 13.5 * cm]))
    story[-1].setStyle(_estilo_tabla_info())
    story.append(Spacer(1, 0.5 * cm))

    # Solicitante
    story.append(Paragraph("Solicitante", style_subtitulo))
    datos_sol = [
        ["Nombre", ticket.solicitante.nombre_completo],
        ["DNI", ticket.solicitante.dni or "—"],
    ]
    story.append(Table(datos_sol, colWidths=[3.5 * cm, 13.5 * cm]))
    story[-1].setStyle(_estilo_tabla_info())
    story.append(Spacer(1, 0.5 * cm))

    # Detalle de la falla
    story.append(Paragraph("Descripción de la falla", style_subtitulo))
    story.append(Paragraph(ticket.detalle_falla or "—", style_normal))
    story.append(Spacer(1, 0.5 * cm))

    # Diagnóstico (si existe)
    try:
        diag = ticket.diagnostico
        story.append(Paragraph("Diagnóstico técnico", style_subtitulo))
        datos_diag = [
            ["Tipo de falla", diag.tipo_falla or "—"],
            ["Resultado", diag.get_tipo_resultado_display()],
            ["Tiempo estimado", diag.tiempo_estimado or "—"],
            ["Técnico", diag.tecnico.nombre_completo],
        ]
        story.append(Table(datos_diag, colWidths=[3.5 * cm, 13.5 * cm]))
        story[-1].setStyle(_estilo_tabla_info())
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph("<b>Detalle técnico:</b>", style_normal))
        story.append(Paragraph(diag.detalle_tecnico or "—", style_normal))
        story.append(Spacer(1, 0.5 * cm))
    except Exception:
        pass

    # Técnico asignado
    if ticket.tecnico:
        story.append(Paragraph("Técnico asignado", style_subtitulo))
        story.append(Paragraph(ticket.tecnico.nombre_completo, style_normal))
        story.append(Spacer(1, 0.5 * cm))

    # Historial de estados
    historial = list(ticket.historial.select_related("usuario").order_by("fecha"))
    if historial:
        story.append(Paragraph("Historial de estados", style_subtitulo))
        filas = [["Fecha", "Usuario", "Estado anterior", "Estado nuevo", "Comentario"]]
        for h in historial:
            filas.append([
                h.fecha.strftime("%d/%m/%Y %H:%M"),
                h.usuario.nombre_completo,
                h.estado_anterior or "—",
                h.estado_nuevo,
                (h.comentario[:60] + "...") if len(h.comentario) > 60 else (h.comentario or "—"),
            ])
        t_hist = Table(filas, colWidths=[3 * cm, 4 * cm, 3 * cm, 3 * cm, 4 * cm])
        t_hist.setStyle(_estilo_tabla_historial())
        story.append(t_hist)
        story.append(Spacer(1, 0.5 * cm))

    # Pie de página con fecha de generación
    story.append(HRFlowable(width="100%", thickness=1, color=AZUL_CLARO))
    story.append(Spacer(1, 0.2 * cm))
    story.append(
        Paragraph(
            f"Documento generado el {timezone.localtime().strftime('%d/%m/%Y %H:%M')} — Sistema SIGTIC",
            ParagraphStyle("pie", parent=style_normal, fontSize=7, textColor=colors.gray),
        )
    )

    doc.build(story)
    return buffer.getvalue()


def _estilo_tabla_info():
    return TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), GRIS_FONDO),
        ("BACKGROUND", (2, 0), (2, -1), GRIS_FONDO),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#F9F9F9")]),
        ("PADDING", (0, 0), (-1, -1), 4),
    ])


def _estilo_tabla_historial():
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL_INSTITUCIONAL),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS_FONDO]),
        ("PADDING", (0, 0), (-1, -1), 3),
    ])
