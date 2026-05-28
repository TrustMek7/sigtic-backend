"""
Script de datos de prueba para SIGTIC.
Ejecutar: python manage.py shell --settings=config.settings.development < scripts/seed_data.py
"""
import datetime
from django.utils import timezone
from datetime import timedelta

# ── Catálogo ──────────────────────────────────────────────────────
from apps.catalogo.models import TipoDispositivo, Marca, SistemaOperativo, Procesador, MemoriaRam, Consumible

tipos = [
    ('COMPUTADORA', 'Computadora', True),
    ('IMPRESORA',   'Impresora',   True),
    ('MONITOR',     'Monitor',     True),
    ('PERIFERICO',  'Periférico',  True),
    ('RED',         'Equipo de Red', True),
    ('CAMARA',      'Cámara',      True),
    ('TELEFONO',    'Teléfono IP', True),
]
tipo_map = {}
for cod, nom, sub in tipos:
    t, _ = TipoDispositivo.objects.get_or_create(codigo=cod, defaults={'nombre': nom, 'tiene_subtabla': sub})
    tipo_map[cod] = t

marcas = ['HP', 'Dell', 'Lenovo', 'EPSON', 'Canon', 'Cisco', 'TP-Link', 'Hikvision', 'Samsung', 'LG', 'Logitech', 'Asus']
marca_map = {}
for m in marcas:
    obj, _ = Marca.objects.get_or_create(nombre=m)
    marca_map[m] = obj

sos = ['Windows 10 Pro', 'Windows 11 Pro', 'Windows 7 Pro', 'Ubuntu 22.04', 'Sin SO']
so_map = {}
for s in sos:
    obj, _ = SistemaOperativo.objects.get_or_create(nombre=s)
    so_map[s] = obj

procs = ['Intel Core i3', 'Intel Core i5', 'Intel Core i7', 'AMD Ryzen 5', 'AMD Ryzen 7', 'Intel Celeron']
proc_map = {}
for p in procs:
    obj, _ = Procesador.objects.get_or_create(nombre=p)
    proc_map[p] = obj

rams = ['2 GB', '4 GB', '8 GB', '16 GB', '32 GB']
ram_map = {}
for r in rams:
    obj, _ = MemoriaRam.objects.get_or_create(capacidad=r)
    ram_map[r] = obj

consumibles_data = [
    ('Toner HP 85A',      'TONER'),
    ('Toner HP 78A',      'TONER'),
    ('Toner EPSON T664',  'TINTA'),
    ('Cinta Epson LX-350','RIBBON'),
    ('Papel A4 75gr',     'PAPEL'),
]
cons_map = {}
for nom, tipo in consumibles_data:
    obj, _ = Consumible.objects.get_or_create(nombre=nom, defaults={'tipo': tipo})
    cons_map[nom] = obj

print('Catálogo OK')

# ── Organización ──────────────────────────────────────────────────
from apps.organizacion.models import Sede, UnidadOrganica, Subgerencia, Dependencia

sede1, _ = Sede.objects.get_or_create(nombre='Sede Central', defaults={'direccion': 'Av. Principal 123'})
sede2, _ = Sede.objects.get_or_create(nombre='Sede Norte',   defaults={'direccion': 'Jr. Los Pinos 456'})

uni1, _ = UnidadOrganica.objects.get_or_create(nombre='Gerencia Municipal',       defaults={'abreviatura': 'GM', 'nivel': 1})
uni2, _ = UnidadOrganica.objects.get_or_create(nombre='Unidad de Informática',    defaults={'abreviatura': 'UI', 'nivel': 2, 'superior': uni1})
uni3, _ = UnidadOrganica.objects.get_or_create(nombre='Gerencia de Administración', defaults={'abreviatura': 'GA', 'nivel': 1})

sub1, _ = Subgerencia.objects.get_or_create(nombre='Subgerencia de Sistemas', defaults={'unidad_organica': uni2})
sub2, _ = Subgerencia.objects.get_or_create(nombre='Subgerencia de Soporte',  defaults={'unidad_organica': uni2})

Dependencia.objects.get_or_create(nombre='Mesa de Ayuda',  defaults={'subgerencia': sub2})
Dependencia.objects.get_or_create(nombre='Desarrollo Web', defaults={'subgerencia': sub1})

print('Organización OK')

# ── Usuarios (UserProfile) ────────────────────────────────────────
from apps.users.models import UserProfile, RolSigtic

