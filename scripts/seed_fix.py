"""Completa los datos que fallaron en seed_data.py"""
import datetime
from django.utils import timezone
from datetime import timedelta

from apps.catalogo.models import Consumible
from apps.inventario.models import Dispositivo, DispImpresora
from apps.users.models import UserProfile, RolSigtic
from apps.tickets.models import Ticket, TicketHistorial, TicketDiagnostico

cons_map = {c.nombre: c for c in Consumible.objects.all()}
prof_map = {p.usu_ide_siggo: p for p in UserProfile.objects.all()}
jefe = prof_map.get(-1) or UserProfile.objects.filter(rol=RolSigtic.JEFE_INFO).first()

# ── Fix imp1 (IMP-001) que falló ─────────────────────────────────
imp1 = Dispositivo.objects.filter(cod_inventario='IMP-001').first()
if imp1:
    DispImpresora.objects.get_or_create(dispositivo=imp1, defaults={
        'tipo': 'LASER',
        'ip': '192.168.1.150',
        'nombre_red': 'IMP-LASER-01',
        'consumible': cons_map.get('Toner HP 85A'),
    })
    print('IMP-001 subtabla OK')

# ── Tickets que faltaron ──────────────────────────────────────────
tickets_data = [
    ('IMP-001', prof_map.get(-6), prof_map.get(-3), 'CORRECTIVO', 'La impresora no imprime, se atasca el papel constantemente y emite un pitido.',         'EN_ATENCION',     7),
    ('PC-002',  prof_map.get(-6), None,              'PREVENTIVO', 'Solicito mantenimiento preventivo trimestral del equipo según cronograma.',             'ENVIADO',         5),
    ('PC-003',  prof_map.get(-7), prof_map.get(-2),  'CORRECTIVO', 'El equipo es muy lento al iniciar Windows, tarda más de 10 minutos en cargar.',         'ASIGNADO',        4),
    ('MON-001', prof_map.get(-5), prof_map.get(-3),  'CORRECTIVO', 'El monitor parpadea constantemente y muestra líneas horizontales en la pantalla.',       'EN_MANTENIMIENTO',8),
    ('PC-004',  prof_map.get(-5), prof_map.get(-2),  'CORRECTIVO', 'El teclado no responde varias teclas (A, S, D, F) al presionarlas.',                    'FINALIZADO',     15),
    ('IMP-002', prof_map.get(-7), None,              'CORRECTIVO', 'La impresora matricial no imprime, la cinta está gastada.',                              'ENVIADO',         2),
    ('PC-005',  prof_map.get(-6), prof_map.get(-3),  'CORRECTIVO', 'El equipo se reinicia solo cada cierto tiempo sin motivo aparente.',                    'EN_REVISION',     3),
]

