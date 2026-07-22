"""
SISPAD-PEI-POA — Script de datos demo completos.
Cadena completa: PGDESA -> PDESA -> PAD -> PEI -> POA -> POAU
con indicadores, presupuesto, seguimiento y evaluacion.

Ejecutar:
  docker compose exec backend python manage.py shell < scripts/seed_demo.py
  o
  python manage.py shell -c "exec(open('scripts/seed_demo.py').read())"
"""
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
if not django.conf.settings.configured:
    django.setup()

from decimal import Decimal
from datetime import date, datetime
from django.db import transaction

print("=" * 70)
print("SISPAD-PEI-POA — DATOS DEMO COMPLETOS")
print("Gobierno Autonomo Municipal de Sacaba")
print("=" * 70)

# =========================================================================
# FUNCIONES AUXILIARES
# =========================================================================
def g(model, defaults=None, **kwargs):
    defaults = defaults or {}
    from datetime import date
    if hasattr(model, 'fecha_vigencia_desde') and 'fecha_vigencia_desde' not in defaults and 'fecha_vigencia_desde' not in kwargs:
        defaults['fecha_vigencia_desde'] = date(2026, 1, 1)
    obj, created = model.objects.get_or_create(defaults=defaults, **kwargs)
    if created:
        print(f"  + {model.__name__}: {kwargs.get('codigo', kwargs.get('nombre', kwargs.get('email', str(kwargs)[:60])))}")
    return obj

def gb(model, defaults=None, **kwargs):
    defaults = defaults or {}
    from datetime import date
    if hasattr(model, 'fecha_vigencia_desde') and 'fecha_vigencia_desde' not in defaults and 'fecha_vigencia_desde' not in kwargs:
        defaults['fecha_vigencia_desde'] = date(2026, 1, 1)
    obj, created = model.objects.get_or_create(defaults=defaults, **kwargs)
    return obj

