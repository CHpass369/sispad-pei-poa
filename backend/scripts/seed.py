"""Idempotent demo data for the SISPOA modules.

Run from ``backend/`` with::

    python manage.py shell -c "exec(open('scripts/seed.py').read())"

All records created by this script use deterministic demo keys.  The script
only creates or updates those keys; it never performs a global delete.
"""

import os
from datetime import date, datetime
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Rol, Usuario
from apps.articulacion.models import (
    AcuerdoInternacional,
    AccionPOA,
    ActividadPOAU,
    ArticulacionPADPEI,
    CodigoNivel,
    LineamientoPAD,
    OperacionPOAU,
    ProductoPAD,
    ProductoPEI,
    ResultadoPAD,
    ResultadoPEI,
    SeguimientoPresupuesto,
    TareaPOAU,
    AsignacionObjetoGasto,
)
from apps.catalogos.models import (
    FinalidadFuncion,
    FuenteFinanciamiento,
    ObjetoGasto,
    OrganismoFinanciador,
    TipoOperacion,
    TipoProducto,
    UnidadMedida,
)
from apps.gestion.models import GestionFiscal
from apps.notificaciones.models import PreferenciaNotificacion
from apps.organizacion.models import (
    AsignacionUsuarioUnidad,
    DireccionAdministrativa,
    TipoUnidad,
    UnidadEjecutora,
    UnidadOrganizacional,
)
from apps.pad.models import SectorPAD
from apps.planificacion.models import (
    ArticulacionPlanificacion as PlanArticulacion,
    NodoPlanificacion,
    Plan,
)
from apps.presupuesto.models import (
    ActividadPresupuestaria,
    LineaPresupuestaria,
    ProgramaPresupuestario,
    ProyectoPresupuestario,
)
from apps.techos.models import DistribucionTecho, TechoPresupuestario
from apps.workflow.models import EnvioFormulacion, Revision


DEMO_YEAR = 2026
DEMO_END_YEAR = 2030
DEMO_DATE = date(DEMO_YEAR, 1, 1)
DEMO_DESCRIPTION = 'Dato demo simulado para revisión funcional; no es información oficial.'


ROLES = [
    ('superadmin', 'Superadministrador Técnico'),
    ('admin_poa', 'Administrador POA'),
    ('admin_presupuesto', 'Administrador de Presupuesto'),
    ('responsable_unidad', 'Responsable POA de Unidad'),
    ('revisor_planificacion', 'Revisor de Planificación'),
    ('revisor_presupuesto', 'Revisor de Presupuesto'),
    ('revisor_inversion', 'Revisor de Proyectos'),
    ('revisor_juridico', 'Revisor Jurídico'),
    ('mae', 'Máxima Autoridad Ejecutiva'),
    ('auditor', 'Auditor'),
    ('seguimiento', 'Responsable de Seguimiento'),
    ('consulta', 'Usuario de Consulta'),
    ('control_social', 'Participación y Control Social'),
]

DEMO_USERS = {
    'admin': {
        'email': 'admin@demo.sispoa.local',
        'first_name': 'Administrador',
        'last_name': 'Demo SISPOA',
        'cargo': 'Administrador del sistema (demo)',
        'roles': ('superadmin', 'admin_poa'),
        'is_staff': True,
        'is_superuser': True,
    },
    'mae': {
        'email': 'mae@demo.sispoa.local',
        'first_name': 'Máxima Autoridad',
        'last_name': 'Ejecutiva Demo',
        'cargo': 'Máxima Autoridad Ejecutiva (demo)',
        'roles': ('mae',),
    },
    'planificador': {
        'email': 'planificador@demo.sispoa.local',
        'first_name': 'Planificador',
        'last_name': 'Demo',
        'cargo': 'Responsable de planificación (demo)',
        'roles': ('revisor_planificacion', 'responsable_unidad'),
    },
    'presupuesto': {
        'email': 'presupuesto@demo.sispoa.local',
        'first_name': 'Analista de Presupuesto',
        'last_name': 'Demo',
        'cargo': 'Responsable de presupuesto (demo)',
        'roles': ('admin_presupuesto', 'revisor_presupuesto'),
    },
    'tecnico': {
        'email': 'tecnico@demo.sispoa.local',
        'first_name': 'Técnico',
        'last_name': 'Demo',
        'cargo': 'Técnico de unidad (demo)',
        'roles': ('responsable_unidad',),
    },
    'seguimiento': {
        'email': 'seguimiento@demo.sispoa.local',
        'first_name': 'Responsable de Seguimiento',
        'last_name': 'Demo',
        'cargo': 'Responsable de seguimiento (demo)',
        'roles': ('seguimiento', 'responsable_unidad'),
    },
    'auditor': {
        'email': 'auditor@demo.sispoa.local',
        'first_name': 'Auditor',
        'last_name': 'Demo',
        'cargo': 'Auditor interno (demo)',
        'roles': ('auditor',),
    },
}

