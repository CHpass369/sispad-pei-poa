"""Adaptador de migración del SIS-POA al modelo V2 (WP-10 / plan §FASE 10).

Importa la cadena operativa legacy (articulacion.AccionPOA → OperacionPOAU →
ActividadPOAU → TareaPOAU) a la jerarquía canónica V2, con trazabilidad en
LegacyMigrationMap y reporte de duplicidades (indicadores vs articulacion).
"""
from django.db.models import Sum

from apps.articulacion.models import (
    AccionPOA,
    ActividadPOAU,
    OperacionPOAU,
    TareaPOAU,
)
from apps.core.migration_audit import checksum_registro
from apps.core.models import LegacyMigrationMap
from apps.poau.models_v2 import (
    AccionCortoPlazo,
    Actividad,
    EstadosPoA,
    Operacion,
    PoAInstitucional,
    ProgramacionActividad,
    Tarea,
)

NIVELES_POA = [
    ('AccionPOA', 'accion'),
    ('OperacionPOAU', 'operacion'),
    ('ActividadPOAU', 'actividad'),
    ('TareaPOAU', 'tarea'),
]


def _padre_v2(obj, por_nivel):
    for campo, nivel in (('accion_poa', 'accion'),
                         ('operacion', 'operacion'),
                         ('actividad', 'actividad')):
        if hasattr(obj, campo):
            padre = getattr(obj, campo)
            if padre:
                return por_nivel[nivel].get(padre.pk)
    return None


def importar_poa_v2(lote='poa', dry_run=False, gestion=None):
    """Importa la jerarquía POA legacy a los modelos V2 del SIS-POA."""
    resumen = {
        'lote': lote,
        'dry_run': dry_run,
        'poas': [],
        'creados': 0,
        'migraciones': 0,
    }

    gestiones = list(
        AccionPOA.objects.values_list('gestion', flat=True).distinct().order_by()
    )
    if gestion:
        gestiones = [g for g in gestiones if g == gestion]

    for g in gestiones:
        if dry_run:
            poa = PoAInstitucional(
                codigo=f'P-{g}', gestion=g, nombre=f'POA {g}',
            )
        else:
            poa, _ = PoAInstitucional.objects.get_or_create(
                codigo=f'P-{g}',
                defaults={
                    'gestion': g,
                    'nombre': f'POA Institucional {g}',
                },
            )

        resumen_poa = 0
        for accion in AccionPOA.objects.filter(gestion=g):
            accion_v2, _ = _crear_instancia('accion', poa, None, accion, dry_run)
            if not dry_run:
                _registrar_mapa(AccionPOA, accion, accion_v2, lote, dry_run)
                resumen['migraciones'] += 1
            resumen['creados'] += 1
            resumen_poa += 1
            for operacion in OperacionPOAU.objects.filter(accion_poa=accion):
                operacion_v2, _ = _crear_instancia(
                    'operacion', poa, accion_v2, operacion, dry_run,
                )
                if not dry_run:
                    _registrar_mapa(OperacionPOAU, operacion, operacion_v2, lote, dry_run)
                    resumen['migraciones'] += 1
                resumen['creados'] += 1
                resumen_poa += 1
                for actividad in ActividadPOAU.objects.filter(operacion=operacion):
                    actividad_v2, _ = _crear_instancia(
                        'actividad', poa, operacion_v2, actividad, dry_run,
                    )
                    if not dry_run:
                        _registrar_mapa(ActividadPOAU, actividad, actividad_v2, lote, dry_run)
                        resumen['migraciones'] += 1
                    resumen['creados'] += 1
                    resumen_poa += 1
                    for tarea in TareaPOAU.objects.filter(actividad=actividad):
                        tarea_v2, _ = _crear_instancia(
                            'tarea', poa, actividad_v2, tarea, dry_run,
                        )
                        if not dry_run:
                            _registrar_mapa(TareaPOAU, tarea, tarea_v2, lote, dry_run)
                            resumen['migraciones'] += 1
                        resumen['creados'] += 1
                        resumen_poa += 1
        resumen['poas'].append({
            'codigo': f'P-{g}', 'gestion': g, 'elementos': resumen_poa,
        })

    return resumen