for cod, solicitante, tecnico, tipo, detalle, estado, dias_atras in tickets_data:
    disp_obj = Dispositivo.objects.filter(cod_inventario=cod).first()
    if not disp_obj or not solicitante:
        print(f'  SKIP {cod} — falta dispositivo o solicitante')
        continue
    if Ticket.objects.filter(dispositivo=disp_obj, estado=estado).exists():
        print(f'  SKIP {cod} — ya existe')
        continue

    fecha_creacion = timezone.now() - timedelta(days=dias_atras)
    t = Ticket(
        dispositivo=disp_obj,
        solicitante=solicitante,
        tecnico=tecnico,
        asignado_por=jefe if tecnico else None,
        tipo_mantenimiento=tipo,
        detalle_falla=detalle,
        estado=estado,
        ip_solicitante='192.168.1.101',
        responsable_snapshot=solicitante,
        nombre_responsable_snapshot=solicitante.nombre_completo,
        cargo_responsable_snapshot='Trabajador Municipal',
        fecha_creacion=fecha_creacion,
        fecha_asignacion=fecha_creacion + timedelta(hours=3) if tecnico else None,
        fecha_cierre=timezone.now() - timedelta(days=1) if estado in ('SOLUCIONADO', 'FINALIZADO') else None,
    )
    t.numero = Ticket._generar_numero()
    t.save()

    # Historial (estado_anterior=None para el primer registro)
    pasos = {
        'ENVIADO':          [(None, 'ENVIADO', solicitante, 'Ticket creado.')],
        'EN_REVISION':      [(None, 'ENVIADO', solicitante, 'Ticket creado.'), ('ENVIADO', 'EN_REVISION', jefe, 'En revisión.')],
        'ASIGNADO':         [(None, 'ENVIADO', solicitante, 'Ticket creado.'), ('ENVIADO', 'EN_REVISION', jefe, 'En revisión.'), ('EN_REVISION', 'ASIGNADO', jefe, 'Asignado al técnico.')],
        'EN_ATENCION':      [(None, 'ENVIADO', solicitante, 'Ticket creado.'), ('ENVIADO', 'EN_REVISION', jefe, 'En revisión.'), ('EN_REVISION', 'ASIGNADO', jefe, 'Asignado.'), ('ASIGNADO', 'EN_ATENCION', tecnico or jefe, 'Técnico inicia atención.')],
        'EN_MANTENIMIENTO': [(None, 'ENVIADO', solicitante, 'Ticket creado.'), ('ENVIADO', 'EN_REVISION', jefe, 'En revisión.'), ('EN_REVISION', 'ASIGNADO', jefe, 'Asignado.'), ('ASIGNADO', 'EN_ATENCION', tecnico or jefe, 'En atención.'), ('EN_ATENCION', 'EN_MANTENIMIENTO', tecnico or jefe, 'Requiere mantenimiento mayor.')],
        'FINALIZADO':       [(None, 'ENVIADO', solicitante, 'Ticket creado.'), ('ENVIADO', 'EN_REVISION', jefe, 'En revisión.'), ('EN_REVISION', 'ASIGNADO', jefe, 'Asignado.'), ('ASIGNADO', 'EN_ATENCION', tecnico or jefe, 'En atención.'), ('EN_ATENCION', 'EN_MANTENIMIENTO', tecnico or jefe, 'Mayor.'), ('EN_MANTENIMIENTO', 'FINALIZADO', tecnico or jefe, 'Trabajo finalizado.')],
    }
    for i, (ant, nvo, usr, com) in enumerate(pasos.get(estado, [(None, 'ENVIADO', solicitante, 'Ticket creado.')])):
        TicketHistorial.objects.create(
            ticket=t, usuario=usr,
            estado_anterior=ant, estado_nuevo=nvo,
            comentario=com,
            fecha=fecha_creacion + timedelta(hours=i),
        )
    print(f'  Ticket {t.numero} ({cod} → {estado}) creado con {len(pasos.get(estado,[]))} pasos de historial')

# ── Diagnósticos para tickets existentes ─────────────────────────
diags = [
    ('EN_ATENCION',     'Atasco mecánico de rodillos',  'Rodillos desgastados. Se limpiará y ajustará el mecanismo de arrastre.',            'MENOR', -3),
    ('EN_MANTENIMIENTO','Falla de panel LCD',            'Panel con falla interna. Se enviará a servicio técnico para reemplazo del panel.', 'MAYOR', -3),
    ('FINALIZADO',      'Desgaste físico del teclado',  'Se reemplazó el teclado por uno nuevo del almacén. Funcionando correctamente.',     'MENOR', -2),
]
for est, tipo_falla, detalle_tec, tipo_res, tec_key in diags:
    t_obj = Ticket.objects.filter(estado=est).exclude(diagnostico__isnull=False).first()
    if t_obj:
        TicketDiagnostico.objects.get_or_create(ticket=t_obj, defaults={
            'tipo_falla': tipo_falla,
            'detalle_tecnico': detalle_tec,
            'tipo_resultado': tipo_res,
            'tecnico': prof_map.get(tec_key),
            'fecha_registro': timezone.now() - timedelta(days=2),
        })
        print(f'  Diagnóstico {est} OK')

# ── Resumen final ─────────────────────────────────────────────────
print()
print('=' * 40)
print(f'Tickets totales : {Ticket.objects.count()}')
for est in ['ENVIADO','EN_REVISION','ASIGNADO','EN_ATENCION','EN_MANTENIMIENTO','SOLUCIONADO','FINALIZADO']:
    n = Ticket.objects.filter(estado=est).count()
    if n:
        print(f'  {est:<20} {n}')
print(f'Diagnósticos    : {TicketDiagnostico.objects.count()}')
print(f'Historial total : {TicketHistorial.objects.count()}')