DEMO_PASSWORD_ENV = {
    'admin': 'SISPOA_DEMO_ADMIN_PASSWORD',
    'mae': 'SISPOA_DEMO_MAE_PASSWORD',
    'planificador': 'SISPOA_DEMO_PLANNING_PASSWORD',
    'presupuesto': 'SISPOA_DEMO_BUDGET_PASSWORD',
    'tecnico': 'SISPOA_DEMO_TECHNICAL_PASSWORD',
    'seguimiento': 'SISPOA_DEMO_MONITORING_PASSWORD',
    'auditor': 'SISPOA_DEMO_AUDITOR_PASSWORD',
}


def _load_demo_passwords():
    missing = [name for name in DEMO_PASSWORD_ENV.values() if not os.environ.get(name)]
    if missing:
        raise RuntimeError(
            'Missing required demo seed environment variables: ' + ', '.join(missing)
        )
    return {
        account: os.environ[env_name]
        for account, env_name in DEMO_PASSWORD_ENV.items()
    }

SECTORS = [
    ('01', 'Salud'),
    ('02', 'Deportes'),
    ('03', 'Educación'),
    ('04', 'Culturas'),
    ('05', 'Justicia'),
    ('06', 'Seguridad ciudadana'),
    ('07', 'Defensa'),
    ('08', 'Urbanismo y vivienda'),
    ('09', 'Transportes'),
    ('10', 'Telecomunicaciones y tecnologías de información'),
    ('11', 'Medio ambiente'),
    ('12', 'Recursos hídricos'),
    ('13', 'Saneamiento básico'),
    ('14', 'Agropecuario'),
    ('15', 'Industria'),
    ('16', 'Comercio'),
    ('17', 'Turismo'),
    ('18', 'Minería'),
    ('19', 'Hidrocarburos'),
    ('20', 'Energía'),
]

ODS = [
    ('01', 'Fin de la pobreza'),
    ('02', 'Hambre cero'),
    ('03', 'Salud y bienestar'),
    ('04', 'Educación de calidad'),
    ('05', 'Igualdad de género'),
    ('06', 'Agua limpia y saneamiento'),
    ('07', 'Energía asequible y no contaminante'),
    ('08', 'Trabajo decente y crecimiento económico'),
    ('09', 'Industria, innovación e infraestructura'),
    ('10', 'Reducción de las desigualdades'),
    ('11', 'Ciudades y comunidades sostenibles'),
    ('12', 'Producción y consumo responsables'),
    ('13', 'Acción por el clima'),
    ('14', 'Vida submarina'),
    ('15', 'Vida de ecosistemas terrestres'),
    ('16', 'Paz, justicia e instituciones sólidas'),
    ('17', 'Alianzas para lograr los objetivos'),
]

PGDESA_AXES = [
    'Erradicación de la pobreza',
    'Desarrollo social universal',
    'Desarrollo económico y productivo',
    'Desarrollo integral del hábitat',
    'Desarrollo de las capacidades productivas',
    'Gestión de riesgos y cambio climático',
    'Gestión institucional y participación social',
]

PDESA_COMPONENTS = [
    'Desarrollo normativo institucional',
    'Fortalecimiento de capacidades institucionales',
    'Planificación y gestión territorial',
    'Infraestructura productiva',
    'Desarrollo agropecuario',
    'Seguridad alimentaria',
    'Promoción del empleo digno',
    'Fomento a la micro y pequeña empresa',
    'Turismo sostenible',
    'Desarrollo industrial',
    'Energías renovables',
    'Conectividad vial',
    'Agua potable y saneamiento',
    'Vivienda social',
    'Gestión de residuos sólidos',
    'Protección de cuencas y recursos hídricos',
    'Conservación de la biodiversidad',
    'Educación y capacitación técnica',
    'Salud preventiva',
    'Cultura y deporte',
    'Participación ciudadana',
    'Transparencia y lucha contra la corrupción',
    'Gestión de riesgos',
    'Desarrollo urbano sostenible',
]


def _upsert_non_unique(model, lookup, defaults):
    """Upsert a legacy model whose schema does not enforce the business key."""
    instance = model.objects.filter(**lookup).order_by('pk').first()
    if instance is None:
        return model.objects.create(**lookup, **defaults), True
    changed = False
    for field, value in defaults.items():
        if getattr(instance, field) != value:
            setattr(instance, field, value)
            changed = True
    if changed:
        instance.save()
    return instance, False


def _catalog(model, codigo, denominacion, descripcion=DEMO_DESCRIPTION):
    return model.objects.update_or_create(
        codigo=codigo,
        gestion=DEMO_YEAR,
        defaults={
            'denominacion': denominacion,
            'descripcion': descripcion,
            'activo': True,
            'fecha_vigencia_desde': DEMO_DATE,
            'fecha_vigencia_hasta': date(DEMO_END_YEAR, 12, 31),
            'metadatos_importacion': {'demo': True, 'fuente': 'seed reproducible'},
        },
    )[0]


