"""Servicios del dominio de preinversión SIS-PRO (SISPRE / RM 115).

Clasificación de tipología, inicialización de ITCP/TDR/EDTP, validaciones
de aprobación, cálculo de madurez y paquete de transferencia a SISPOA.
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from .models_preinversion import (
    CondicionITCP,
    EDTP,
    EstadoCondicion,
    EstadosDocumentoPreinversion,
    ITCP,
    SeccionEDTP,
    TDR,
)
from .section_catalog import secciones_para
from .models_v2 import EstadosExpedientePreinversion, TipologiaRM115

REGLA_CLASIFICACION = {
    'PUENTE': TipologiaRM115.TIPO_II,
    'CAMINO': TipologiaRM115.TIPO_II,
    'RIEGO': TipologiaRM115.TIPO_II,
    'POZO': TipologiaRM115.TIPO_III,
    'AGUA': TipologiaRM115.TIPO_III,
    'ALCANTARILLADO': TipologiaRM115.TIPO_III,
    'TINGLADO': TipologiaRM115.TIPO_III,
    'UNIDAD EDUCATIVA': TipologiaRM115.TIPO_III,
    'MURO': TipologiaRM115.TIPO_III,
    'SOFTWARE': TipologiaRM115.TIPO_IV,
    'SISTEMA': TipologiaRM115.TIPO_IV,
    'INVESTIGACION': TipologiaRM115.TIPO_V,
}

CONDICIONES_ITCP = [
    ('derecho_propietario', 'Derecho propietario', True),
    ('uso_suelo', 'Compatibilidad de uso de suelo', True),
    ('terceros', 'Derecho de vía / afectaciones', True),
    ('riesgo', 'Riesgos no mitigables', True),
    ('competencia_institucional', 'Competencia institucional', True),
]

PESOS_MADUREZ = {
    'identidad': Decimal('10'),
    'alineamiento': Decimal('10'),
    'localizacion': Decimal('10'),
    'itcp': Decimal('20'),
    'tdr': Decimal('10'),
    'edtp': Decimal('25'),
    'documentos': Decimal('5'),
    'aprobaciones': Decimal('10'),
}

UMBRAL_MADUREZ_POA = Decimal('90')


def clasificar_tipologia(proyecto):
    """Sugiere tipología RM 115 según el nombre/clase del proyecto."""
    texto = f'{proyecto.nombre} {proyecto.descripcion}'.upper()
    for palabra, tipologia in REGLA_CLASIFICACION.items():
        if palabra in texto:
            return tipologia
    return TipologiaRM115.TIPO_III


@transaction.atomic
def inicializar_itcp(proyecto, usuario=None):
    """Crea el ITCP con sus condiciones y el TDR (Parte B)."""
    itcp, creado = ITCP.objects.get_or_create(
        proyecto=proyecto, defaults={'created_by': usuario},
    )
    if creado or not itcp.condiciones.exists():
        for orden, (categoria, titulo, critica) in enumerate(CONDICIONES_ITCP, start=1):
            CondicionITCP.objects.get_or_create(
                itcp=itcp, categoria=categoria,
                defaults={
                    'proyecto': proyecto, 'titulo': titulo,
                    'critica': critica, 'orden': orden, 'created_by': usuario,
                },
            )
    else:
        # Sincronizar el checklist: eliminar condiciones que ya no forman parte
        # del catálogo vigente (p. ej. tras cambios de negocio en RM 115).
        catalogadas = {categoria for categoria, _, _ in CONDICIONES_ITCP}
        itcp.condiciones.exclude(categoria__in=catalogadas).delete()
        for orden, (categoria, titulo, critica) in enumerate(CONDICIONES_ITCP, start=1):
            condicion, _ = CondicionITCP.objects.get_or_create(
                itcp=itcp, categoria=categoria,
                defaults={
                    'proyecto': proyecto, 'titulo': titulo,
                    'critica': critica, 'orden': orden, 'created_by': usuario,
                },
            )
            condicion.titulo = titulo
            condicion.critica = critica
            condicion.orden = orden
            condicion.save(update_fields=['titulo', 'critica', 'orden'])
    if proyecto.estado_preinversion in [
        EstadosExpedientePreinversion.REGISTRADA,
        EstadosExpedientePreinversion.ADMITIDA,
    ]:
        proyecto.estado_preinversion = EstadosExpedientePreinversion.ITCP_ELABORACION
        proyecto.save(update_fields=['estado_preinversion', 'updated_at'])
    TDR.objects.get_or_create(proyecto=proyecto, defaults={'created_by': usuario})
    return itcp


@transaction.atomic
def inicializar_edtp(proyecto, usuario=None):
    """Crea el EDTP con secciones dinámicas por tipología RM 115."""
    itcp = getattr(proyecto, 'itcp', None)
    if itcp is None or itcp.estado != EstadosDocumentoPreinversion.APROBADO:
        raise ValidationError(
            'El ITCP debe estar aprobado antes de iniciar el EDTP'
        )
    tdr = getattr(proyecto, 'tdr', None)
    if tdr is None or tdr.presupuesto_referencial is None:
        raise ValidationError(
            'Se requieren TDR y presupuesto referencial del EDTP'
        )
    edtp, creado = EDTP.objects.get_or_create(
        proyecto=proyecto, defaults={'created_by': usuario},
    )
    if creado or not edtp.secciones.exists():
        for orden, (codigo, titulo, requerida) in enumerate(
            secciones_para(proyecto.tipologia_rm115), start=1
        ):
            SeccionEDTP.objects.get_or_create(
                edtp=edtp, codigo=codigo,
                defaults={
                    'titulo': titulo, 'requerida': requerida,
                    'orden': orden, 'created_by': usuario,
                },
            )
    proyecto.estado_preinversion = EstadosExpedientePreinversion.EDTP_ELABORACION
    proyecto.save(update_fields=['estado_preinversion', 'updated_at'])
    return edtp


def validar_itcp_para_aprobacion(itcp):
    """Regla de negocio `ITCP_APROBADO` (RM 115)."""
    errores = []
    sin_resolver = itcp.condiciones.filter(critica=True).exclude(
        estado__in=EstadoCondicion.RESUELTAS,
    )
    if sin_resolver.exists():
        errores.append(
            f'Existen {sin_resolver.count()} condiciones críticas sin resolver'
        )
    tdr = getattr(itcp.proyecto, 'tdr', None)
    if tdr is None:
        errores.append('No existe TDR del EDTP')
    elif tdr.presupuesto_referencial is None:
        errores.append('El presupuesto referencial del EDTP no está definido')
    if not itcp.conclusiones or not itcp.recomendaciones:
        errores.append('Conclusiones y recomendaciones son obligatorias')
    return errores


def validar_edtp_para_aprobacion(edtp):
    """Regla de negocio `EDTP_APROBADO` (RM 115)."""
    errores = []
    faltantes = edtp.secciones.filter(requerida=True, aplicable=True).exclude(
        estado=EstadosDocumentoPreinversion.APROBADO,
    )
    if faltantes.exists():
        errores.append(
            f'Existen {faltantes.count()} secciones obligatorias sin aprobar'
        )
    if edtp.estudios_tecnicos.filter(requerido=True).exclude(
        estado=EstadosDocumentoPreinversion.APROBADO,
    ).exists():
        errores.append('Existen estudios técnicos obligatorios sin aprobar')
    total_costo = sum(
        (item.subtotal for item in edtp.items_costo.all()), Decimal('0')
    )
    total_financiamiento = sum(
        (f.monto for f in edtp.fuentes_financiamiento.all()), Decimal('0')
    )
    if total_costo and abs(total_costo - total_financiamiento) > Decimal('0.01'):
        errores.append('El costo de inversión no coincide con el financiamiento')
    pom = getattr(edtp, 'plan_om', None)
    if pom and pom.costo_operacion_anual == 0 and pom.costo_mantenimiento_anual == 0:
        if not pom.justificacion_costo_cero:
            errores.append(
                'Los costos de operación y mantenimiento están en cero sin justificación'
            )
    return errores


def calcular_madurez(proyecto):
    """Puntaje de madurez 0-100 y habilitación para POA (SISPOA)."""
    puntaje = Decimal('0')
    if proyecto.nombre and proyecto.gestion and proyecto.responsable_id:
        puntaje += PESOS_MADUREZ['identidad']
    if proyecto.problema and proyecto.objetivo_general and proyecto.tipologia_rm115:
        puntaje += PESOS_MADUREZ['alineamiento']
    if proyecto.geom and proyecto.distrito:
        puntaje += PESOS_MADUREZ['localizacion']
    itcp = getattr(proyecto, 'itcp', None)
    if itcp:
        condiciones = itcp.condiciones.all()
        if condiciones.exists():
            resueltas = condiciones.filter(estado__in=EstadoCondicion.RESUELTAS).count()
            puntaje += (
                PESOS_MADUREZ['itcp'] * Decimal(resueltas) / Decimal(condiciones.count())
            )
    tdr = getattr(proyecto, 'tdr', None)
    if tdr and tdr.presupuesto_referencial is not None:
        puntaje += PESOS_MADUREZ['tdr']
    edtp = getattr(proyecto, 'edtp', None)
    if edtp:
        secciones = edtp.secciones.filter(requerida=True)
        if secciones.exists():
            puntaje += (
                PESOS_MADUREZ['edtp']
                * Decimal(secciones.filter(estado=EstadosDocumentoPreinversion.APROBADO).count())
                / Decimal(secciones.count())
            )
    if proyecto.documentos_preinv.exists():
        puntaje += PESOS_MADUREZ['documentos']
    if proyecto.aprobaciones.filter(estado='aprobado').exists():
        puntaje += PESOS_MADUREZ['aprobaciones']

    puntaje = min(puntaje, Decimal('100'))
    proyecto.puntaje_madurez = puntaje
    proyecto.habilitado_poa = (
        proyecto.estado_preinversion
        in [
            EstadosExpedientePreinversion.EDTP_APROBADO,
            EstadosExpedientePreinversion.VIABLE,
        ]
        and puntaje >= UMBRAL_MADUREZ_POA
        and not proyecto.observaciones.filter(
            estado='abierta', severidad='critica',
        ).exists()
    )
    if proyecto.habilitado_poa:
        proyecto.estado_preinversion = EstadosExpedientePreinversion.HABILITADO_POA
    proyecto.save(update_fields=[
        'puntaje_madurez', 'habilitado_poa', 'estado_preinversion', 'updated_at',
    ])
    return proyecto.puntaje_madurez


def construir_paquete_transferencia(proyecto):
    """Paquete de solo lectura para SISPOA (JSON + GeoJSON + documentos)."""
    geometria = None
    if proyecto.geom:
        import json

        geometria = json.loads(
            proyecto.geom.transform(4326, clone=True).geojson
        )
    paquete = {
        'schema_version': '1.0',
        'project_id': str(proyecto.id),
        'project_code': proyecto.codigo_interno,
        'official_name': proyecto.nombre,
        'management_year': proyecto.gestion,
        'status': proyecto.estado_preinversion,
        'rm115_typology': proyecto.tipologia_rm115,
        'district_code': proyecto.distrito,
        'community_name': proyecto.comunidad,
        'geometry': geometria,
        'problem_statement': proyecto.problema,
        'general_objective': proyecto.objetivo_general,
        'approved_budget': str(proyecto.presupuesto_aprobado or ''),
        'currency': proyecto.moneda,
        'readiness_score': str(proyecto.puntaje_madurez),
        'components': [
            {
                'id': str(c.id), 'code': c.codigo, 'name': c.nombre,
                'target': str(c.meta_fisica or ''), 'unit': c.unidad,
                'budget': str(c.presupuesto),
            }
            for c in proyecto.componentes.all()
        ],
        'beneficiaries': [
            {
                'type': b.tipo, 'description': b.descripcion,
                'quantity': b.cantidad, 'unit': b.unidad,
            }
            for b in proyecto.grupos_beneficiarios.all()
        ],
        'documents': [
            {
                'id': str(d.id), 'type': d.tipo_documento, 'title': d.titulo,
                'status': d.estado, 'version': d.version_actual,
            }
            for d in proyecto.documentos_preinv.all()
        ],
    }
    edtp = getattr(proyecto, 'edtp', None)
    if edtp:
        paquete['edtp'] = {
            'version': edtp.version,
            'viability_result': edtp.resultado_viabilidad,
            'evaluation_method': edtp.metodo_evaluacion,
            'financing': [
                {
                    'code': f.codigo_fuente, 'name': f.nombre_fuente,
                    'amount': str(f.monto), 'confirmed': f.confirmada,
                }
                for f in edtp.fuentes_financiamiento.all()
            ],
        }
    return paquete