perfiles = [
    (-1, 'Juan Pérez López',     'jperez',  RolSigtic.JEFE_INFO,      '43210001'),
    (-2, 'María García Ríos',    'mgarcia', RolSigtic.TECNICO,        '43210002'),
    (-3, 'Carlos Torres Vega',   'ctorres', RolSigtic.TECNICO,        '43210003'),
    (-4, 'Ana Flores Mendoza',   'aflores', RolSigtic.ENCARGADO_INFO, '43210004'),
    (-5, 'Luis Ramos Chávez',    'lramos',  RolSigtic.USUARIO,        '43210005'),
    (-6, 'Rosa Díaz Paredes',    'rdiaz',   RolSigtic.USUARIO,        '43210006'),
    (-7, 'Pedro Quispe Mamani',  'pquispe', RolSigtic.USUARIO,        '43210007'),
]
prof_map = {}
for uid, nombre, usu, rol, dni in perfiles:
    p, _ = UserProfile.objects.get_or_create(
        usu_ide_siggo=uid,
        defaults={
            'per_ide_siggo': 0,
            'dni': dni,
            'nombre_completo': nombre,
            'email': f'{usu}@muni.gob.pe',
            'rol': rol,
            'activo': True,
            'sede': sede1,
        },
    )
    prof_map[uid] = p

jefe = prof_map[-1]
print('Usuarios OK')

# ── Inventario ────────────────────────────────────────────────────
from apps.inventario.models import (
    Dispositivo, DispComputadora, DispImpresora,
    DispMonitor, DispPeriferico, DispRed,
)

def make_disp(cod, tipo_cod, marca_nom, modelo, serie, sede, responsable, estado='OPERATIVO'):
    obj, _ = Dispositivo.objects.get_or_create(
        cod_inventario=cod,
        defaults={
            'tipo_dispositivo': tipo_map[tipo_cod],
            'marca': marca_map.get(marca_nom),
            'modelo': modelo,
            'serie': serie,
            'estado': estado,
            'sede': sede,
            'responsable': responsable,
            'activo': True,
            'fecha_registro': datetime.date(2024, 1, 15),
        },
    )
    return obj

pc1 = make_disp('PC-001', 'COMPUTADORA', 'HP',     'HP ProBook 450',       'SN-HP-001', sede1, prof_map[-5])
pc2 = make_disp('PC-002', 'COMPUTADORA', 'Dell',   'Dell OptiPlex 7090',   'SN-DL-001', sede1, prof_map[-6])
pc3 = make_disp('PC-003', 'COMPUTADORA', 'Lenovo', 'Lenovo ThinkCentre',   'SN-LN-001', sede2, prof_map[-7])
pc4 = make_disp('PC-004', 'COMPUTADORA', 'HP',     'HP EliteBook 840',     'SN-HP-002', sede1, prof_map[-5], 'EN_MANTENIMIENTO')
pc5 = make_disp('PC-005', 'COMPUTADORA', 'Asus',   'Asus ExpertCenter D5', 'SN-AS-001', sede2, prof_map[-6])

computadoras = [
    (pc1, '192.168.1.101', 'PC-RECEPCION', 'Windows 10 Pro',  'Intel Core i5', '8 GB'),
    (pc2, '192.168.1.102', 'PC-ADMIN',     'Windows 11 Pro',  'Intel Core i7', '16 GB'),
    (pc3, '192.168.1.201', 'PC-NORTE',     'Windows 10 Pro',  'Intel Core i3', '4 GB'),
    (pc4, '192.168.1.103', 'PC-JEFE',      'Windows 11 Pro',  'Intel Core i7', '16 GB'),
    (pc5, '192.168.1.202', 'PC-NORTE2',    'Windows 10 Pro',  'Intel Core i5', '8 GB'),
]
for pc, ip, nombre_eq, so, proc, ram in computadoras:
    DispComputadora.objects.get_or_create(
        dispositivo=pc,
        defaults={
            'sistema_operativo': so_map[so],
            'procesador': proc_map[proc],
            'memoria_ram': ram_map[ram],
            'almacenamiento': '500GB SSD',
            'ip': ip,
            'mac': f'AA:BB:CC:{pc.id:02X}:00:01',
            'nombre_equipo': nombre_eq,
            'dominio': 'muni.local',
            'tipo_pc': 'DESKTOP',
            'licencia_windows': True,
            'licencia_office': True,
            'antivirus': True,
        },
    )