def _ensure_plan(codigo, tipo, nombre, gestion_fin):
    plan, _ = Plan.objects.get_or_create(
        codigo=codigo,
        tipo=tipo,
        defaults={
            'nombre': nombre,
            'gestion_inicio': DEMO_YEAR,
            'gestion_fin': gestion_fin,
            'descripcion': DEMO_DESCRIPTION,
            'fecha_vigencia_desde': DEMO_DATE,
            'fecha_vigencia_hasta': date(gestion_fin, 12, 31),
        },
    )
    if not plan.descripcion:
        plan.descripcion = DEMO_DESCRIPTION
        plan.save(update_fields=['descripcion', 'updated_at'])
    return plan


def _ensure_node(plan, codigo, nivel, nombre, orden, padre=None):
    return NodoPlanificacion.objects.update_or_create(
        plan=plan,
        codigo=codigo,
        nivel=nivel,
        defaults={
            'padre': padre,
            'nombre': nombre,
            'descripcion': DEMO_DESCRIPTION,
            'gestion': DEMO_YEAR,
            'orden': orden,
            'activo': True,
        },
    )[0]


def _seed_roles_and_users(passwords):
    roles = {}
    for order, (codigo, nombre) in enumerate(ROLES, 1):
        roles[codigo], _ = Rol.objects.update_or_create(
            codigo=codigo,
            defaults={
                'nombre': nombre,
                'descripcion': f'{nombre} — rol demo',
                'es_sistema': True,
                'activo': True,
                'orden': order,
            },
        )

    users = {}
    for key, data in DEMO_USERS.items():
        user, _ = Usuario.objects.get_or_create(
            email=data['email'],
            defaults={
                'first_name': data['first_name'],
                'last_name': data['last_name'],
                'cargo': data['cargo'],
                'is_staff': data.get('is_staff', False),
                'is_superuser': data.get('is_superuser', False),
                'activo': True,
                'debe_cambiar_password': False,
            },
        )
        user.first_name = data['first_name']
        user.last_name = data['last_name']
        user.cargo = data['cargo']
        user.is_staff = data.get('is_staff', False)
        user.is_superuser = data.get('is_superuser', False)
        user.activo = True
        user.debe_cambiar_password = False
        user.set_password(passwords[key])
        user.save()
        user.roles.set([roles[codigo] for codigo in data['roles']])
        users[key] = user
    return roles, users


def _seed_gestion_and_organization(users):
    gestion, _ = GestionFiscal.objects.update_or_create(
        anio=DEMO_YEAR,
        defaults={
            'estado': GestionFiscal.Estado.ABIERTA,
            'descripcion': 'Gestión fiscal demo para revisión funcional del sistema.',
            'anio_inicio_plurianual': DEMO_YEAR,
            'anio_fin_plurianual': DEMO_END_YEAR,
            'fecha_apertura': timezone.make_aware(datetime(DEMO_YEAR, 1, 1)),
            'activa': True,
            'creado_por': users['admin'],
        },
    )

    tipos = {}
    for codigo, nombre, nivel in [
        ('INST', 'Institución demo', 1),
        ('SEC', 'Secretaría demo', 2),
        ('DIR', 'Dirección demo', 3),
        ('UE', 'Unidad ejecutora demo', 4),
    ]:
        tipos[codigo], _ = TipoUnidad.objects.update_or_create(
            codigo=codigo,
            defaults={'nombre': nombre, 'nivel': nivel, 'activo': True},
        )

    institucion, _ = UnidadOrganizacional.objects.update_or_create(
        codigo='ORG-DEMO',
        gestion=DEMO_YEAR,
        defaults={
            'nombre': 'Gobierno Autónomo Municipal Demo',
            'sigla': 'GAM-DEMO',
            'tipo': tipos['INST'],
            'responsable': users['mae'],
            'fecha_vigencia_desde': DEMO_DATE,
            'fecha_vigencia_hasta': date(DEMO_END_YEAR, 12, 31),
            'activo': True,
            'orden': 1,
        },
    )
    unidad_plan, _ = UnidadOrganizacional.objects.update_or_create(
        codigo='DIR-DEMO',
        gestion=DEMO_YEAR,
        defaults={
            'nombre': 'Dirección de Planificación Demo',
            'sigla': 'DPL-DEMO',
            'tipo': tipos['DIR'],
            'padre': institucion,
            'responsable': users['planificador'],
            'fecha_vigencia_desde': DEMO_DATE,
            'fecha_vigencia_hasta': date(DEMO_END_YEAR, 12, 31),
            'activo': True,
            'orden': 1,
        },
    )
    unidad_operativa, _ = UnidadOrganizacional.objects.update_or_create(
        codigo='UE-DEMO',
        gestion=DEMO_YEAR,
        defaults={
            'nombre': 'Unidad Operativa Demo',
            'sigla': 'UOP-DEMO',
            'tipo': tipos['UE'],
            'padre': institucion,
            'responsable': users['tecnico'],
            'fecha_vigencia_desde': DEMO_DATE,
            'fecha_vigencia_hasta': date(DEMO_END_YEAR, 12, 31),
            'activo': True,
            'orden': 2,
        },
    )
    da, _ = DireccionAdministrativa.objects.update_or_create(
        codigo='DA-DEMO',
        gestion=DEMO_YEAR,
        defaults={
            'nombre': 'Dirección Administrativa Demo',
            'responsable': users['presupuesto'],
            'fecha_vigencia_desde': DEMO_DATE,
            'fecha_vigencia_hasta': date(DEMO_END_YEAR, 12, 31),
            'activo': True,
        },
    )
    ue, _ = UnidadEjecutora.objects.update_or_create(
        codigo='UE-DEMO',
        da=da,
        gestion=DEMO_YEAR,
        defaults={
            'nombre': 'Unidad Ejecutora Demo',
            'unidad_organizacional': unidad_operativa,
            'responsable': users['presupuesto'],
            'fecha_vigencia_desde': DEMO_DATE,
            'fecha_vigencia_hasta': date(DEMO_END_YEAR, 12, 31),
            'activo': True,
        },
    )
    for user_key, unidad, responsable in [
        ('planificador', unidad_plan, True),
        ('tecnico', unidad_operativa, True),
        ('seguimiento', unidad_operativa, False),
        ('presupuesto', unidad_plan, False),
    ]:
        AsignacionUsuarioUnidad.objects.update_or_create(
            usuario=users[user_key],
            unidad=unidad,
            gestion=DEMO_YEAR,
            defaults={'es_responsable_poa': responsable, 'activo': True},
        )
    return gestion, institucion, unidad_plan, unidad_operativa, da, ue