def _crear_instancia(nivel, poa, padre, obj, dry_run):
    atributos = {}
    for campo in ('presupuesto_programado', 'meta_gestion', 'meta_anual',
                  'total_programado', 'responsable'):
        if hasattr(obj, campo):
            valor = getattr(obj, campo)
            if valor is not None and valor != '':
                atributos[campo] = str(valor)

    nombre = obj.denominacion if hasattr(obj, 'denominacion') else str(obj)
    if nivel == 'accion':
        codigo = obj.codigo_accion
    elif nivel == 'operacion':
        codigo = obj.codigo_operacion
    elif nivel == 'actividad':
        codigo = obj.codigo_actividad
    else:
        codigo = obj.codigo_tarea

    defaults = {
        'nombre': nombre,
        'atributos': atributos,
        'estado': EstadosPoA.BORRADOR,
    }
    if nivel == 'accion':
        return _get_or_create(AccionCortoPlazo, {'poa': poa, 'codigo': codigo}, defaults, dry_run)
    if nivel == 'operacion':
        return _get_or_create(Operacion, {'accion': padre, 'codigo': codigo}, defaults, dry_run)
    if nivel == 'actividad':
        return _get_or_create(Actividad, {'operacion': padre, 'codigo': codigo}, defaults, dry_run)
    return _get_or_create(Tarea, {'actividad': padre, 'codigo': codigo}, defaults, dry_run)


def _get_or_create(modelo, lookup, defaults, dry_run):
    if dry_run:
        return modelo(**lookup, **defaults), True
    instancia, creado = modelo.objects.get_or_create(
        **lookup, defaults=defaults,
    )
    return instancia, creado


def _registrar_mapa(modelo, obj, destino, lote, dry_run):
    if dry_run:
        return
    entry, _ = LegacyMigrationMap.objects.get_or_create(
        app_legacy='articulacion',
        modelo_legacy=modelo._meta.model_name,
        uuid_legacy=obj.pk,
        defaults={'lote': lote, 'checksum': checksum_registro(obj)},
    )
    entry.tipo_destino = destino.__class__.__name__
    entry.uuid_destino = destino.pk
    entry.estado = LegacyMigrationMap.Estados.MIGRADO
    entry.lote = lote
    entry.save()


def resumen_presupuesto(poa):
    """Proyección: programado/ejecutado físico y financiero del POA."""
    programaciones = ProgramacionActividad.objects.filter(
        actividad__operacion__accion__poa=poa,
    ).values('tipo').annotate(
        programado=Sum('programado'),
        ejecutado=Sum('ejecutado'),
    )
    resumen = {
        'poa': str(poa.id),
        'codigo': poa.codigo,
        'gestion': poa.gestion,
        'fisica': {'programado': '0', 'ejecutado': '0'},
        'financiera': {'programado': '0', 'ejecutado': '0'},
        'actividades': poa.acciones.count(),
    }
    for fila in programaciones:
        tipo = fila['tipo']
        resumen[tipo] = {
            'programado': str(fila['programado'] or 0),
            'ejecutado': str(fila['ejecutado'] or 0),
        }
    return resumen


def validar_techo(poa):
    """Valida el formulado financiero contra el techo de la gestión (si existe)."""
    from decimal import Decimal
    from apps.techos.models import TechoPresupuestario

    financiero = resumen_presupuesto(poa)['financiera']
    formulado = Decimal(financiero['programado'])
    techo = TechoPresupuestario.objects.filter(
        gestion=poa.gestion,
    ).aggregate(total=Sum('monto_total'))['total'] or Decimal('0')
    if techo and formulado > techo:
        return {
            'excede': True,
            'techo': str(techo),
            'formulado': str(formulado),
            'mensaje': 'El formulado financiero excede el techo presupuestario.',
        }
    return {
        'excede': False,
        'techo': str(techo),
        'formulado': str(formulado),
        'mensaje': 'Formulado dentro del techo.',
    }


def comparar_duplicados_poa():
    """Reporte de duplicidades operación/tarea: articulacion vs indicadores."""
    from apps.indicadores.models import Operacion as OperacionInd, Tarea as TareaInd

    def _norm(texto):
        return ' '.join(str(texto or '').strip().lower().split())

    def _comparar(qs_art, qs_ind, campo_art, campo_ind, nombre_art, nombre_ind):
        codigos_art = set(qs_art.values_list(campo_art, flat=True))
        codigos_ind = set(qs_ind.values_list(campo_ind, flat=True))
        comunes = codigos_art & codigos_ind
        nombres_art = {
            c: _norm(getattr(o, nombre_art))
            for o in qs_art if (c := getattr(o, campo_art))
        }
        nombres_ind = {
            c: _norm(getattr(o, nombre_ind))
            for o in qs_ind if (c := getattr(o, campo_ind))
        }
        return {
            'articulacion': len(codigos_art),
            'indicadores': len(codigos_ind),
            'coinciden_codigo_y_nombre': sum(
                1 for c in comunes
                if nombres_art.get(c) and nombres_art[c] == nombres_ind.get(c)
            ),
        }

    return {
        'operaciones': _comparar(
            OperacionPOAU.objects.all(), OperacionInd.objects.all(),
            'codigo_operacion', 'codigo', 'denominacion', 'nombre',
        ),
        'tareas': _comparar(
            TareaPOAU.objects.all(), TareaInd.objects.all(),
            'codigo_tarea', 'codigo', 'denominacion', 'nombre',
        ),
    }
