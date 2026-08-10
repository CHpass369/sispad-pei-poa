"""Adaptador del SIS-PRO V2 (WP-11).

Importa ProyectoInversion legacy como semilla, y expone la cadena ascendente
Proyecto → POA → PEI → PAD → marco superior (plan §14.2) a partir de los
vínculos del SIS-POA V2 y del kernel estratégico.
"""
from apps.core.migration_audit import checksum_registro
from apps.core.models import LegacyMigrationMap
from apps.inversion.models import ProyectoInversion
from apps.inversion.models_v2 import FasesProyecto, Proyecto

# Equivalencia best-effort de etapas legacy → fases V2 del ciclo
MAPEO_ETAPA_FASE = {
    'idea': FasesProyecto.IDEA,
    'preinversion': FasesProyecto.PREINVERSION,
    'formulacion': FasesProyecto.FORMULACION,
    'ejecucion': FasesProyecto.EJECUCION,
    'cierre': FasesProyecto.CIERRE,
    'evaluacion': FasesProyecto.EVALUACION,
}


def importar_proyectos_v2(lote='sis-pro', dry_run=False, gestion=None):
    """Importa los proyectos legacy al modelo V2 con trazabilidad."""
    resumen = {'lote': lote, 'dry_run': dry_run, 'creados': 0, 'migrados': 0}

    qs = ProyectoInversion.objects.filter(activo=True)
    if gestion:
        qs = qs.filter(gestion_inicio=gestion)

    for legacy in qs.order_by('codigo_interno'):
        defaults = {
            'nombre': legacy.nombre,
            'descripcion': legacy.descripcion,
            'gestion': legacy.gestion_inicio,
            'fase': MAPEO_ETAPA_FASE.get(legacy.etapa, FasesProyecto.IDEA),
            'costo_total': legacy.costo_total,
            'ejecucion_acumulada': legacy.ejecucion_acumulada,
            'prioridad': legacy.prioridad,
            'codigo_sisin': legacy.codigo_sisin,
            'atributos': {'procedencia': 'importacion_legacy'},
        }
        if dry_run:
            resumen['creados'] += 1
            continue
        proyecto, creado = Proyecto.objects.get_or_create(
            codigo_interno=legacy.codigo_interno,
            defaults=defaults,
        )
        if creado:
            resumen['creados'] += 1
        entry, _ = LegacyMigrationMap.objects.get_or_create(
            app_legacy='inversion',
            modelo_legacy='proyectoinversion',
            uuid_legacy=legacy.pk,
            defaults={'lote': lote, 'checksum': checksum_registro(legacy)},
        )
        entry.tipo_destino = 'Proyecto'
        entry.uuid_destino = proyecto.pk
        entry.estado = LegacyMigrationMap.Estados.MIGRADO
        entry.lote = lote
        entry.save()
        resumen['migrados'] += 1

    return resumen


def cadena_ascendente(proyecto):
    """Traza la cadena del proyecto hacia la estrategia (plan §14.2).

    Proyecto → Actividad → Operación → Acción → POA → Versión PEI →
    Instrumento PEI (y, vía vínculos del kernel, hacia PAD/marco superior).
    """
    pasos = [
        {
            'tipo': 'proyecto',
            'codigo': proyecto.codigo_interno,
            'nombre': proyecto.nombre,
        },
    ]
    vinculo = proyecto.vinculos_actividad.select_related(
        'actividad__operacion__accion__poa__version_pei',
    ).first()
    if not vinculo:
        return pasos
    actividad = vinculo.actividad
    operacion = actividad.operacion
    accion = operacion.accion
    poa = accion.poa
    pasos.extend([
        {'tipo': 'actividad', 'codigo': actividad.codigo, 'nombre': actividad.nombre},
        {'tipo': 'operacion', 'codigo': operacion.codigo, 'nombre': operacion.nombre},
        {'tipo': 'accion_corto_plazo', 'codigo': accion.codigo, 'nombre': accion.nombre},
        {'tipo': 'poa', 'codigo': poa.codigo, 'nombre': poa.nombre},
    ])
    version_pei = poa.version_pei
    if version_pei:
        instrumento = version_pei.instrumento
        pasos.append({
            'tipo': 'version_pei',
            'codigo': f'{instrumento.codigo} v{version_pei.numero}',
            'nombre': instrumento.nombre,
        })
        # Hacia el marco superior a través de los vínculos del kernel
        for vinculo_kernel in version_pei.vinculos.select_related(
            'destino__version__instrumento',
        )[:3]:
            destino = vinculo_kernel.destino
            pasos.append({
                'tipo': 'articulacion',
                'codigo': destino.codigo,
                'nombre': (
                    f'{destino.nombre} → '
                    f'{destino.version.instrumento.codigo}'
                ),
            })
    return pasos