def _seed_catalogs(ue):
    source = _catalog(FuenteFinanciamiento, 'FF-DEMO', 'Recursos propios demo')
    organism = _catalog(OrganismoFinanciador, 'OF-DEMO', 'Organismo financiador demo')
    object_expense = _catalog(ObjetoGasto, 'OG-DEMO', 'Servicios generales demo')
    purpose = _catalog(FinalidadFuncion, 'FIN-DEMO', 'Finalidad social demo')
    unit_measure = _catalog(UnidadMedida, 'UM-DEMO', 'Unidad demo')
    operation_type = _catalog(TipoOperacion, 'TOP-DEMO', 'Operación sustantiva demo')
    product_type = _catalog(TipoProducto, 'TP-DEMO', 'Producto institucional demo')
    program, _ = ProgramaPresupuestario.objects.update_or_create(
        codigo='P-DEMO-01',
        gestion=DEMO_YEAR,
        defaults={
            'nombre': 'Programa demo de servicios municipales',
            'descripcion': DEMO_DESCRIPTION,
            'ue_responsable': ue,
            'activo': True,
        },
    )
    project, _ = ProyectoPresupuestario.objects.update_or_create(
        codigo='PR-DEMO-01',
        programa=program,
        gestion=DEMO_YEAR,
        defaults={'nombre': 'Proyecto demo de articulación', 'activo': True},
    )
    activity, _ = ActividadPresupuestaria.objects.update_or_create(
        codigo='ACT-DEMO-01',
        proyecto=project,
        gestion=DEMO_YEAR,
        defaults={'nombre': 'Actividad presupuestaria demo', 'activo': True},
    )
    return {
        'source': source,
        'organism': organism,
        'object_expense': object_expense,
        'purpose': purpose,
        'unit_measure': unit_measure,
        'operation_type': operation_type,
        'product_type': product_type,
        'program': program,
        'project': project,
        'activity': activity,
    }