# =========================================================================
# TRANSACCION PRINCIPAL
# =========================================================================
with transaction.atomic():
    # -----------------------------------------------------------------
    # 1. CATALOGOS BASE
    # -----------------------------------------------------------------
    print("\n--- CATALOGOS ---")
    from apps.catalogos.models import (
        UnidadMedida, ObjetoGasto, FuenteFinanciamiento,
        OrganismoFinanciador, FinalidadFuncion, TipoOperacion,
        TipoProducto, TipoProyecto, ClasificadorInstitucional,
        RubroRecurso, EntidadTransferencia, TipoFinanciamiento,
    )

    um_unidad = g(UnidadMedida, denominacion='Unidad', codigo='UNI', gestion=2026)
    um_persona = g(UnidadMedida, denominacion='Persona', codigo='PER', gestion=2026)
    um_vivienda = g(UnidadMedida, denominacion='Vivienda', codigo='VIV', gestion=2026)
    um_km = g(UnidadMedida, denominacion='Kilometro', codigo='KM', gestion=2026)
    um_m2 = g(UnidadMedida, denominacion='Metro cuadrado', codigo='M2', gestion=2026)
    um_ha = g(UnidadMedida, denominacion='Hectarea', codigo='HA', gestion=2026)
    um_porcentaje = g(UnidadMedida, denominacion='Porcentaje', codigo='%', gestion=2026)
    um_litro = g(UnidadMedida, denominacion='Litro', codigo='LT', gestion=2026)
    um_tonelada = g(UnidadMedida, denominacion='Tonelada', codigo='TON', gestion=2026)
    um_servicio = g(UnidadMedida, denominacion='Servicio', codigo='SRV', gestion=2026)

    # Objeto del gasto (classificacion presupuestaria)
    og_111 = g(ObjetoGasto, codigo='111', denominacion='Personal activo', gestion=2026)
    og_112 = g(ObjetoGasto, codigo='112', denominacion='Personal pasivo', gestion=2026)
    og_121 = g(ObjetoGasto, codigo='121', denominacion='Bienes muebles e inmuebles', gestion=2026)
    og_122 = g(ObjetoGasto, codigo='122', denominacion='Materiales y suministros', gestion=2026)
    og_131 = g(ObjetoGasto, codigo='131', denominacion='Servicios personales', gestion=2026)
    og_132 = g(ObjetoGasto, codigo='132', denominacion='Servicios no personales', gestion=2026)
    og_211 = g(ObjetoGasto, codigo='211', denominacion='Inversión nueva', gestion=2026)
    og_212 = g(ObjetoGasto, codigo='212', denominacion='Mejoramiento', gestion=2026)
    og_311 = g(ObjetoGasto, codigo='311', denominacion='Transferencias y subvenciones', gestion=2026)
    og_321 = g(ObjetoGasto, codigo='321', denominacion='Rentas de capital', gestion=2026)

    # Fuente de financiamiento
    ff_111 = g(FuenteFinanciamiento, codigo='111', denominacion='Recursos del Tesoro Municipal', gestion=2026)
    ff_121 = g(FuenteFinanciamiento, codigo='121', denominacion='Impuesto Directo a los Hidrocarburos (IDH)', gestion=2026)
    ff_131 = g(FuenteFinanciamiento, codigo='131', denominacion='Coparticipacion Nacional', gestion=2026)
    ff_211 = g(FuenteFinanciamiento, codigo='211', denominacion='Credito externo', gestion=2026)
    ff_311 = g(FuenteFinanciamiento, codigo='311', denominacion='Donaciones', gestion=2026)

    # Organismo financiador
    of_gob = g(OrganismoFinanciador, codigo='GOB', denominacion='Gobierno Municipal', gestion=2026)
    of_bm = g(OrganismoFinanciador, codigo='BM', denominacion='Banco Mundial', gestion=2026)
    of_bid = g(OrganismoFinanciador, codigo='BID', denominacion='Banco Interamericano de Desarrollo', gestion=2026)
    of_caf = g(OrganismoFinanciador, codigo='CAF', denominacion='Corporacion Andina de Fomento', gestion=2026)
    of_kfw = g(OrganismoFinanciador, codigo='KFW', denominacion='KfW Alemania', gestion=2026)

    # Finalidad / Funcion
    ff_func_01 = g(FinalidadFuncion, codigo='01', denominacion='Gobierno general', gestion=2026)
    ff_func_02 = g(FinalidadFuncion, codigo='02', denominacion='Defensa y orden publico', gestion=2026)
    ff_func_03 = g(FinalidadFuncion, codigo='03', denominacion='Educacion', gestion=2026)
    ff_func_04 = g(FinalidadFuncion, codigo='04', denominacion='Salud', gestion=2026)
    ff_func_05 = g(FinalidadFuncion, codigo='05', denominacion='Prevision social', gestion=2026)
    ff_func_06 = g(FinalidadFuncion, codigo='06', denominacion='Vivienda y servicios comunales', gestion=2026)
    ff_func_07 = g(FinalidadFuncion, codigo='07', denominacion='Actividades economicas', gestion=2026)

    # Tipo de operacion
    to_servicio = g(TipoOperacion, codigo='SRV', denominacion='Servicio', gestion=2026)
    to_mantenimiento = g(TipoOperacion, codigo='MNT', denominacion='Mantenimiento', gestion=2026)
    to_obra = g(TipoOperacion, codigo='OBR', denominacion='Obra', gestion=2026)
    to_capacitacion = g(TipoOperacion, codigo='CAP', denominacion='Capacitacion', gestion=2026)
    to_estudio = g(TipoOperacion, codigo='EST', denominacion='Estudio', gestion=2026)
    to_equipamiento = g(TipoOperacion, codigo='EQP', denominacion='Equipamiento', gestion=2026)

    # Tipo de producto
    tp_servicio = g(TipoProducto, codigo='SRV', denominacion='Servicio publico', gestion=2026)
    tp_infra = g(TipoProducto, codigo='INF', denominacion='Infraestructura', gestion=2026)
    tp_cap = g(TipoProducto, codigo='CAP', denominacion='Capacitacion', gestion=2026)
    tp_estudio = g(TipoProducto, codigo='EST', denominacion='Estudio tecnico', gestion=2026)
    tp_equip = g(TipoProducto, codigo='EQU', denominacion='Equipamiento', gestion=2026)

    # Tipo de proyecto
    tp_inv = g(TipoProyecto, codigo='INV', denominacion='Inversion publica', gestion=2026)
    tp_mant = g(TipoProyecto, codigo='MAN', denominacion='Mantenimiento', gestion=2026)
    tp_mej = g(TipoProyecto, codigo='MEJ', denominacion='Mejoramiento', gestion=2026)

    # Tipos adicionales
    g(ClasificadorInstitucional, codigo='CLA-01', denominacion='Entidad principal', gestion=2026)
    g(RubroRecurso, codigo='RR-01', denominacion='Recursos propios', gestion=2026)
    g(RubroRecurso, codigo='RR-02', denominacion='Recursos transferidos', gestion=2026)
    g(EntidadTransferencia, codigo='ET-01', denominacion='Gobierno Central', gestion=2026)
    g(EntidadTransferencia, codigo='ET-02', denominacion='Gobierno Departamental', gestion=2026)
    g(TipoFinanciamiento, codigo='TF-01', denominacion='Financiamiento directo', gestion=2026)
    g(TipoFinanciamiento, codigo='TF-02', denominacion='Contraentrega', gestion=2026)

    print(f"  Total catalogos: {sum([UnidadMedida.objects.count(), ObjetoGasto.objects.count(), FuenteFinanciamiento.objects.count(), OrganismoFinanciador.objects.count(), FinalidadFuncion.objects.count()])}")

    # -----------------------------------------------------------------
    # 2. USUARIOS
    # -----------------------------------------------------------------
    print("\n--- USUARIOS ---")
    from apps.accounts.models import Usuario, Rol
    from django.contrib.auth.hashers import make_password

    # Roles base (el seed.py ya los crea, pero aseguramos)
    roles_data = [
        ('superadmin', 'Superadministrador Tecnico'),
        ('admin_poa', 'Administrador POA'),
        ('admin_presupuesto', 'Administrador de Presupuesto'),
        ('responsable_unidad', 'Responsable POA de Unidad'),
        ('revisor_planificacion', 'Revisor de Planificacion'),
        ('revisor_presupuesto', 'Revisor de Presupuesto'),
        ('revisor_inversion', 'Revisor de Proyectos'),
        ('revisor_juridico', 'Revisor Juridico'),
        ('mae', 'Maxima Autoridad Ejecutiva'),
        ('auditor', 'Auditor'),
        ('consulta', 'Usuario de Consulta'),
        ('control_social', 'Participacion y Control Social'),
        ('articulador_tecnico', 'Tecnico de Articulacion PAD'),
        ('articulador_aprobador', 'Administrador de Articulaciones'),
        ('poau_responsable', 'Responsable POAU de Unidad'),
        ('poau_revisor', 'Revisor de POAU'),
    ]
    roles = {}
    for cod, nombre in roles_data:
        r = g(Rol, defaults={'nombre': nombre, 'es_sistema': True, 'descripcion': nombre}, codigo=cod)
        roles[cod] = r

    # Usuarios demo
    admin, _ = Usuario.objects.get_or_create(
        email='admin@gamsacaba.gob.bo',
        defaults={
            'first_name': 'Admin', 'last_name': 'SISPOA',
            'is_staff': True, 'is_superuser': True,
            'password': make_password('admin2026'),
        }
    )
    if _:
        admin.set_password('admin2026')
        admin.save()
    admin.roles.add(roles['superadmin'])
    print(f"  + Usuario: admin@gamsacaba.gob.bo / admin2026")

    def crear_usuario(email, nombre, apellido, password, rol_cod):
        u, created = Usuario.objects.get_or_create(
            email=email,
            defaults={
                'first_name': nombre, 'last_name': apellido,
                'password': make_password(password),
            }
        )
        if created:
            u.set_password(password)
            u.save()
            print(f"  + Usuario: {email} / {password}")
        u.roles.add(roles.get(rol_cod, roles['consulta']))
        return u

    u_mae = crear_usuario('mae@gamsacaba.gob.bo', 'Maria', 'Condori', 'mae2026', 'mae')
    u_plan = crear_usuario('planificador@gamsacaba.gob.bo', 'Carlos', 'Mamani', 'plan2026', 'revisor_planificacion')
    u_pres = crear_usuario('presupuesto@gamsacaba.gob.bo', 'Ana', 'Quispe', 'pres2026', 'revisor_presupuesto')
    u_jefe_plan = crear_usuario('jefe_plan@gamsacaba.gob.bo', 'Luis', 'Huanca', 'jefe2026', 'responsable_unidad')
    u_jefe_obras = crear_usuario('jefe_obras@gamsacaba.gob.bo', 'Pedro', 'Flores', 'jefe2026', 'responsable_unidad')
    u_tecnico = crear_usuario('tecnico@gamsacaba.gob.bo', 'Rosa', 'Vargas', 'tec2026', 'poau_responsable')
    u_auditor = crear_usuario('auditor@gamsacaba.gob.bo', 'Jorge', 'Ramos', 'aud2026', 'auditor')

    # -----------------------------------------------------------------
    # 3. ESTRUCTURA ORGANIZACIONAL
    # -----------------------------------------------------------------
    print("\n--- ESTRUCTURA ORGANIZACIONAL ---")
    from apps.organizacion.models import (
        TipoUnidad, UnidadOrganizacional, DireccionAdministrativa,
        UnidadEjecutora, AsignacionUsuarioUnidad,
    )

    # Tipos de unidad
    tipo_mae = g(TipoUnidad, codigo='MAE', nombre='Maxima Autoridad Ejecutiva', nivel=1)
    tipo_sec = g(TipoUnidad, codigo='SEC', nombre='Secretaria Municipal', nivel=2)
    tipo_dir = g(TipoUnidad, codigo='DIR', nombre='Direccion', nivel=3)
    tipo_jef = g(TipoUnidad, codigo='JEF', nombre='Jefatura', nivel=4)
    tipo_uni = g(TipoUnidad, codigo='UNI', nombre='Unidad', nivel=5)
    tipo_ue = g(TipoUnidad, codigo='UE', nombre='Unidad Ejecutora', nivel=3)

    # Direcciones Administrativas
    da_100 = g(DireccionAdministrativa, codigo='100', nombre='Direccion Administrativa Municipal', gestion=2026)
    da_200 = g(DireccionAdministrativa, codigo='200', nombre='Secretaria de Planificacion y Desarrollo Territorial', gestion=2026)
    da_300 = g(DireccionAdministrativa, codigo='300', nombre='Secretaria de Obras Publicas e Infraestructura', gestion=2026)

    # Unidades Ejecutoras
    ue_100 = g(UnidadEjecutora, codigo='UE-100', nombre='UE Administrativa Municipal', da=da_100, gestion=2026)
    ue_200 = g(UnidadEjecutora, codigo='UE-200', nombre='UE Planificacion Territorial', da=da_200, gestion=2026)
    ue_300 = g(UnidadEjecutora, codigo='UE-300', nombre='UE Obras Publicas', da=da_300, gestion=2026)

    # Unidades Organizacionales (jerarquia)
    uo_gam = g(UnidadOrganizacional, codigo='GAM', nombre='Gobierno Autonomo Municipal de Sacaba',
               sigla='GAM SACABA', tipo=tipo_mae, gestion=2026, responsable=u_mae, padre=None)
    uo_sec_plan = g(UnidadOrganizacional, codigo='SEC-PLA', nombre='Secretaria de Planificacion y Desarrollo Territorial',
                     sigla='SPTD', tipo=tipo_sec, gestion=2026, responsable=u_plan, padre=uo_gam)
    uo_sec_op = g(UnidadOrganizacional, codigo='SEC-OBR', nombre='Secretaria de Obras Publicas',
                   sigla='SOP', tipo=tipo_sec, gestion=2026, responsable=u_jefe_obras, padre=uo_gam)
    uo_dir_plan = g(UnidadOrganizacional, codigo='DIR-PLA', nombre='Direccion de Planificacion',
                     tipo=tipo_dir, gestion=2026, responsable=u_jefe_plan, padre=uo_sec_plan)
    uo_dir_cata = g(UnidadOrganizacional, codigo='DIR-CAT', nombre='Direccion de Catastro Multifinalitario y Administracion de Tierras',
                     tipo=tipo_dir, gestion=2026, responsable=u_jefe_plan, padre=uo_sec_plan)
    uo_upl = g(UnidadOrganizacional, codigo='UPL', nombre='Unidad de Planificacion Estrategica',
                tipo=tipo_uni, gestion=2026, responsable=u_tecnico, padre=uo_dir_plan)
    uo_upre = g(UnidadOrganizacional, codigo='UPRE', nombre='Unidad de Presupuesto',
                 tipo=tipo_uni, gestion=2026, responsable=u_pres, padre=uo_dir_plan)
    uo_dir_obras = g(UnidadOrganizacional, codigo='DIR-OBR', nombre='Direccion de Proyectos de Inversion',
                      tipo=tipo_dir, gestion=2026, responsable=u_jefe_obras, padre=uo_sec_op)
    uo_uip = g(UnidadOrganizacional, codigo='UIP', nombre='Unidad de Inversion Publica',
                tipo=tipo_uni, gestion=2026, responsable=u_jefe_obras, padre=uo_dir_obras)
    uo_umant = g(UnidadOrganizacional, codigo='UMANT', nombre='Unidad de Mantenimiento',
                  tipo=tipo_uni, gestion=2026, responsable=u_tecnico, padre=uo_dir_obras)

    # Asignaciones usuario-unidad
    g(AsignacionUsuarioUnidad, usuario=u_tecnico, unidad=uo_upl, es_responsable_poa=True, gestion=2026)
    g(AsignacionUsuarioUnidad, usuario=u_jefe_obras, unidad=uo_uip, es_responsable_poa=True, gestion=2026)
    g(AsignacionUsuarioUnidad, usuario=u_jefe_plan, unidad=uo_upre, es_responsable_poa=True, gestion=2026)

    # -----------------------------------------------------------------
    # 4. GESTION FISCAL
    # -----------------------------------------------------------------
    print("\n--- GESTION FISCAL ---")
    from apps.gestion.models import GestionFiscal, CicloFormulacion, EtapaFormulacion
    from django.utils import timezone
    import datetime

    gestion, _ = GestionFiscal.objects.get_or_create(
        anio=2026,
        defaults={
            'estado': 'formulacion',
            'anio_inicio_plurianual': 2026,
            'anio_fin_plurianual': 2028,
            'fecha_apertura': timezone.now() - datetime.timedelta(days=90),
        }
    )
    print(f"  + GestionFiscal: 2026 (formulacion)")

    ciclo, _ = CicloFormulacion.objects.get_or_create(
        gestion=gestion, nombre='Formulacion POA 2026',
        defaults={
            'fecha_inicio': timezone.now() - datetime.timedelta(days=60),
            'fecha_cierre': timezone.now() + datetime.timedelta(days=90),
            'orden': 1,
        }
    )

    for i, (cod, nombre, orden) in enumerate([
        ('FORM', 'Formulacion', 1),
        ('REVI', 'Revision', 2),
        ('CONS', 'Consolidacion', 3),
        ('APRO', 'Aprobacion', 4),
    ], 1):
        EtapaFormulacion.objects.get_or_create(
            ciclo=ciclo, codigo=cod,
            defaults={
                'nombre': nombre,
                'fecha_inicio': timezone.now() - datetime.timedelta(days=60 + (4 - i) * 15),
                'fecha_cierre': timezone.now() + datetime.timedelta(days=90 - i * 15),
                'orden': orden,
                'completada': i == 1,
            }
        )

    # -----------------------------------------------------------------
    # 5. PLANES Y JERARQUIA ESTRATEGICA
    # -----------------------------------------------------------------
    print("\n--- PLANES Y JERARQUIA ---")
    from apps.planificacion.models import (
        Plan, Sector, NodoPlanificacion, AccionMedianoPlazo,
        AccionCortoPlazo, ArticulacionPlanificacion,
    )

    # Sectores
    sec_infra = g(Sector, codigo='INF', nombre='Infraestructura y Servicios Basicos')
    sec_prod = g(Sector, codigo='PRO', nombre='Desarrollo Productivo')
    sec_serv = g(Sector, codigo='SER', nombre='Servicios Publicos')

    # Plan PDES (Plan Estrategico Departamental)
    pdes = g(Plan, codigo='PDES-2021', nombre='Plan Estrategico de Desarrollo Departamental Cochabamba',
             tipo='pdes', gestion_inicio=2021, gestion_fin=2025)

    # Nodos PDES
    nodo_pdes_pilar = g(NodoPlanificacion, plan=pdes, nivel='pilar', codigo='PDES-PI-01',
                         nombre='Desarrollo Sostenible y Competitivo', gestion=2021)
    nodo_pdes_eje1 = g(NodoPlanificacion, plan=pdes, nivel='eje', codigo='PDES-EJ-01',
                        nombre='Infraestructura y Connectivity', padre=nodo_pdes_pilar, gestion=2021)
    nodo_pdes_eje2 = g(NodoPlanificacion, plan=pdes, nivel='eje', codigo='PDES-EJ-02',
                        nombre='Desarrollo Productivo Local', padre=nodo_pdes_pilar, gestion=2021)
    nodo_pdes_meta1 = g(NodoPlanificacion, plan=pdes, nivel='meta', codigo='PDES-MT-01',
                         nombre='Mejorar conectividad vial departamental', padre=nodo_pdes_eje1, gestion=2021)
    nodo_pdes_meta2 = g(NodoPlanificacion, plan=pdes, nivel='meta', codigo='PDES-MT-02',
                         nombre='Fortalecer productividad local', padre=nodo_pdes_eje2, gestion=2021)

    # Plan PTDI (Plan de Desarrollo Integral Municipal - Sacaba)
    ptdi = g(Plan, codigo='PTDI-SAC', nombre='Plan de Desarrollo Territorial Integral de Sacaba',
             tipo='ptdi', gestion_inicio=2021, gestion_fin=2025)

    # Nodos PTDI
    nodo_ptdi_acc1 = g(NodoPlanificacion, plan=ptdi, nivel='accion_pdes', codigo='PTDI-AC-01',
                        nombre='Acciones de articulacion con el PDES', gestion=2021)
    nodo_ptdi_acc2 = g(NodoPlanificacion, plan=ptdi, nivel='accion_pdes', codigo='PTDI-AC-02',
                        nombre='Acciones de mediano plazo', gestion=2021)

    # Plan PEI 2026
    pei = g(Plan, codigo='PEI-2026', nombre='Plan Estrategico Institucional 2026-2028',
            tipo='pei', gestion_inicio=2026, gestion_fin=2028)

    # Nodos PEI (accion_mediano)
    nodos_pei = []
    for i in range(1, 7):
        n = g(NodoPlanificacion, plan=pei, nivel='accion_mediano',
              codigo=f'PEI-AMP-{i:02d}',
              nombre=f'Accion de Mediano Plazo {i} - Linea {i}',
              padre=nodo_ptdi_acc2, gestion=2026)
        nodos_pei.append(n)

    # -----------------------------------------------------------------
    # 6. ACCIONES MEDIANO Y CORTO PLAZO
    # -----------------------------------------------------------------
    print("\n--- ACCIONES AMP / ACP ---")
    amp_data = [
        ('AMP-001', 'Mejoramiento de vias urbanas en distritos prioritarios', 2026, 2028),
        ('AMP-002', 'Ampliacion del servicio de agua potable a comunidades rurales', 2026, 2028),
        ('AMP-003', 'Construccion de puentes vehiculares en zona sur', 2026, 2028),
        ('AMP-004', 'Fortalecimiento de mercados municipales', 2026, 2028),
        ('AMP-005', 'Programa de apoyo a micro y pequeños productores', 2026, 2028),
        ('AMP-006', 'Implementacion de sistema de alcantarillado sanitario', 2026, 2028),
    ]
    amps = []
    for i, (cod, nombre, gf, gt) in enumerate(amp_data):
        amp = g(AccionMedianoPlazo, codigo=cod, nombre=nombre,
                nodo_planificacion=nodos_pei[i], gestion_inicio=gf, gestion_fin=gt,
                responsable=u_plan)
        amps.append(amp)

    acps = []
    for i, amp in enumerate(amps):
        acp = g(AccionCortoPlazo,
                codigo=f'ACP-{i+1:03d}',
                nombre=f'POA {amp.nombre[:50]}',
                accion_mediano_plazo=amp,
                unidad_responsable=uo_upl if i < 3 else uo_uip,
                gestion=2026,
                fecha_inicio=date(2026, 1, 15),
                fecha_fin=date(2026, 12, 31))
        acps.append(acp)

    # Articulacion PTDI -> PEI -> POA
    for i, (amp, nodo_pei) in enumerate(zip(amps, nodos_pei)):
        g(ArticulacionPlanificacion,
          nodo_origen=nodo_ptdi_acc1 if i < 3 else nodo_ptdi_acc2,
          nodo_destino=nodo_pei, es_principal=True, gestion=2026)

    # -----------------------------------------------------------------
    # 7. PAD - PLAN DE DESARROLLO MUNICIPAL
    # -----------------------------------------------------------------
    print("\n--- PAD ---")
    from apps.pad.models import (
        SectorPAD, PoliticaPAD, LineamientoEstrategico,
        ResultadoTerritorial, ProductoTerritorial,
        ProgramacionAnualPAD, ArticulacionSIPEB,
    )

    sectores_pad = []
    for cod, nombre in [('INF', 'Infraestructura y Servicios Basicos'),
                        ('DSB', 'Desarrollo Socioeconomico'),
                        ('GAM', 'Gestion Ambiental y Territorial')]:
        sectores_pad.append(g(SectorPAD, codigo=cod, nombre=nombre))

    politicas = []
    for cod, nombre in [
        ('POL-001', 'Infraestructura vial y equipamiento municipal'),
        ('POL-002', 'Agua potable y saneamiento basico'),
        ('POL-003', 'Desarrollo economico productivo local'),
    ]:
        pol = g(PoliticaPAD, codigo=cod, nombre=nombre, gestion=2026)
        politicas.append(pol)

    lineamientos = []
    lin_data = [
        ('LIN-001-01', 'Vias pavimentadas y rehabilitadas', politicas[0]),
        ('LIN-001-02', 'Puentes vehiculares seguros', politicas[0]),
        ('LIN-002-01', 'Servicio de agua potable continua', politicas[1]),
        ('LIN-002-02', 'Red de alcantarillado sanitario', politicas[1]),
        ('LIN-003-01', 'Mercados municipales modernos', politicas[2]),
        ('LIN-003-002', 'Apoyo a productores locales', politicas[2]),
    ]
    for cod, nombre, politica in lin_data:
        lin = g(LineamientoEstrategico, codigo=cod, nombre=nombre, politica=politica, gestion=2026)
        lineamientos.append(lin)

    resultados = []
    res_data = [
        ('RES-001', 'Kilometros de vias pavimentadas', lineamientos[0], sectores_pad[0], 'Longitud total de vias rehabilitadas', 'km', 2.5, 15.0),
        ('RES-002', 'Puentes rehabilitados', lineamientos[1], sectores_pad[0], 'Cantidad de puentes rehabilitados', 'unidades', 1, 8),
        ('RES-003', 'Beneficiarios con agua potable', lineamientos[2], sectores_pad[1], 'Personas con acceso continuo', 'personas', 15000, 45000),
        ('RES-004', 'Km de alcantarillado construido', lineamientos[3], sectores_pad[1], 'Red sanitaria instalada', 'km', 3.0, 18.0),
        ('RES-005', 'Mercados rehabilitados', lineamientos[4], sectores_pad[2], 'Mercados con mejoras', 'unidades', 2, 5),
        ('RES-006', 'Productores capacitados', lineamientos[5], sectores_pad[2], 'Beneficiarios directos', 'personas', 200, 1200),
    ]
    for i, (cod, nombre, lin, sec, indicador, unidad, lb, meta) in enumerate(res_data):
        res = g(ResultadoTerritorial, codigo=cod, nombre=nombre, lineamiento=lin,
                sector=sec, indicador=f'{indicador} ({unidad})',
                formula=f'Cantidad de {nombre.lower()}',
                linea_base=Decimal(str(lb)), meta_2030=Decimal(str(meta)),
                cod_geografico=f'SAC-{cod}', gestion=2026, estado='aprobado')
        resultados.append(res)

        prod = g(ProductoTerritorial,
                 codigo=f'PROD-{cod[-3:]}',
                 nombre=f'Producto: {nombre}',
                 resultado=res, gestion=2026,
                 territorializacion='GAM Sacaba',
                 responsable='Unidad de Planificacion',
                 indicador=f'Cantidad de {nombre.lower()}',
                 linea_base=Decimal(str(lb)),
                 meta_2030=Decimal(str(meta)),
                 cuenta_con_financiamiento='SI',
                 presupuesto_total_pad=Decimal('1500000') * (i + 1))

        # Programacion anual
        for anio in [2026, 2027, 2028]:
            prog_fisica = Decimal(str(meta - lb)) * Decimal(str((anio - 2025) / 3)) + Decimal(str(lb))
            prog_financiera = prog_fisica * Decimal('50000')
            ProgramacionAnualPAD.objects.get_or_create(
                resultado=res, producto=prod, anio=anio, tipo='fisica',
                defaults={'valor': prog_fisica.quantize(Decimal('0.0001'))}
            )
            ProgramacionAnualPAD.objects.get_or_create(
                resultado=res, producto=prod, anio=anio, tipo='financiera',
                defaults={'valor': prog_financiera.quantize(Decimal('0.0001'))}
            )

        # Articulacion SIPEB
        ArticulacionSIPEB.objects.get_or_create(
            resultado=res,
            defaults={
                'cod_eje_pgdesa': 'PDES-EJ-01' if i < 4 else 'PDES-EJ-02',
                'objetivo_impacto_pgdesa': 'Desarrollo sostenible departamental',
                'cod_componente_pdesa': f'PDES-CMP-{i+1:02d}',
                'objetivo_efecto_pdesa': f'Mejora de indicadores en {nombre.lower()}',
                'cod_ods': 'ODS-09' if i < 4 else 'ODS-08',
                'cod_meta_ndc': f'NDC-{i+1:02d}',
                'cod_principio_ndt': f'NDT-{i+1:02d}',
                'cod_sector': sec.codigo,
                'sector_nombre': sec.nombre,
                'cod_resultado_pds': f'PDS-{i+1:02d}',
                'resultado_pds': f'Resultado PDS: {nombre}',
                'cod_geografico': f'SAC-{cod}',
                'denominacion_eta': 'Gobierno Autonomo Municipal de Sacaba',
                'gestion': 2026,
            }
        )

    # -----------------------------------------------------------------
    # 8. INDICADORES Y OPERACIONES
    # -----------------------------------------------------------------
    print("\n--- INDICADORES Y OPERACIONES ---")
    from apps.indicadores.models import (
        Indicador, MetaProgramada, Operacion, Tarea, Producto,
        MedioVerificacion, Supuesto,
    )

    ind_data = [
        ('IND-001', 'km vias pavimentadas', 'km', 'acumulable', 2.5, 6.0),
        ('IND-002', 'Puentes rehabilitados', 'unidades', 'acumulable', 1, 2),
        ('IND-003', 'Personas con agua potable', 'personas', 'acumulable', 15000, 25000),
        ('IND-004', 'km alcantarillado', 'km', 'acumulable', 3.0, 6.0),
        ('IND-005', 'Mercados rehabilitados', 'unidades', 'acumulable', 2, 4),
        ('IND-006', 'Productores capacitados', 'personas', 'acumulable', 200, 400),
    ]
    indicadores = []
    for i, (cod, nombre, um, comportamiento, lb, meta) in enumerate(ind_data):
        ind = g(Indicador, codigo=cod, nombre=nombre,
                formula=f'({nombre} / Meta) x 100',
                unidad_medida=gb(UnidadMedida, defaults={'denominacion': um, 'gestion': 2026}, codigo=um[:3].upper()),
                tipo_comportamiento=comportamiento,
                linea_base=Decimal(str(lb)),
                anio_linea_base=2025,
                meta_anual=Decimal(str(meta)),
                medio_verificacion='Informes tecnicos y actas de recepcion',
                frecuencia_medicion='Trimestral',
                responsable=u_plan)
        indicadores.append(ind)

        MetaProgramada.objects.get_or_create(
            indicador=ind, gestion=2026, version=1,
            defaults={
                'meta_anual': Decimal(str(meta)),
                'trimestre1': Decimal(str(meta * 0.2)),
                'trimestre2': Decimal(str(meta * 0.25)),
                'trimestre3': Decimal(str(meta * 0.3)),
                'trimestre4': Decimal(str(meta * 0.25)),
            }
        )

        MedioVerificacion.objects.get_or_create(
            indicador=ind, nombre=f'MV-{cod}',
            defaults={'descripcion': f'Medio de verificacion para {nombre}', 'soporte_esperado': 'Fotos, informes, actas'}
        )

    # Operaciones y tareas
    op_data = [
        ('OP-001', 'Operacion de pavimentacion', to_obra, acps[0]),
        ('OP-002', 'Operacion de puentes', to_obra, acps[2]),
        ('OP-003', 'Operacion agua potable', to_obra, acps[1]),
        ('OP-004', 'Operacion alcantarillado', to_obra, acps[5]),
        ('OP-005', 'Operacion mercados', to_mantenimiento, acps[3]),
        ('OP-006', 'Operacion productores', to_capacitacion, acps[4]),
    ]
    ops = []
    for cod, nombre, tipo, acp in op_data:
        op = g(Operacion, accion_corto_plazo=acp, codigo=cod, nombre=nombre,
               tipo=tipo, fecha_inicio=date(2026, 1, 15), fecha_fin=date(2026, 11, 30))
        ops.append(op)
        for j in range(1, 3):
            g(Tarea, operacion=op, codigo=f'T-{cod[-3:]}-{j}',
              nombre=f'Tarea {j} de {nombre}')

    # Productos
    prod_data = [
        ('PRD-001', 'Vias pavimentadas y seguras', acps[0]),
        ('PRD-002', 'Puentes rehabilitados', acps[2]),
        ('PRD-003', 'Red de agua potable instalada', acps[1]),
        ('PRD-004', 'Red de alcantarillado operativa', acps[5]),
        ('PRD-005', 'Mercados modernos y funcionales', acps[3]),
        ('PRD-006', 'Productores capacitados en produccion', acps[4]),
    ]
    for cod, nombre, acp in prod_data:
        g(Producto, accion_corto_plazo=acp, codigo=cod, nombre=nombre,
          tipo='terminal', estado='acabado')

    # Supuestos
    sup_data = [
        ('Disponibilidad de materiales de construccion', 'Incremento de precios de materiales'),
        ('Estabilidad climatica favorables', 'Fenomenos meteorologicos extremos'),
        ('Aporte oportuno del IDH', 'Retraso en transferencias del IDH'),
        ('Capacidad operativa de la empresa contratista', 'Falta de empresas calificadas'),
        ('Participacion activa de productores', 'Desinteres de los beneficiarios'),
        ('Cumplimiento de normativa ambiental', 'Restricciones ambientales'),
    ]
    for i, (desc, riesgo) in enumerate(sup_data):
        g(Supuesto, accion_corto_plazo=acps[i], descripcion=desc,
          riesgo_externo=riesgo, probabilidad='Media')

    # -----------------------------------------------------------------
    # 9. ESTRUCTURA PRESUPUESTARIA
    # -----------------------------------------------------------------
    print("\n--- ESTRUCTURA PRESUPUESTARIA ---")
    from apps.presupuesto.models import (
        ProgramaPresupuestario, ProyectoPresupuestario,
        ActividadPresupuestaria, LineaPresupuestaria,
    )

    prog_infra = g(ProgramaPresupuestario, codigo='P-001',
                    nombre='Programa de Infraestructura Vial', gestion=2026, ue_responsable=ue_300)
    prog_serv = g(ProgramaPresupuestario, codigo='P-002',
                   nombre='Programa de Servicios Basicos', gestion=2026, ue_responsable=ue_200)
    prog_prod = g(ProgramaPresupuestario, codigo='P-003',
                   nombre='Programa de Desarrollo Productivo', gestion=2026, ue_responsable=ue_200)

    pry_1 = g(ProyectoPresupuestario, codigo='PRY-001', nombre='Mejoramiento vial urbano',
               programa=prog_infra, gestion=2026)
    pry_2 = g(ProyectoPresupuestario, codigo='PRY-002', nombre='Agua potable y saneamiento',
               programa=prog_serv, gestion=2026)
    pry_3 = g(ProyectoPresupuestario, codigo='PRY-003', nombre='Apoyo productivo local',
               programa=prog_prod, gestion=2026)

    act_11 = g(ActividadPresupuestaria, codigo='ACT-01', nombre='Pavimentacion de vias',
                proyecto=pry_1, gestion=2026)
    act_12 = g(ActividadPresupuestaria, codigo='ACT-02', nombre='Rehabilitacion de puentes',
                proyecto=pry_1, gestion=2026)
    act_21 = g(ActividadPresupuestaria, codigo='ACT-03', nombre='Instalacion de red de agua potable',
                proyecto=pry_2, gestion=2026)
    act_22 = g(ActividadPresupuestaria, codigo='ACT-04', nombre='Construccion de alcantarillado',
                proyecto=pry_2, gestion=2026)
    act_31 = g(ActividadPresupuestaria, codigo='ACT-05', nombre='Rehabilitacion de mercados',
                proyecto=pry_3, gestion=2026)
    act_32 = g(ActividadPresupuestaria, codigo='ACT-06', nombre='Capacitacion a productores',
                proyecto=pry_3, gestion=2026)

    # -----------------------------------------------------------------
    # 10. TECHOS PRESUPUESTARIOS
    # -----------------------------------------------------------------
    print("\n--- TECHOS PRESUPUESTARIOS ---")
    from apps.techos.models import TechoPresupuestario, DistribucionTecho

    t1 = g(TechoPresupuestario, gestion=2026, monto_total=Decimal('5000000'),
            fuente=ff_111, organismo=of_gob, descripcion='Techo recursos propios 2026')
    t2 = g(TechoPresupuestario, gestion=2026, monto_total=Decimal('2000000'),
            fuente=ff_121, organismo=of_gob, descripcion='Techo IDH 2026')
    t3 = g(TechoPresupuestario, gestion=2026, monto_total=Decimal('1000000'),
            fuente=ff_131, organismo=of_gob, descripcion='Techo Coparticipacion 2026')

    # Distribucion por DA
    for techo, monto_da1, monto_da2, monto_da3 in [
        (t1, 1500000, 2000000, 1500000),
        (t2, 500000, 800000, 700000),
        (t3, 300000, 400000, 300000),
    ]:
        g(DistribucionTecho, techo=techo, da=da_100, ue=ue_100, monto_asignado=Decimal(str(monto_da1)))
        g(DistribucionTecho, techo=techo, da=da_200, ue=ue_200, monto_asignado=Decimal(str(monto_da2)))
        g(DistribucionTecho, techo=techo, da=da_300, ue=ue_300, monto_asignado=Decimal(str(monto_da3)))

    # -----------------------------------------------------------------
    # 11. LINEAS PRESUPUESTARIAS
    # -----------------------------------------------------------------
    print("\n--- LINEAS PRESUPUESTARIAS ---")
    lp_data = [
        (prog_infra, pry_1, act_11, og_211, ff_111, 1500000),
        (prog_infra, pry_1, act_12, og_211, ff_111, 800000),
        (prog_serv, pry_2, act_21, og_211, ff_121, 1200000),
        (prog_serv, pry_2, act_22, og_211, ff_121, 600000),
        (prog_prod, pry_3, act_31, og_212, ff_131, 400000),
        (prog_prod, pry_3, act_32, og_132, ff_131, 200000),
    ]
    lineas = []
    for prog, pry, act, og, ff, monto in lp_data:
        lp = g(LineaPresupuestaria, gestion=2026, entidad='GAM',
               da=da_300 if prog == prog_infra else (da_200 if prog == prog_serv else da_200),
               ue=ue_300 if prog == prog_infra else ue_200,
               programa=prog, proyecto=pry, actividad=act,
               finalidad_funcion=ff_func_07 if prog == prog_prod else ff_func_06,
               fuente=ff, organismo=of_gob, objeto_gasto=og,
               importe=Decimal(str(monto)),
               operacion=ops[lp_data.index((prog, pry, act, og, ff, monto))])
        lineas.append(lp)

    # -----------------------------------------------------------------
    # 12. POAU - PLAN OPERATIVO ANUAL POR UNIDAD
    # -----------------------------------------------------------------
    print("\n--- POAU ---")
    from apps.poau.models import POAU, POAUActividad, EjecucionFisica, EjecucionFinanciera

    poau_data = [
        ('POAU-UPL-2026', 'POAU Unidad de Planificacion Estrategica 2026',
         uo_upl, resultados[0], 'aprobado', u_tecnico),
        ('POAU-UIP-2026', 'POAU Unidad de Inversion Publica 2026',
         uo_uip, resultados[2], 'enviado', u_jefe_obras),
        ('POAU-UMANT-2026', 'POAU Unidad de Mantenimiento 2026',
         uo_umant, resultados[4], 'borrador', u_tecnico),
    ]
    all_actividades = []
    for codigo, nombre, unidad, res, estado, resp in poau_data:
        poau = g(POAU, codigo=codigo, nombre=nombre, unidad=unidad,
                 producto_territorial=res.productos.first(),
                 gestion=2026, estado=estado, responsable=resp)

        # 3 actividades por POAU
        act_data = [
            (f'ACT-{codigo[-4:]}-01', f'Actividad 1 de {unidad.sigla}', Decimal('120'), Decimal('500000'), og_211),
            (f'ACT-{codigo[-4:]}-02', f'Actividad 2 de {unidad.sigla}', Decimal('80'), Decimal('300000'), og_132),
            (f'ACT-{codigo[-4:]}-03', f'Actividad 3 de {unidad.sigla}', Decimal('40'), Decimal('200000'), og_122),
        ]
        for act_cod, act_nom, meta, pres, og in act_data:
            act = g(POAUActividad, poau=poau, codigo=act_cod, nombre=act_nom,
                    objeto_gasto=og,
                    meta_fisica_anual=meta, presupuesto_anual=pres,
                    meta_q1=(meta * Decimal('0.2')).quantize(Decimal('0.0001')),
                    meta_q2=(meta * Decimal('0.25')).quantize(Decimal('0.0001')),
                    meta_q3=(meta * Decimal('0.3')).quantize(Decimal('0.0001')),
                    meta_q4=(meta * Decimal('0.25')).quantize(Decimal('0.0001')),
                    accion_corto_plazo=acps[0])
            all_actividades.append(act)

            # Ejecucion fisica trimestral
            for q, pct in [('2026-Q1', Decimal('0.9')), ('2026-Q2', Decimal('0.7')),
                           ('2026-Q3', Decimal('0.3')), ('2026-Q4', Decimal('0'))]:
                prog_val = (meta * {'2026-Q1': Decimal('0.25'), '2026-Q2': Decimal('0.25'),
                                    '2026-Q3': Decimal('0.25'), '2026-Q4': Decimal('0.25')}[q]).quantize(Decimal('0.0001'))
                ejec_val = (prog_val * pct).quantize(Decimal('0.0001'))
                EjecucionFisica.objects.get_or_create(
                    actividad=act, periodo=q,
                    defaults={'tipo_periodo': 'trimestral', 'programado': prog_val, 'ejecutado': ejec_val}
                )

            # Ejecucion financiera trimestral
            for q, pct in [('2026-Q1', Decimal('0.85')), ('2026-Q2', Decimal('0.65')),
                           ('2026-Q3', Decimal('0.25')), ('2026-Q4', Decimal('0'))]:
                prog_val = pres * {'2026-Q1': Decimal('0.25'), '2026-Q2': Decimal('0.25'),
                                   '2026-Q3': Decimal('0.25'), '2026-Q4': Decimal('0.25')}[q]
                ejec_val = (prog_val * pct).quantize(Decimal('0.01'))
                EjecucionFinanciera.objects.get_or_create(
                    actividad=act, periodo=q,
                    defaults={'tipo_periodo': 'trimestral', 'programado': prog_val, 'ejecutado': ejec_val}
                )

    # -----------------------------------------------------------------
    # 13. RESUMEN FINAL
    # -----------------------------------------------------------------
    print("\n" + "=" * 70)
    print("DATOS DEMO COMPLETADOS EXITOSAMENTE")
    print("=" * 70)
    print(f"  Catalogos:          {UnidadMedida.objects.count() + ObjetoGasto.objects.count() + FuenteFinanciamiento.objects.count()}")
    print(f"  Unidades org.:      {UnidadOrganizacional.objects.count()}")
    print(f"  Usuarios:           {Usuario.objects.count()}")
    print(f"  Roles:              {Rol.objects.count()}")
    print(f"  Planes:             {Plan.objects.count()}")
    print(f"  Nodos planif.:      {NodoPlanificacion.objects.count()}")
    print(f"  AMP:                {AccionMedianoPlazo.objects.count()}")
    print(f"  ACP:                {AccionCortoPlazo.objects.count()}")
    print(f"  PAD Resultados:     {ResultadoTerritorial.objects.count()}")
    print(f"  PAD Productos:      {ProductoTerritorial.objects.count()}")
    print(f"  Indicadores:        {Indicador.objects.count()}")
    print(f"  Operaciones:        {Operacion.objects.count()}")
    print(f"  Programas:          {ProgramaPresupuestario.objects.count()}")
    print(f"  Lineas presup.:     {LineaPresupuestaria.objects.count()}")
    print(f"  Techos:             {TechoPresupuestario.objects.count()}")
    print(f"  POAUs:              {POAU.objects.count()}")
    print(f"  Actividades POAU:   {POAUActividad.objects.count()}")
    print(f"  Ejecuciones fis.:   {EjecucionFisica.objects.count()}")
    print(f"  Ejecuciones fin.:   {EjecucionFinanciera.objects.count()}")
    techo_total = sum(t.monto_total for t in TechoPresupuestario.objects.filter(gestion=2026))
    print(f"  Techo total:        Bs {techo_total:,.2f}")
    print("\n  USUARIOS:")
    print("    admin@gamsacaba.gob.bo / admin2026")
    print("    mae@gamsacaba.gob.bo / mae2026")
    print("    planificador@gamsacaba.gob.bo / plan2026")
    print("    presupuesto@gamsacaba.gob.bo / pres2026")
    print("    jefe_plan@gamsacaba.gob.bo / jefe2026")
    print("    jefe_obras@gamsacaba.gob.bo / jefe2026")
    print("    tecnico@gamsacaba.gob.bo / tec2026")
    print("    auditor@gamsacaba.gob.bo / aud2026")
    print("=" * 70)
    print("Cadena PGDESA -> PDESA -> PTDI -> PEI -> POA -> POAU completa.")
    print("GAM Sacaba — Sistema Integrado de Planificacion.")
    print("=" * 70)