imp1 = make_disp('IMP-001', 'IMPRESORA', 'HP',    'HP LaserJet Pro M404', 'SN-IMP-001', sede1, prof_map[-6])
imp2 = make_disp('IMP-002', 'IMPRESORA', 'EPSON', 'Epson LX-350',         'SN-IMP-002', sede1, prof_map[-7])
imp3 = make_disp('IMP-003', 'IMPRESORA', 'Canon', 'Canon MF3010',         'SN-IMP-003', sede2, prof_map[-5])

DispImpresora.objects.get_or_create(imp1.pk and imp1, dispositivo=imp1, defaults={
    'tipo': 'LASER', 'ip': '192.168.1.150',
    'nombre_red': 'IMP-LASER-01',
    'consumible': cons_map['Toner HP 85A'],
})
DispImpresora.objects.get_or_create(dispositivo=imp2, defaults={
    'tipo': 'MATRICIAL', 'nombre_red': 'IMP-MAT-01',
    'consumible': cons_map['Cinta Epson LX-350'],
})
DispImpresora.objects.get_or_create(dispositivo=imp3, defaults={
    'tipo': 'LASER', 'nombre_red': 'IMP-LASER-02',
    'consumible': cons_map['Toner HP 78A'],
})

mon1 = make_disp('MON-001', 'MONITOR', 'Samsung', 'Samsung S24F350', 'SN-MON-001', sede1, prof_map[-5])
mon2 = make_disp('MON-002', 'MONITOR', 'LG',      'LG 22MK430',     'SN-MON-002', sede1, prof_map[-6])
DispMonitor.objects.get_or_create(dispositivo=mon1, defaults={'tamanio_pulgadas': 24, 'resolucion': '1920x1080', 'tipo_panel': 'IPS', 'conexion': 'HDMI'})
DispMonitor.objects.get_or_create(dispositivo=mon2, defaults={'tamanio_pulgadas': 22, 'resolucion': '1920x1080', 'tipo_panel': 'TN',  'conexion': 'HDMI'})

per1 = make_disp('PER-001', 'PERIFERICO', 'Logitech', 'Logitech MK270', 'SN-PER-001', sede1, prof_map[-5])
per2 = make_disp('PER-002', 'PERIFERICO', 'Logitech', 'Logitech M100',  'SN-PER-002', sede1, prof_map[-6])
DispPeriferico.objects.get_or_create(dispositivo=per1, defaults={'subtipo': 'TECLADO', 'conexion': 'USB'})
DispPeriferico.objects.get_or_create(dispositivo=per2, defaults={'subtipo': 'MOUSE',   'conexion': 'USB'})

red1 = make_disp('RED-001', 'RED', 'Cisco',    'Cisco SG350-28',   'SN-RED-001', sede1, prof_map[-1])
red2 = make_disp('RED-002', 'RED', 'TP-Link',  'TP-Link TL-SF1024','SN-RED-002', sede2, prof_map[-1])
DispRed.objects.get_or_create(dispositivo=red1, defaults={'subtipo': 'SWITCH', 'ip': '192.168.1.1',   'nombre_red': 'SW-PRINCIPAL', 'puertos': 28})
DispRed.objects.get_or_create(dispositivo=red2, defaults={'subtipo': 'SWITCH', 'ip': '192.168.2.1',   'nombre_red': 'SW-NORTE',     'puertos': 24})

print('Inventario OK')

# ── Almacén ───────────────────────────────────────────────────────
from apps.almacen.models import StockConsumible, MovimientoStock

stocks_data = [
    ('Toner HP 85A',       'HP',    25, 5,  'OC-2024-001', 45.50),
    ('Toner HP 78A',       'HP',    10, 3,  'OC-2024-001', 38.00),
    ('Toner EPSON T664',   'EPSON',  8, 2,  'OC-2024-002', 22.00),
    ('Cinta Epson LX-350', 'EPSON', 15, 4,  'OC-2024-002', 12.00),
    ('Papel A4 75gr',      None,     3, 5,  'OC-2024-003',  8.50),
]
stock_map = {}
admin_prof = UserProfile.objects.filter(rol=RolSigtic.ADMIN).first() or jefe

for nom, marca_nom, qty, minimo, oc, costo in stocks_data:
    s, created = StockConsumible.objects.get_or_create(
        consumible=cons_map[nom],
        defaults={
            'marca': marca_map.get(marca_nom) if marca_nom else None,
            'stock_actual': qty,
            'stock_minimo': minimo,
            'orden_compra': oc,
            'costo_unitario': costo,
            'fecha_actualizacion': datetime.date(2024, 3, 1),
        },
    )
    stock_map[nom] = s
    if created:
        MovimientoStock.objects.create(
            stock_consumible=s,
            tipo='INGRESO',
            cantidad=qty,
            registrado_por=admin_prof,
            referencia=oc,
            observacion='Ingreso inicial de stock.',
        )