def _seed_catalogs_and_plans():
    sectors = {}
    for codigo, nombre in SECTORS:
        sectors[codigo], _ = SectorPAD.objects.update_or_create(
            codigo=codigo,
            defaults={'nombre': nombre},
        )

    ods = {}
    for codigo, denominacion in ODS:
        ods[codigo], _ = _upsert_non_unique(
            AcuerdoInternacional,
            {'tipo_acuerdo': 'ODS', 'codigo': codigo},
            {
                'denominacion': denominacion,
                'rango_valido': 'ODS 1-17',
                'es_codigo_oficial': True,
                'activo': True,
            },
        )

    codigo_padre = CodigoNivel.objects.filter(nivel='Entidad').first()
    if codigo_padre is None:
        codigo_padre, _ = CodigoNivel.objects.get_or_create(
            nivel='Entidad',
            defaults={
                'codigo_nivel': '01',
                'segmentos': 'ENT',
                'longitud': '4',
                'ejemplo': '0001',
                'regla_generacion': 'Código demo de entidad.',
                'editable': False,
                'vigencia': 'Demo',
            },
        )
    CodigoNivel.objects.update_or_create(
        nivel='Resultado PAD',
        defaults={
            'codigo_nivel': '10',
            'segmentos': 'CGEO.LL.RR',
            'longitud': '6+2+2',
            'codigo_padre': codigo_padre,
            'ejemplo': '031001.01.01',
            'regla_generacion': 'CGEO fijo + lineamiento de dos dígitos + resultado de dos dígitos.',
            'editable': True,
            'vigencia': '2026-2030',
        },
    )
    plan_pgdesa = _ensure_plan(
        'PGDESA-2026-2050',
        'pgdesa',
        'PGDESA demo simulado 2026-2050',
        2050,
    )
    plan_pdesa = _ensure_plan(
        'PDESA-2026-2030',
        'pdesa',
        'PDESA demo simulado 2026-2030',
        2030,
    )
    ejes = []
    resultados_superiores = []
    for eje_index, eje_nombre in enumerate(PGDESA_AXES, 1):
        eje = _ensure_node(
            plan_pgdesa,
            f'{eje_index:02d}',
            'eje',
            f'{eje_nombre} (demo)',
            eje_index,
        )
        ejes.append(eje)
        for meta_index in range(1, 4):
            meta = _ensure_node(
                plan_pgdesa,
                f'{eje.codigo}.{meta_index:02d}',
                'meta',
                f'Meta demo {eje.codigo}.{meta_index:02d} - {eje_nombre}',
                meta_index,
                eje,
            )
            for result_index in range(1, 3):
                resultado = _ensure_node(
                    plan_pgdesa,
                    f'{meta.codigo}.{result_index:02d}',
                    'resultado',
                    f'Resultado superior demo {meta.codigo}.{result_index:02d}',
                    result_index,
                    meta,
                )
                resultados_superiores.append(resultado)

    componentes = []
    acciones_pdesa = []
    for component_index, component_name in enumerate(PDESA_COMPONENTS, 1):
        component = _ensure_node(
            plan_pdesa,
            f'{component_index:02d}',
            'componente',
            f'{component_name} (demo)',
            component_index,
        )
        componentes.append(component)
        action_count = 3 if component_index % 2 else 2
        for action_index in range(1, action_count + 1):
            acciones_pdesa.append(
                _ensure_node(
                    plan_pdesa,
                    f'{component.codigo}.{action_index:02d}',
                    'accion',
                    f'Acción demo {component.codigo}.{action_index:02d} - {component_name}',
                    action_index,
                    component,
                )
            )
    for index, resultado in enumerate(resultados_superiores):
        PlanArticulacion.objects.update_or_create(
            nodo_origen=resultado,
            nodo_destino=componentes[index % len(componentes)],
            gestion=DEMO_YEAR,
            defaults={'es_principal': True},
        )
    return sectors, ods, plan_pgdesa, plan_pdesa, ejes, componentes, acciones_pdesa


def _seed_pad(sectors, ods, acciones_pdesa):
    lineamientos = {}
    for index, (codigo, _) in enumerate(SECTORS, 1):
        lineamientos[codigo], _ = _upsert_non_unique(
            LineamientoPAD,
            {'codigo': codigo},
            {
                'denominacion': f'Lineamiento PAD demo para {sectors[codigo].nombre}',
                'codigo_padre': '',
                'gestion_desde': DEMO_YEAR,
                'gestion_hasta': DEMO_END_YEAR,
                'activo': True,
            },
        )

    codigo_nivel = CodigoNivel.objects.get(nivel='Resultado PAD')
    if codigo_nivel.segmentos != 'CGEO.LL.RR':
        raise ValueError('Resultado PAD requiere el nivel de código CGEO.LL.RR')

    resultados = []
    productos = []
    for lineamiento_index, (lineamiento_code, _) in enumerate(SECTORS, 1):
        lineamiento = lineamientos[lineamiento_code]
        sector = sectors[lineamiento_code]
        for result_index in range(1, 4):
            codigo_resultado = f'031001.{lineamiento_code}.{result_index:02d}'
            action = acciones_pdesa[(lineamiento_index * 3 + result_index - 1) % len(acciones_pdesa)]
            resultado, _ = ResultadoPAD.objects.update_or_create(
                codigo_resultado=codigo_resultado,
                vigencia_desde=DEMO_YEAR,
                defaults={
                    'id_cadena': f'{codigo_resultado}-{DEMO_YEAR}',
                    'denominacion': (
                        f'Resultado PAD demo {lineamiento_code}.{result_index:02d}: '
                        f'{sector.nombre.lower()} con servicios articulados'
                    ),
                    'lineamiento_pad': lineamiento.codigo,
                    'territorializacion': 'Municipio demo de Sacaba',
                    'responsable_pad': 'Unidad de planificación demo',
                    'vigencia_hasta': DEMO_END_YEAR,
                    'cod_geografico': '031001',
                    'eta': 'Gobierno Autónomo Municipal Demo (simulado)',
                    'cod_eje_pgdesa': f'{((lineamiento_index - 1) % 7) + 1:02d}',
                    'objetivo_impacto': DEMO_DESCRIPTION,
                    'cod_componente_pdesa': action.padre.codigo,
                    'nodo_pdesa': action,
                    'objetivo_efecto': DEMO_DESCRIPTION,
                    'cod_sector': sector.codigo,
                    'sector': sector.nombre,
                    'cod_resultado_pds': f'DEMO-{lineamiento_code}-{result_index:02d}',
                    'resultado_pds': 'Resultado sectorial demo simulado.',
                    'estado': 'REFERENCIAL',
                },
            )
            resultado.acuerdo_ods.set([ods[f'{((lineamiento_index - 1) % 17) + 1:02d}']])
            resultados.append(resultado)
            for product_index in range(1, 3):
                producto, _ = ProductoPAD.objects.update_or_create(
                    codigo_producto=f'{codigo_resultado}.{product_index:02d}',
                    resultado_pad=resultado,
                    defaults={
                        'denominacion': (
                            f'Producto PAD demo {codigo_resultado}.{product_index:02d} '
                            f'para {sector.nombre.lower()}'
                        ),
                        'territorializacion': 'Municipio demo de Sacaba',
                        'responsable': 'Unidad ejecutora demo',
                    },
                )
                productos.append(producto)
    return resultados, productos, lineamientos


