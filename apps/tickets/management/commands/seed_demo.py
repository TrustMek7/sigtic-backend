"""
Management command: carga datos de demostración completos.
Uso: python manage.py seed_demo --settings=config.settings.development
     python manage.py seed_demo --flush  (borra todo antes de cargar)
"""
import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Carga datos de demostración para SIGTIC'

    def add_arguments(self, parser):
        parser.add_argument('--flush', action='store_true', help='Borra datos previos antes de cargar')

    def handle(self, *args, **options):
        if options['flush']:
            self._flush()

        self._catalogo()
        self._organizacion()
        self._usuarios()
        self._inventario()
        self._almacen()
        self._tickets()
        self._bajas()
        self._resumen()

    # ─────────────────────────────────────────────────────────────────
    def _flush(self):
        from apps.tickets.models import TicketHistorial, TicketDiagnostico, TicketAdjunto, TicketAccion, TicketTercerizado, Ticket
        from apps.inventario.models import BienBaja, BienBajaFoto
        from apps.almacen.models import MovimientoStock, StockConsumible
        TicketHistorial.objects.all().delete()
        TicketDiagnostico.objects.all().delete()
        TicketAdjunto.objects.all().delete()
        TicketAccion.objects.all().delete()
        TicketTercerizado.objects.all().delete()
        Ticket.objects.all().delete()
        BienBajaFoto.objects.all().delete()
        BienBaja.objects.all().delete()
        MovimientoStock.objects.all().delete()
        StockConsumible.objects.all().delete()
        from apps.inventario.models import (DispComputadora, DispImpresora, DispMonitor,
                                             DispPeriferico, DispRed, DispCamara, DispTelefono, Dispositivo)
        DispComputadora.objects.all().delete()
        DispImpresora.objects.all().delete()
        DispMonitor.objects.all().delete()
        DispPeriferico.objects.all().delete()
        DispRed.objects.all().delete()
        DispCamara.objects.all().delete()
        DispTelefono.objects.all().delete()
        Dispositivo.objects.all().delete()
        from apps.users.models import UserProfile
        UserProfile.objects.filter(usu_ide_siggo__lt=0).exclude(usu_ide_siggo__gt=-900).delete()
        self.stdout.write('  Datos anteriores eliminados.')

    # ─────────────────────────────────────────────────────────────────
    def _catalogo(self):
        from apps.catalogo.models import TipoDispositivo, Marca, SistemaOperativo, Procesador, MemoriaRam, Consumible

        for cod, nom in [('COMPUTADORA','Computadora'),('IMPRESORA','Impresora'),
                          ('MONITOR','Monitor'),('PERIFERICO','Periférico'),
                          ('RED','Equipo de Red'),('CAMARA','Cámara'),('TELEFONO','Teléfono IP')]:
            TipoDispositivo.objects.get_or_create(codigo=cod, defaults={'nombre': nom, 'tiene_subtabla': True})

        for m in ['HP','Dell','Lenovo','EPSON','Canon','Cisco','TP-Link','Hikvision','Samsung','LG','Logitech','Asus']:
            Marca.objects.get_or_create(nombre=m)

        for s in ['Windows 10 Pro','Windows 11 Pro','Windows 7 Pro','Ubuntu 22.04','Sin SO']:
            SistemaOperativo.objects.get_or_create(nombre=s)

        for p in ['Intel Core i3','Intel Core i5','Intel Core i7','AMD Ryzen 5','AMD Ryzen 7','Intel Celeron']:
            Procesador.objects.get_or_create(nombre=p)

        for r in ['2 GB','4 GB','8 GB','16 GB','32 GB']:
            MemoriaRam.objects.get_or_create(capacidad=r)

        for nom, tipo in [('Toner HP 85A','TONER'),('Toner HP 78A','TONER'),
                           ('Toner EPSON T664','TINTA'),('Cinta Epson LX-350','RIBBON'),('Papel A4 75gr','PAPEL')]:
            Consumible.objects.get_or_create(nombre=nom, defaults={'tipo': tipo})

        self.stdout.write(self.style.SUCCESS('  Catálogo OK'))

    # ─────────────────────────────────────────────────────────────────
    def _organizacion(self):
        from apps.organizacion.models import Sede, UnidadOrganica, Subgerencia, Dependencia

        Sede.objects.get_or_create(nombre='Sede Central', defaults={'direccion': 'Av. Principal 123'})
        Sede.objects.get_or_create(nombre='Sede Norte',   defaults={'direccion': 'Jr. Los Pinos 456'})
        u1, _ = UnidadOrganica.objects.get_or_create(nombre='Gerencia Municipal',    defaults={'abreviatura': 'GM', 'nivel': 1})
        u2, _ = UnidadOrganica.objects.get_or_create(nombre='Unidad de Informática', defaults={'abreviatura': 'UI', 'nivel': 2, 'superior': u1})
        UnidadOrganica.objects.get_or_create(nombre='Gerencia de Administración',    defaults={'abreviatura': 'GA', 'nivel': 1})
        s1, _ = Subgerencia.objects.get_or_create(nombre='Subgerencia de Sistemas', defaults={'unidad_organica': u2})
        s2, _ = Subgerencia.objects.get_or_create(nombre='Subgerencia de Soporte',  defaults={'unidad_organica': u2})
        Dependencia.objects.get_or_create(nombre='Mesa de Ayuda',  defaults={'subgerencia': s2})
        Dependencia.objects.get_or_create(nombre='Desarrollo Web', defaults={'subgerencia': s1})
        self.stdout.write(self.style.SUCCESS('  Organización OK'))

    # ─────────────────────────────────────────────────────────────────
    def _usuarios(self):
        from apps.users.models import UserProfile, RolSigtic
        from apps.organizacion.models import Sede
        sede = Sede.objects.filter(nombre='Sede Central').first()

        perfiles = [
            (-1,  'Juan Pérez López',     'jperez',  RolSigtic.JEFE_INFO,      '43210001'),
            (-2,  'María García Ríos',    'mgarcia', RolSigtic.TECNICO,        '43210002'),
            (-3,  'Carlos Torres Vega',   'ctorres', RolSigtic.TECNICO,        '43210003'),
            (-4,  'Ana Flores Mendoza',   'aflores', RolSigtic.ENCARGADO_INFO, '43210004'),
            (-5,  'Luis Ramos Chávez',    'lramos',  RolSigtic.USUARIO,        '43210005'),
            (-6,  'Rosa Díaz Paredes',    'rdiaz',   RolSigtic.USUARIO,        '43210006'),
            (-7,  'Pedro Quispe Mamani',  'pquispe', RolSigtic.USUARIO,        '43210007'),
        ]
        for uid, nombre, usu, rol, dni in perfiles:
            UserProfile.objects.get_or_create(
                usu_ide_siggo=uid,
                defaults={'per_ide_siggo': 0, 'dni': dni, 'nombre_completo': nombre,
                          'email': f'{usu}@muni.gob.pe', 'rol': rol, 'activo': True, 'sede': sede},
            )
        self.stdout.write(self.style.SUCCESS('  Usuarios OK'))

    # ─────────────────────────────────────────────────────────────────
    def _inventario(self):
        from apps.catalogo.models import TipoDispositivo, Marca, SistemaOperativo, Procesador, MemoriaRam, Consumible
        from apps.organizacion.models import Sede
        from apps.users.models import UserProfile
        from apps.inventario.models import (Dispositivo, DispComputadora, DispImpresora,
                                             DispMonitor, DispPeriferico, DispRed)

        t = {o.codigo: o for o in TipoDispositivo.objects.all()}
        m = {o.nombre: o for o in Marca.objects.all()}
        s = {o.nombre: o for o in Sede.objects.all()}
        p = {o.usu_ide_siggo: o for o in UserProfile.objects.all()}
        so = {o.nombre: o for o in SistemaOperativo.objects.all()}
        proc = {o.nombre: o for o in Procesador.objects.all()}
        ram = {o.capacidad: o for o in MemoriaRam.objects.all()}
        cons = {o.nombre: o for o in Consumible.objects.all()}

        def disp(cod, tipo, marca, modelo, serie, sede_nom, resp_id, estado='OPERATIVO'):
            obj, _ = Dispositivo.objects.get_or_create(cod_inventario=cod, defaults={
                'tipo_dispositivo': t[tipo], 'marca': m.get(marca), 'modelo': modelo,
                'serie': serie, 'estado': estado, 'sede': s.get(sede_nom),
                'responsable': p.get(resp_id), 'activo': True,
                'fecha_registro': datetime.date(2024, 1, 15),
            })
            return obj

        pc1 = disp('PC-001','COMPUTADORA','HP',    'HP ProBook 450',       'SN-HP-001','Sede Central',-5)
        pc2 = disp('PC-002','COMPUTADORA','Dell',  'Dell OptiPlex 7090',   'SN-DL-001','Sede Central',-6)
        pc3 = disp('PC-003','COMPUTADORA','Lenovo','Lenovo ThinkCentre',   'SN-LN-001','Sede Norte',  -7)
        pc4 = disp('PC-004','COMPUTADORA','HP',    'HP EliteBook 840',     'SN-HP-002','Sede Central',-5,'EN_MANTENIMIENTO')
        pc5 = disp('PC-005','COMPUTADORA','Asus',  'Asus ExpertCenter D5', 'SN-AS-001','Sede Norte',  -6)

        for pc, ip, eq, os_, pr, ra in [
            (pc1,'192.168.1.101','PC-RECEPCION','Windows 10 Pro','Intel Core i5','8 GB'),
            (pc2,'192.168.1.102','PC-ADMIN',    'Windows 11 Pro','Intel Core i7','16 GB'),
            (pc3,'192.168.1.201','PC-NORTE',    'Windows 10 Pro','Intel Core i3','4 GB'),
            (pc4,'192.168.1.103','PC-JEFE',     'Windows 11 Pro','Intel Core i7','16 GB'),
            (pc5,'192.168.1.202','PC-NORTE2',   'Windows 10 Pro','Intel Core i5','8 GB'),
        ]:
            DispComputadora.objects.get_or_create(dispositivo=pc, defaults={
                'sistema_operativo': so[os_], 'procesador': proc[pr], 'memoria_ram': ram[ra],
                'almacenamiento': '500GB SSD', 'ip': ip, 'mac': f'AA:BB:CC:{pc.id:02X}:00:01',
                'nombre_equipo': eq, 'dominio': 'muni.local', 'tipo_pc': 'DESKTOP',
                'licencia_windows': True, 'licencia_office': True, 'antivirus': True,
            })

        imp1 = disp('IMP-001','IMPRESORA','HP',   'HP LaserJet Pro M404','SN-IMP-001','Sede Central',-6)
        imp2 = disp('IMP-002','IMPRESORA','EPSON','Epson LX-350',        'SN-IMP-002','Sede Central',-7)
        imp3 = disp('IMP-003','IMPRESORA','Canon','Canon MF3010',        'SN-IMP-003','Sede Norte',  -5)
        DispImpresora.objects.get_or_create(dispositivo=imp1, defaults={'tipo':'LASER',    'ip':'192.168.1.150', 'nombre_red':'IMP-LASER-01', 'consumible':cons.get('Toner HP 85A')})
        DispImpresora.objects.get_or_create(dispositivo=imp2, defaults={'tipo':'MATRICIAL','nombre_red':'IMP-MAT-01',   'consumible':cons.get('Cinta Epson LX-350')})
        DispImpresora.objects.get_or_create(dispositivo=imp3, defaults={'tipo':'LASER',    'nombre_red':'IMP-LASER-02', 'consumible':cons.get('Toner HP 78A')})

        mon1 = disp('MON-001','MONITOR','Samsung','Samsung S24F350','SN-MON-001','Sede Central',-5)
        mon2 = disp('MON-002','MONITOR','LG',     'LG 22MK430',    'SN-MON-002','Sede Central',-6)
        DispMonitor.objects.get_or_create(dispositivo=mon1, defaults={'tamanio_pulgadas':24,'resolucion':'1920x1080','tipo_panel':'IPS','conexion':'HDMI'})
        DispMonitor.objects.get_or_create(dispositivo=mon2, defaults={'tamanio_pulgadas':22,'resolucion':'1920x1080','tipo_panel':'TN', 'conexion':'HDMI'})

        per1 = disp('PER-001','PERIFERICO','Logitech','Logitech MK270','SN-PER-001','Sede Central',-5)
        per2 = disp('PER-002','PERIFERICO','Logitech','Logitech M100', 'SN-PER-002','Sede Central',-6)
        DispPeriferico.objects.get_or_create(dispositivo=per1, defaults={'subtipo':'TECLADO','conexion':'USB'})
        DispPeriferico.objects.get_or_create(dispositivo=per2, defaults={'subtipo':'MOUSE',  'conexion':'USB'})

        red1 = disp('RED-001','RED','Cisco',  'Cisco SG350-28',   'SN-RED-001','Sede Central',-1)
        red2 = disp('RED-002','RED','TP-Link','TP-Link TL-SF1024','SN-RED-002','Sede Norte',  -1)
        DispRed.objects.get_or_create(dispositivo=red1, defaults={'subtipo':'SWITCH','ip':'192.168.1.1','nombre_red':'SW-PRINCIPAL','puertos':28})
        DispRed.objects.get_or_create(dispositivo=red2, defaults={'subtipo':'SWITCH','ip':'192.168.2.1','nombre_red':'SW-NORTE',    'puertos':24})

        self.stdout.write(self.style.SUCCESS(f'  Inventario OK ({Dispositivo.objects.count()} dispositivos)'))

    # ─────────────────────────────────────────────────────────────────
    def _almacen(self):
        from apps.catalogo.models import Consumible, Marca
        from apps.almacen.models import StockConsumible, MovimientoStock
        from apps.users.models import UserProfile, RolSigtic

        registrador = UserProfile.objects.filter(rol=RolSigtic.ADMIN).first() or \
                      UserProfile.objects.filter(rol=RolSigtic.JEFE_INFO).first()
        cons = {o.nombre: o for o in Consumible.objects.all()}
        marc = {o.nombre: o for o in Marca.objects.all()}

        stocks = [
            ('Toner HP 85A',       'HP',    25, 5, 'OC-2024-001', 45.50),
            ('Toner HP 78A',       'HP',    10, 3, 'OC-2024-001', 38.00),
            ('Toner EPSON T664',   'EPSON',  8, 2, 'OC-2024-002', 22.00),
            ('Cinta Epson LX-350', 'EPSON', 15, 4, 'OC-2024-002', 12.00),
            ('Papel A4 75gr',      None,     3, 5, 'OC-2024-003',  8.50),
        ]
        for nom, marca_nom, qty, minimo, oc, costo in stocks:
            s, created = StockConsumible.objects.get_or_create(
                consumible=cons[nom],
                defaults={'marca': marc.get(marca_nom) if marca_nom else None,
                          'stock_actual': qty, 'stock_minimo': minimo,
                          'orden_compra': oc, 'costo_unitario': costo,
                          'fecha_actualizacion': datetime.date(2024, 3, 1)},
            )
            if created and registrador:
                MovimientoStock.objects.create(
                    stock_consumible=s, tipo='INGRESO', cantidad=qty,
                    registrado_por=registrador, referencia=oc, observacion='Ingreso inicial.',
                )
        self.stdout.write(self.style.SUCCESS('  Almacén OK'))

    # ─────────────────────────────────────────────────────────────────
    def _tickets(self):
        from apps.inventario.models import Dispositivo
        from apps.users.models import UserProfile
        from apps.tickets.models import Ticket, TicketHistorial, TicketDiagnostico

        p = {o.usu_ide_siggo: o for o in UserProfile.objects.all()}
        d = {o.cod_inventario: o for o in Dispositivo.objects.all()}
        jefe = p.get(-1)

        # (cod, solicitante_id, tecnico_id, tipo, detalle, estado, dias_atras)
        tickets_data = [
            ('PC-001', -5, -2, 'CORRECTIVO', 'La computadora no enciende, solo muestra pantalla negra al presionar el botón de encendido.',    'SOLUCIONADO',     9),
            ('IMP-001',-6, -3, 'CORRECTIVO', 'La impresora no imprime, se atasca el papel constantemente y emite un pitido al intentar imprimir.','EN_ATENCION',  7),
            ('PC-002', -6, None,'PREVENTIVO', 'Solicito mantenimiento preventivo trimestral del equipo según el cronograma establecido.',         'ENVIADO',        5),
            ('PC-003', -7, -2, 'CORRECTIVO', 'El equipo es muy lento al iniciar Windows, tarda más de 10 minutos en cargar el escritorio.',      'ASIGNADO',       4),
            ('MON-001',-5, -3, 'CORRECTIVO', 'El monitor parpadea constantemente y muestra líneas horizontales en la pantalla al usarse.',       'EN_MANTENIMIENTO',8),
            ('PC-004', -5, -2, 'CORRECTIVO', 'El teclado no responde varias teclas (A, S, D, F) al presionarlas durante el trabajo normal.',     'FINALIZADO',    15),
            ('IMP-002',-7, None,'CORRECTIVO', 'La impresora matricial no imprime, la cinta parece gastada y no transfiere tinta al papel.',       'ENVIADO',        2),
            ('PC-005', -6, -3, 'CORRECTIVO', 'El equipo se reinicia solo cada cierto tiempo sin motivo aparente, perdiendo el trabajo.',          'EN_REVISION',    3),
        ]

        historial_pasos = {
            'ENVIADO':          [('ENVIADO', None)],
            'EN_REVISION':      [('ENVIADO', None), ('EN_REVISION', jefe)],
            'ASIGNADO':         [('ENVIADO', None), ('EN_REVISION', jefe), ('ASIGNADO', jefe)],
            'EN_ATENCION':      [('ENVIADO', None), ('EN_REVISION', jefe), ('ASIGNADO', jefe), ('EN_ATENCION', None)],
            'EN_MANTENIMIENTO': [('ENVIADO', None), ('EN_REVISION', jefe), ('ASIGNADO', jefe), ('EN_ATENCION', None), ('EN_MANTENIMIENTO', None)],
            'SOLUCIONADO':      [('ENVIADO', None), ('EN_REVISION', jefe), ('ASIGNADO', jefe), ('EN_ATENCION', None), ('SOLUCIONADO', None)],
            'FINALIZADO':       [('ENVIADO', None), ('EN_REVISION', jefe), ('ASIGNADO', jefe), ('EN_ATENCION', None), ('EN_MANTENIMIENTO', None), ('FINALIZADO', None)],
        }
        comentarios = {
            'ENVIADO': 'Ticket creado por el solicitante.',
            'EN_REVISION': 'Ticket recibido, en revisión por el jefe de informática.',
            'ASIGNADO': 'Ticket asignado al técnico de soporte.',
            'EN_ATENCION': 'Técnico inicia la atención del ticket.',
            'EN_MANTENIMIENTO': 'Diagnóstico realizado. Requiere mantenimiento mayor.',
            'SOLUCIONADO': 'Falla solucionada exitosamente.',
            'FINALIZADO': 'Trabajo de mantenimiento concluido.',
        }

        for cod, sol_id, tec_id, tipo, detalle, estado, dias in tickets_data:
            disp_obj = d.get(cod)
            sol = p.get(sol_id)
            tec = p.get(tec_id) if tec_id else None
            if not disp_obj or not sol:
                continue
            if Ticket.objects.filter(dispositivo=disp_obj).exists():
                continue

            fecha = timezone.now() - timedelta(days=dias)
            t = Ticket(
                dispositivo=disp_obj, solicitante=sol, tecnico=tec,
                asignado_por=jefe if tec else None,
                tipo_mantenimiento=tipo, detalle_falla=detalle, estado=estado,
                ip_solicitante='192.168.1.101',
                responsable_snapshot=sol, nombre_responsable_snapshot=sol.nombre_completo,
                cargo_responsable_snapshot='Trabajador Municipal',
                fecha_creacion=fecha,
                fecha_asignacion=fecha + timedelta(hours=3) if tec else None,
                fecha_cierre=timezone.now() - timedelta(hours=6) if estado in ('SOLUCIONADO','FINALIZADO') else None,
            )
            t.numero = Ticket._generar_numero()
            t.save()

            pasos = historial_pasos.get(estado, [('ENVIADO', None)])
            estado_prev = None
            for i, (est_nuevo, override_usr) in enumerate(pasos):
                usr = override_usr or tec or sol
                TicketHistorial.objects.create(
                    ticket=t, usuario=usr,
                    estado_anterior=estado_prev, estado_nuevo=est_nuevo,
                    comentario=comentarios.get(est_nuevo, ''),
                    fecha=fecha + timedelta(hours=i * 2),
                )
                estado_prev = est_nuevo

        # Diagnósticos
        diags = [
            ('SOLUCIONADO',     'Falla de fuente de poder',     'Se reemplazó la fuente de poder. Equipo enciende correctamente.',                 'MENOR', -2),
            ('EN_ATENCION',     'Atasco mecánico de rodillos',  'Rodillos desgastados. Se limpia y ajusta mecanismo de arrastre del papel.',       'MENOR', -3),
            ('EN_MANTENIMIENTO','Falla de panel LCD',           'Panel con falla interna. Se envía a servicio técnico para reemplazo del panel.',  'MAYOR', -3),
            ('FINALIZADO',      'Desgaste físico del teclado',  'Se reemplazó teclado por uno nuevo del almacén. Funcionando correctamente.',      'MENOR', -2),
        ]
        for est, tipo_f, detalle_t, tipo_r, tec_key in diags:
            t_obj = Ticket.objects.filter(estado=est).exclude(
                id__in=TicketDiagnostico.objects.values_list('ticket_id', flat=True)
            ).first()
            if t_obj and p.get(tec_key):
                TicketDiagnostico.objects.create(
                    ticket=t_obj, tipo_falla=tipo_f, detalle_tecnico=detalle_t,
                    tipo_resultado=tipo_r, tecnico=p[tec_key],
                    fecha_registro=timezone.now() - timedelta(days=2),
                )

        total = Ticket.objects.count()
        self.stdout.write(self.style.SUCCESS(f'  Tickets OK ({total} tickets, {TicketHistorial.objects.count()} registros historial)'))

    # ─────────────────────────────────────────────────────────────────
    def _bajas(self):
        from apps.inventario.models import Dispositivo, BienBaja
        from apps.users.models import UserProfile

        admin = UserProfile.objects.filter(usu_ide_siggo=-1).first()
        if not admin:
            return

        from apps.catalogo.models import TipoDispositivo
        from apps.organizacion.models import Sede
        from apps.inventario.models import DispComputadora

        t = {o.codigo: o for o in TipoDispositivo.objects.all()}
        s = {o.nombre: o for o in Sede.objects.all()}
        p = {o.usu_ide_siggo: o for o in UserProfile.objects.all()}

        disp_baja, _ = Dispositivo.objects.get_or_create(
            cod_inventario='PC-OLD',
            defaults={'tipo_dispositivo': t['COMPUTADORA'], 'modelo': 'HP Compaq DC7900',
                      'serie': 'SN-OLD-001', 'estado': 'DE_BAJA',
                      'sede': s.get('Sede Central'), 'responsable': p.get(-5),
                      'activo': False, 'fecha_registro': datetime.date(2014, 5, 1)},
        )

        BienBaja.objects.get_or_create(dispositivo=disp_baja, defaults={
            'sin_registro': False, 'cod_inventario_ref': 'PC-OLD',
            'motivo': 'Equipo obsoleto, supera los 10 años de uso. No admite actualizaciones de software ni hardware.',
            'estado': 'APROBADO', 'fecha': datetime.date(2024, 2, 10),
            'lugar_origen': 'Oficina de Administración - Sede Central',
            'registrado_por': admin,
        })

        BienBaja.objects.get_or_create(sin_registro=True, sr_cod_inventario='SIN-001', defaults={
            'sin_registro': True, 'sr_cod_inventario': 'SIN-001',
            'sr_descripcion': 'Monitor CRT antiguo encontrado en almacén sin código de inventario',
            'sr_marca': 'Samsung', 'sr_modelo': 'SyncMaster 793', 'sr_serie': 'DESCONOCIDA',
            'motivo': 'Monitor CRT obsoleto sin registro en inventario.',
            'estado': 'PENDIENTE', 'fecha': datetime.date(2024, 3, 5),
            'lugar_origen': 'Almacén general', 'registrado_por': admin,
        })
        self.stdout.write(self.style.SUCCESS('  Bajas OK'))

    # ─────────────────────────────────────────────────────────────────
    def _resumen(self):
        from apps.catalogo.models import TipoDispositivo, Marca
        from apps.organizacion.models import Sede
        from apps.users.models import UserProfile
        from apps.inventario.models import Dispositivo, BienBaja
        from apps.almacen.models import StockConsumible
        from apps.tickets.models import Ticket, TicketHistorial, TicketDiagnostico

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 45))
        self.stdout.write(self.style.SUCCESS('  DATOS DE DEMO CARGADOS CORRECTAMENTE'))
        self.stdout.write(self.style.SUCCESS('=' * 45))
        self.stdout.write(f'  Tipos de dispositivo : {TipoDispositivo.objects.count()}')
        self.stdout.write(f'  Marcas               : {Marca.objects.count()}')
        self.stdout.write(f'  Sedes                : {Sede.objects.count()}')
        self.stdout.write(f'  Perfiles de usuario  : {UserProfile.objects.count()}')
        self.stdout.write(f'  Dispositivos         : {Dispositivo.objects.count()}')
        self.stdout.write(f'  Stock (consumibles)  : {StockConsumible.objects.count()}')
        self.stdout.write(f'  Tickets              : {Ticket.objects.count()}')
        self.stdout.write(f'  Registros historial  : {TicketHistorial.objects.count()}')
        self.stdout.write(f'  Diagnósticos         : {TicketDiagnostico.objects.count()}')
        self.stdout.write(f'  Bienes de baja       : {BienBaja.objects.count()}')
        self.stdout.write('')
        for est in ['ENVIADO','EN_REVISION','ASIGNADO','EN_ATENCION','EN_MANTENIMIENTO','SOLUCIONADO','FINALIZADO']:
            n = Ticket.objects.filter(estado=est).count()
            if n:
                self.stdout.write(f'    {est:<22} {n} ticket(s)')