print('Almacén OK')

# ── Tickets ───────────────────────────────────────────────────────
from apps.tickets.models import Ticket, TicketHistorial, TicketDiagnostico

tickets_data = [
    (pc1,  prof_map[-5], prof_map[-2], 'CORRECTIVO', 'La computadora no enciende, solo muestra pantalla negra al presionar el botón de encendido.', 'SOLUCIONADO', 9),
    (imp1, prof_map[-6], prof_map[-3], 'CORRECTIVO', 'La impresora no imprime, se atasca el papel constantemente y emite un pitido.', 'EN_ATENCION', 7),
    (pc2,  prof_map[-6], None,         'PREVENTIVO', 'Solicito mantenimiento preventivo trimestral del equipo según cronograma.', 'ENVIADO', 5),
    (pc3,  prof_map[-7], prof_map[-2], 'CORRECTIVO', 'El equipo es muy lento al iniciar Windows, tarda más de 10 minutos en cargar.', 'ASIGNADO', 4),
    (mon1, prof_map[-5], prof_map[-3], 'CORRECTIVO', 'El monitor parpadea constantemente y muestra líneas horizontales en la pantalla.', 'EN_MANTENIMIENTO', 8),
    (pc4,  prof_map[-5], prof_map[-2], 'CORRECTIVO', 'El teclado no responde varias teclas (A, S, D, F) al presionarlas.', 'FINALIZADO', 15),
    (imp2, prof_map[-7], None,         'CORRECTIVO', 'La impresora matricial no imprime, la cinta está gastada.', 'ENVIADO', 2),
    (pc5,  prof_map[-6], prof_map[-3], 'CORRECTIVO', 'El equipo se reinicia solo cada cierto tiempo sin motivo aparente.', 'EN_REVISION', 3),
]

for disp_obj, solicitante, tecnico, tipo, detalle, estado, dias_atras in tickets_data:
    if Ticket.objects.filter(dispositivo=disp_obj, estado=estado).exists():
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
        fecha_cierre=timezone.now() - timedelta(days=1) if estado in ('SOLUCIONADO', 'FINALIZADO', 'RECHAZADO') else None,
    )
    t.numero = Ticket._generar_numero()
    t.save()

    # Historial
    TicketHistorial.objects.create(
        ticket=t, usuario=solicitante,
        estado_anterior=None, estado_nuevo='ENVIADO',
        comentario='Ticket creado.',
        fecha=fecha_creacion,
    )
    pasos = {
        'EN_REVISION':    [('ENVIADO', 'EN_REVISION', jefe, 'En revisión por el jefe de informática.')],
        'ASIGNADO':       [('ENVIADO', 'EN_REVISION', jefe, 'En revisión.'), ('EN_REVISION', 'ASIGNADO', jefe, f'Asignado al técnico {tecnico.nombre_completo if tecnico else ""}.')],
        'EN_ATENCION':    [('ENVIADO', 'EN_REVISION', jefe, 'En revisión.'), ('EN_REVISION', 'ASIGNADO', jefe, 'Asignado.'), ('ASIGNADO', 'EN_ATENCION', tecnico or jefe, 'Técnico inicia atención.')],
        'EN_MANTENIMIENTO': [('ENVIADO', 'EN_REVISION', jefe, 'En revisión.'), ('EN_REVISION', 'ASIGNADO', jefe, 'Asignado.'), ('ASIGNADO', 'EN_ATENCION', tecnico or jefe, 'En atención.'), ('EN_ATENCION', 'EN_MANTENIMIENTO', tecnico or jefe, 'Requiere mantenimiento mayor.')],
        'SOLUCIONADO':    [('ENVIADO', 'EN_REVISION', jefe, 'En revisión.'), ('EN_REVISION', 'ASIGNADO', jefe, 'Asignado.'), ('ASIGNADO', 'EN_ATENCION', tecnico or jefe, 'En atención.'), ('EN_ATENCION', 'SOLUCIONADO', tecnico or jefe, 'Falla solucionada.')],
        'FINALIZADO':     [('ENVIADO', 'EN_REVISION', jefe, 'En revisión.'), ('EN_REVISION', 'ASIGNADO', jefe, 'Asignado.'), ('ASIGNADO', 'EN_ATENCION', tecnico or jefe, 'En atención.'), ('EN_ATENCION', 'EN_MANTENIMIENTO', tecnico or jefe, 'Mayor.'), ('EN_MANTENIMIENTO', 'FINALIZADO', tecnico or jefe, 'Trabajo finalizado.')],
    }
    for ant, nuevo, usr, com in pasos.get(estado, []):
        TicketHistorial.objects.create(
            ticket=t, usuario=usr,
            estado_anterior=ant, estado_nuevo=nuevo,
            comentario=com,
            fecha=fecha_creacion + timedelta(hours=pasos.get(estado, []).index((ant, nuevo, usr, com)) + 1),
        )