def _seed_pei_poa(productos_pad, unit, catalogs, plan_pei):
    resultados_pei = []
    productos_pei = []
    for result_index in range(1, 21):
        resultado, _ = ResultadoPEI.objects.update_or_create(
            codigo_resultado=f'{result_index:02d}.01',
            vigencia_desde=DEMO_YEAR,
            defaults={
                'denominacion': f'Resultado PEI demo {result_index:02d} - servicios municipales',
                'cod_entidad': '031001',
                'entidad': 'Gobierno Autónomo Municipal Demo',
                'cod_oei': f'OEI-{result_index:02d}',
                'vigencia_hasta': DEMO_END_YEAR,
            },
        )
        resultados_pei.append(resultado)
        for product_index in range(1, 4):
            producto, _ = ProductoPEI.objects.update_or_create(
                codigo_producto=f'{result_index:02d}.01.{product_index:02d}',
                resultado_pei=resultado,
                defaults={
                    'denominacion': f'Producto PEI demo {result_index:02d}.{product_index:02d}',
                    'cod_programa_presup': catalogs['program'].codigo,
                    'programa_presup': catalogs['program'].nombre,
                },
            )
            productos_pei.append(producto)

    acciones = []
    for index, producto_pei in enumerate(productos_pei, 1):
        accion, _ = AccionPOA.objects.update_or_create(
            codigo_accion=f'{producto_pei.codigo_producto}.01',
            defaults={
                'denominacion': f'Acción POA demo para {producto_pei.denominacion}',
                'resultado_esperado': 'Producto anual demo entregado.',
                'producto_pei': producto_pei,
                'indicador': f'Porcentaje de avance del producto {index}',
                'formula': 'ejecutado / programado * 100',
                'unidad_medida': catalogs['unit_measure'].denominacion,
                'linea_base': Decimal('0'),
                'meta_gestion': Decimal('100'),
                'cargo_responsable': 'Responsable de unidad demo',
                'fecha_inicio': DEMO_DATE,
                'fecha_fin': date(DEMO_YEAR, 12, 31),
                'tipo_operacion': catalogs['operation_type'].denominacion,
                'categoria_programatica': catalogs['program'].codigo,
                'programa': catalogs['program'].nombre,
                'actividad_presupuestaria': catalogs['activity'].codigo,
                'presupuesto_programado': Decimal('250000.00'),
                'fuente_financiamiento': catalogs['source'].codigo,
                'organismo_financiador': catalogs['organism'].codigo,
                'medio_verificacion': 'Reporte de seguimiento demo.',
                'riesgo': 'Riesgo operativo demo controlado.',
                'gestion': DEMO_YEAR,
                'unidad_responsable': unit,
                'estado': 'REFERENCIAL',
            },
        )
        acciones.append(accion)

    for index, producto_pad in enumerate(productos_pad):
        producto_pei = productos_pei[index % len(productos_pei)]
        ArticulacionPADPEI.objects.update_or_create(
            producto_pad=producto_pad,
            producto_pei=producto_pei,
            defaults={
                'tipo_contribucion': 'Directa demo',
                'ponderacion': Decimal('50.00'),
                'justificacion': DEMO_DESCRIPTION,
                'estado': 'REFERENCIAL',
            },
        )

    return resultados_pei, productos_pei, acciones


