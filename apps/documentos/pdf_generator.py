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


# ── PDF de Traslado ───────────────────────────────────────────────────────────

def generar_pdf_traslado(traslado) -> bytes:
    """
    Genera el Acta de Traslado de Bien Informático en PDF.
    Incluye sección de firmas para entrega/recepción.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=f"Acta de Traslado {traslado.numero}",
    )

    styles = getSampleStyleSheet()
    s_titulo = ParagraphStyle("tit", parent=styles["Heading1"], fontSize=13,
                               textColor=AZUL_INSTITUCIONAL, spaceAfter=2, alignment=1)
    s_sub    = ParagraphStyle("sub", parent=styles["Heading2"], fontSize=10,
                               textColor=AZUL_CLARO, spaceBefore=10, spaceAfter=4)
    s_normal = ParagraphStyle("nor", parent=styles["Normal"], fontSize=9)
    s_firma  = ParagraphStyle("fir", parent=styles["Normal"], fontSize=8,
                               alignment=1, textColor=colors.darkgrey)
    s_pie    = ParagraphStyle("pie", parent=styles["Normal"], fontSize=7,
                               textColor=colors.gray)

    def _n(obj, attr="nombre"):
        """Retorna el atributo del objeto o '—'."""
        return getattr(obj, attr, None) or "—" if obj else "—"

    story = []

    # ── Encabezado ────────────────────────────────────────────────
    story.append(Paragraph("MUNICIPALIDAD DISTRITAL", s_titulo))
    story.append(Paragraph("Unidad de Informática y Sistemas", s_titulo))
    story.append(HRFlowable(width="100%", thickness=2, color=AZUL_INSTITUCIONAL))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("ACTA DE TRASLADO DE BIEN INFORMÁTICO", s_titulo))
    story.append(Spacer(1, 0.4 * cm))

    # ── Datos del traslado ────────────────────────────────────────
    fecha_sol = traslado.fecha_solicitud.strftime("%d/%m/%Y %H:%M") if traslado.fecha_solicitud else "—"
    fecha_apr = traslado.fecha_aprobacion.strftime("%d/%m/%Y") if traslado.fecha_aprobacion else "—"
    fecha_eje = traslado.fecha_ejecucion.strftime("%d/%m/%Y") if traslado.fecha_ejecucion else "—"

    datos_trl = [
        ["N° Traslado", traslado.numero,        "Estado", traslado.get_estado_display()],
        ["Fecha solicitud", fecha_sol,           "Fecha aprobación", fecha_apr],
        ["Fecha ejecución", fecha_eje,           "Solicitado por", _n(traslado.solicitado_por, "nombre_completo")],
    ]
    t = Table(datos_trl, colWidths=[3.5 * cm, 6 * cm, 3.5 * cm, 4 * cm])
    t.setStyle(_estilo_tabla_info())
    story.append(t)
    story.append(Spacer(1, 0.5 * cm))

    # ── Datos del dispositivo ─────────────────────────────────────
    story.append(Paragraph("Bien Informático", s_sub))
    disp = traslado.dispositivo
    datos_disp = [
        ["Código inventario", disp.cod_inventario,             "Tipo",    disp.tipo_dispositivo.nombre],
        ["Marca",            _n(disp.marca),                   "Modelo",  disp.modelo or "—"],
        ["Serie",            disp.serie or "—",                "Estado",  disp.get_estado_display()],
    ]
    t2 = Table(datos_disp, colWidths=[3.5 * cm, 6 * cm, 3.5 * cm, 4 * cm])
    t2.setStyle(_estilo_tabla_info())
    story.append(t2)
    story.append(Spacer(1, 0.5 * cm))

    # ── Tabla Origen → Destino ────────────────────────────────────
    story.append(Paragraph("Detalle del Traslado", s_sub))
    tabla_od = [
        ["",                 "ORIGEN",                                    "DESTINO"],
        ["Sede",             _n(traslado.sede_origen),                    _n(traslado.sede_destino)],
        ["Área / Unidad",    _n(traslado.area_origen),                    _n(traslado.area_destino)],
        ["Subgerencia",      _n(traslado.subger_origen),                  _n(traslado.subger_destino)],
        ["Dependencia",      _n(traslado.depend_origen),                  _n(traslado.depend_destino)],
        ["Responsable",      _n(traslado.responsable_origen, "nombre_completo"),
                             _n(traslado.responsable_destino, "nombre_completo")],
    ]
    t_od = Table(tabla_od, colWidths=[3.5 * cm, 8 * cm, 5.5 * cm])
    t_od.setStyle(TableStyle([
        # Encabezado
        ("BACKGROUND",  (0, 0), (-1, 0),  AZUL_INSTITUCIONAL),
        ("TEXTCOLOR",   (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",    (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("ALIGN",       (1, 0), (-1, 0),  "CENTER"),
        # Columna etiquetas
        ("BACKGROUND",  (0, 1), (0, -1),  GRIS_FONDO),
        ("FONTNAME",    (0, 1), (0, -1),  "Helvetica-Bold"),
        # Colores alternos
        ("ROWBACKGROUNDS", (1, 1), (-1, -1), [colors.white, colors.HexColor("#EBF3FB")]),
        ("FONTSIZE",    (0, 0), (-1, -1),  8),
        ("GRID",        (0, 0), (-1, -1),  0.5, colors.lightgrey),
        ("VALIGN",      (0, 0), (-1, -1),  "MIDDLE"),
        ("PADDING",     (0, 0), (-1, -1),  5),
        # Fila vacía (0,0) → celda en blanco
        ("TEXTCOLOR",   (0, 0), (0, 0),   AZUL_INSTITUCIONAL),
    ]))
    story.append(t_od)
    story.append(Spacer(1, 0.5 * cm))

    # ── Motivo ────────────────────────────────────────────────────
    story.append(Paragraph("Motivo del traslado", s_sub))
    story.append(Paragraph(traslado.motivo or "—", s_normal))
    if traslado.observacion:
        story.append(Spacer(1, 0.2 * cm))
        story.append(Paragraph(f"<b>Observaciones:</b> {traslado.observacion}", s_normal))
    story.append(Spacer(1, 0.8 * cm))

    # ── Firmas ────────────────────────────────────────────────────
    story.append(Paragraph("Conformidad y firmas", s_sub))
    story.append(Spacer(1, 0.3 * cm))

    resp_origen_nombre  = _n(traslado.responsable_origen, "nombre_completo")
    resp_destino_nombre = _n(traslado.responsable_destino, "nombre_completo")
    aprobado_nombre     = _n(traslado.aprobado_por, "nombre_completo")

    _linea = "_" * 30
    firma_data = [
        [
            Paragraph(f"{_linea}<br/><b>ENTREGADO POR</b><br/>{resp_origen_nombre}<br/>{_n(traslado.sede_origen)}", s_firma),
            Paragraph(f"{_linea}<br/><b>RECIBIDO POR</b><br/>{resp_destino_nombre}<br/>{_n(traslado.sede_destino)}", s_firma),
            Paragraph(f"{_linea}<br/><b>V°B° JEFE DE INFORMÁTICA</b><br/>{aprobado_nombre}", s_firma),
        ]
    ]
    t_firma = Table(firma_data, colWidths=[5.5 * cm, 5.5 * cm, 6 * cm])
    t_firma.setStyle(TableStyle([
        ("VALIGN",  (0, 0), (-1, -1), "TOP"),
        ("ALIGN",   (0, 0), (-1, -1), "CENTER"),
        ("PADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(t_firma)

    # ── Pie de página ─────────────────────────────────────────────
    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=AZUL_CLARO))
    story.append(Spacer(1, 0.15 * cm))
    story.append(
        Paragraph(
            f"Documento generado el {timezone.localtime().strftime('%d/%m/%Y %H:%M')} — Sistema SIGTIC",
            s_pie,
        )
    )

    doc.build(story)
    return buffer.getvalue()