# Diagnósticos
for ticket_estado, tipo_falla, detalle_tec, tipo_res, tec_key in [
    ('SOLUCIONADO',     'Falla de fuente de poder',      'Se reemplazó la fuente de poder. El equipo enciende correctamente.',               'MENOR', -2),
    ('EN_MANTENIMIENTO','Falla de panel LCD',            'El panel presenta falla interna. Se enviará a servicio técnico para reemplazo.',   'MAYOR', -3),
    ('EN_ATENCION',     'Atasco mecánico de rodillos',   'Se identificó desgaste en rodillos de arrastre. Se limpiará y ajustará el mecanismo.', 'MENOR', -3),
    ('FINALIZADO',      'Desgaste físico del teclado',   'Se reemplazó el teclado con uno nuevo del almacén. Funcionando correctamente.',    'MENOR', -2),
]:
    t_obj = Ticket.objects.filter(estado=ticket_estado).first()
    if t_obj and not TicketDiagnostico.objects.filter(ticket=t_obj).exists():
        TicketDiagnostico.objects.create(
            ticket=t_obj,
            tipo_falla=tipo_falla,
            detalle_tecnico=detalle_tec,
            tipo_resultado=tipo_res,
            tecnico=prof_map[tec_key],
            fecha_registro=timezone.now() - timedelta(days=2),
        )

print('Tickets OK')

# ── Bajas ─────────────────────────────────────────────────────────
from apps.inventario.models import BienBaja

disp_baja = make_disp('PC-OLD', 'COMPUTADORA', 'HP', 'HP Compaq DC7900', 'SN-OLD-001', sede1, prof_map[-5], 'DE_BAJA')
BienBaja.objects.get_or_create(
    dispositivo=disp_baja,
    defaults={
        'sin_registro': False,
        'cod_inventario_ref': 'PC-OLD',
        'motivo': 'Equipo obsoleto, supera los 10 años de uso. No admite actualizaciones de software.',
        'estado': 'APROBADO',
        'fecha': datetime.date(2024, 2, 10),
        'lugar_origen': 'Oficina de Administración - Sede Central',
        'registrado_por': prof_map[-1],
    },
)

BienBaja.objects.get_or_create(
    dispositivo=None,
    sin_registro=True,
    defaults={
        'sin_registro': True,
        'sr_cod_inventario': 'SIN-001',
        'sr_descripcion': 'Monitor CRT antiguo sin código de inventario',
        'sr_marca': 'Samsung',
        'sr_modelo': 'SyncMaster 793',
        'sr_serie': 'DESCONOCIDA',
        'motivo': 'Monitor CRT encontrado en almacén sin registro. Obsoleto y sin utilidad.',
        'estado': 'PENDIENTE',
        'fecha': datetime.date(2024, 3, 5),
        'lugar_origen': 'Almacén general',
        'registrado_por': prof_map[-1],
    },
)

print('Bajas OK')

# ── Resumen ───────────────────────────────────────────────────────
from apps.almacen.models import StockConsumible
from apps.tickets.models import Ticket

print()
print('=' * 40)
print('DATOS DE PRUEBA CARGADOS')
print('=' * 40)
print(f'Tipos de dispositivo : {TipoDispositivo.objects.count()}')
print(f'Marcas               : {Marca.objects.count()}')
print(f'Sedes                : {Sede.objects.count()}')
print(f'Unidades orgánicas   : {UnidadOrganica.objects.count()}')
print(f'Perfiles de usuario  : {UserProfile.objects.count()}')
print(f'Dispositivos         : {Dispositivo.objects.count()}')
print(f'Tickets              : {Ticket.objects.count()}')
print(f'Stock (consumibles)  : {StockConsumible.objects.count()}')
print(f'Bajas registradas    : {BienBaja.objects.count()}')