def _seed_poau_and_tracking(acciones, users, catalogs):
    operaciones = []
    actividades = []
    tareas = []
    for index, accion in enumerate(acciones, 1):
        operacion, _ = OperacionPOAU.objects.update_or_create(
            codigo_operacion=f'{accion.codigo_accion}.01',
            defaults={
                'denominacion': f'Operación POAU demo {index:03d}',
                'tipo_operacion': 'SUSTANTIVA DEMO',
                'producto_entregable': 'Entregable demo verificable.',
                'accion_poa': accion,
                'unidad_ejecutora': 'UE-DEMO',
                'codigo_unidad_ejecutora': 'UE-DEMO',
                'responsable': users['tecnico'].get_full_name(),
                'codigo_responsable': 'USR-DEMO',
                'meta_anual': Decimal('1'),
                'indicador': 'Porcentaje de operación completada',
                'unidad_medida': catalogs['unit_measure'].denominacion,
                'fecha_inicio': DEMO_DATE,
                'fecha_fin': date(DEMO_YEAR, 12, 31),
                'programacion_mensual': {'2026-01': 0, '2026-06': 0.5, '2026-12': 1},
                'total_programado': Decimal('1'),
                'medio_verificacion': 'Acta demo y reporte de seguimiento.',
                'requerimientos': 'Recursos humanos demo.',
                'riesgo': 'Demora operativa demo.',
                'estado': 'REFERENCIAL',
            },
        )
        actividad, _ = ActividadPOAU.objects.update_or_create(
            codigo_actividad=f'{operacion.codigo_operacion}.01',
            defaults={
                'denominacion': f'Actividad POAU demo {index:03d}',
                'operacion': operacion,
                'producto_entregable': 'Actividad demo ejecutada.',
                'meta_anual': Decimal('1'),
                'indicador': 'Actividad completada',
                'unidad_medida': catalogs['unit_measure'].denominacion,
                'fecha_inicio': DEMO_DATE,
                'fecha_fin': date(DEMO_YEAR, 12, 31),
                'programacion_mensual': {'2026-01': 0, '2026-06': 0.5, '2026-12': 1},
                'total_programado': Decimal('1'),
                'medio_verificacion': 'Informe demo de actividad.',
                'requerimientos': 'Coordinación con unidad demo.',
                'riesgo': 'Sin riesgo crítico demo.',
                'estado': 'REFERENCIAL',
            },
        )
        tarea, _ = TareaPOAU.objects.update_or_create(
            codigo_tarea=f'{actividad.codigo_actividad}.01',
            defaults={
                'denominacion': f'Tarea POAU demo {index:03d}',
                'actividad': actividad,
                'responsable': users['tecnico'].get_full_name(),
                'fecha_inicio': DEMO_DATE,
                'fecha_fin': date(DEMO_YEAR, 12, 31),
                'metas': Decimal('1'),
                'programacion_mensual': {'2026-06': 0.5, '2026-12': 1},
                'requerimientos': 'Equipo demo.',
                'evidencia': 'Evidencia demostrativa simulada.',
                'estado': 'REFERENCIAL',
            },
        )
        operaciones.append(operacion)
        actividades.append(actividad)
        tareas.append(tarea)

    return operaciones, actividades, tareas


def _seed_budget_and_evaluation(
    acciones,
    operaciones,
    actividades,
    tareas,
    unit,
    da,
    ue,
    catalogs,
):
    # W-real 4R: desde 0004 el techo es 1:1 con GestionFiscal (NOT NULL);
    # sin esto el seed revienta tras la migración. get_or_create reutiliza
    # la gestión ya sembrada por _seed_gestion_and_organization.
    gestion_fiscal, _ = GestionFiscal.objects.get_or_create(anio=DEMO_YEAR)
    techo, _ = TechoPresupuestario.objects.get_or_create(
        gestion=DEMO_YEAR,
        gestion_fiscal=gestion_fiscal,
        fuente=catalogs['source'],
        organismo=catalogs['organism'],
        defaults={
            'monto_total': Decimal('15000000.00'),
            'descripcion': DEMO_DESCRIPTION,
            'activo': True,
            'version': 1,
        },
    )
    DistribucionTecho.objects.get_or_create(
        techo=techo,
        programa=catalogs['program'],
        defaults={
            'da': da,
            'ue': ue,
            'unidad': unit,
            'monto_asignado': Decimal('250000.00'),
            'monto_reserva': Decimal('25000.00'),
            'activo': True,
        },
    )
    LineaPresupuestaria.objects.get_or_create(
        gestion=DEMO_YEAR,
        entidad='DEMO',
        da=da,
        ue=ue,
        programa=catalogs['program'],
        proyecto=catalogs['project'],
        actividad=catalogs['activity'],
        finalidad_funcion=catalogs['purpose'],
        fuente=catalogs['source'],
        organismo=catalogs['organism'],
        objeto_gasto=catalogs['object_expense'],
        defaults={
            'importe': Decimal('250000.00'),
            'importe_plurianual': Decimal('750000.00'),
            'activo': True,
            'version': 1,
        },
    )
    AsignacionObjetoGasto.objects.update_or_create(
        codigo_asignacion='DEMO-0001',
        gestion=DEMO_YEAR,
        defaults={
            'accion_poa': acciones[0],
            'operacion': operaciones[0],
            'actividad': actividades[0],
            'tarea': tareas[0],
            'categoria_programatica': catalogs['program'].codigo,
            'da': da.codigo,
            'ue': ue.codigo,
            'programa': catalogs['program'].codigo,
            'proyecto_sisin': 'SISIN-DEMO-01',
            'actividad_presup': catalogs['activity'].codigo,
            'cod_objeto_gasto': catalogs['object_expense'].codigo,
            'descripcion_objeto': catalogs['object_expense'].denominacion,
            'grupo_gasto': '20000',
            'tipo_gasto': 'Corriente demo',
            'fuente_financiamiento': catalogs['source'].codigo,
            'organismo_financiador': catalogs['organism'].codigo,
            'monto_programado': Decimal('250000.00'),
            'monto_vigente': Decimal('250000.00'),
            'justificacion': DEMO_DESCRIPTION,
            'memoria_calculo': 'Base demo de cálculo presupuestario.',
            'estado': 'REFERENCIAL',
        },
    )
    SeguimientoPresupuesto.objects.update_or_create(
        id_cadena='SP-DEMO-2026-01',
        defaults={
            'gestion': DEMO_YEAR,
            'accion_poa': acciones[0],
            'operacion': operaciones[0],
            'actividad': actividades[0],
            'tarea': tareas[0],
            'categoria_programatica': catalogs['program'].codigo,
            'da': da.codigo,
            'ue': ue.codigo,
            'programa': catalogs['program'].codigo,
            'proyecto_sisin': 'SISIN-DEMO-01',
            'actividad_presup': catalogs['activity'].codigo,
            'tipo_gasto': 'Corriente demo',
            'presupuesto_inicial': Decimal('250000.00'),
            'presupuesto_vigente': Decimal('250000.00'),
            'ejecucion_mensual': {'2026-01': 0, '2026-06': 112500},
            'ejecutado_total': Decimal('112500.00'),
            'porcentaje_ejecucion_financiera': Decimal('45.00'),
            'meta_fisica': Decimal('1'),
            'ejecucion_fisica': Decimal('0.45'),
            'porcentaje_ejecucion_fisica': Decimal('45.00'),
            'eficacia': Decimal('90.00'),
            'eficiencia': Decimal('90.00'),
            'evidencia': 'Reporte de avance demo simulado.',
            'fecha_actualizacion': date(DEMO_YEAR, 6, 30),
            'estado': 'REFERENCIAL',
        },
    )


def _seed_notifications_and_workflow(unit, users):
    PreferenciaNotificacion.objects.update_or_create(
        user=users['seguimiento'],
        defaults={'receive_internal': True, 'receive_email': False, 'frequency': 'inmediata'},
    )
    envio, _ = EnvioFormulacion.objects.get_or_create(
        unidad=unit,
        gestion=DEMO_YEAR,
        version=1,
        defaults={
            'enviado_por': users['planificador'],
            'comentario': 'Envío de formulación demo para validar workflow.',
            'estado_anterior': 'borrador',
            'activo': True,
        },
    )
    revision, _ = Revision.objects.get_or_create(
        envio=envio,
        tipo_revision='planificacion',
        defaults={
            'revisor': users['planificador'],
            'estado': 'en_curso',
        },
    )


@transaction.atomic
def seed_demo_data():
    """Create the complete, repeatable demonstration dataset."""
    passwords = _load_demo_passwords()
    _, users = _seed_roles_and_users(passwords)
    _, _, unit_plan, unit_operativa, da, ue = _seed_gestion_and_organization(users)
    catalogs = _seed_catalogs(ue)
    sectors, ods, _, _, _, _, acciones_pdesa = _seed_catalogs_and_plans()
    resultados_pad, productos_pad, _ = _seed_pad(sectors, ods, acciones_pdesa)
    plan_pei = _ensure_plan('PEI-DEMO-2026', 'pei', 'PEI demo simulado 2026-2028', 2028)
    resultados_pei, productos_pei, acciones = _seed_pei_poa(
        productos_pad,
        unit_plan,
        catalogs,
        plan_pei,
    )
    operaciones, actividades, tareas = _seed_poau_and_tracking(
        acciones,
        users,
        catalogs,
    )
    _seed_budget_and_evaluation(
        acciones,
        operaciones,
        actividades,
        tareas,
        unit_operativa,
        da,
        ue,
        catalogs,
    )
    _seed_notifications_and_workflow(unit_operativa, users)

    counts = {
        'usuarios_demo': len(DEMO_USERS),
        'sectores_pad': len(sectors),
        'ods': len(ods),
        'resultados_pad': len(resultados_pad),
        'productos_pad': len(productos_pad),
        'resultados_pei': len(resultados_pei),
        'productos_pei': len(productos_pei),
        'acciones_poa': len(acciones),
        'operaciones_poau': len(operaciones),
        'actividades_poau': len(actividades),
        'tareas_poau': len(tareas),
    }
    print('Semilla demo ejecutada correctamente.')
    for key, value in counts.items():
        print(f'  - {key}: {value}')
    return counts


if __name__ in {'__main__', 'django.core.management.commands.shell'}:
    seed_demo_data()
