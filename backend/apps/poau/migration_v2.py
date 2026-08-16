"""Adaptador de migración del SIS-POA al modelo V2 (WP-10 / plan §FASE 10).

Importa la cadena operativa legacy (articulacion.AccionPOA → OperacionPOAU →
ActividadPOAU → TareaPOAU) a la jerarquía canónica V2, con trazabilidad en
LegacyMigrationMap y reporte de duplicidades (indicadores vs articulacion).

Contratos de idempotencia y verificación (PIP-PE-004):
  * Re-ejecución sobre datos sin cambios = no-op (``saltar`` por elemento).
  * Si el origen cambió (checksum distinto al almacenado en LegacyMigrationMap),
    se re-sincronizan nombre/atributos/estado en V2 y se actualiza el checksum.
  * Cada gestión se procesa en una transacción atómica: un error a mitad de
    lote revierte esa gestión sin dejar estados parciales.
  * ``dry_run``/``check`` nunca escriben: reportan la acción prevista por
    elemento (crear/actualizar/saltar) y las discrepancias detectadas.
  * Limitación de checksum por corrida: ``LegacyMigrationMap`` solo guarda un
    ``checksum`` (campo único), por lo que no se conserva el historial de
    checksums por corrida; cada sincronización sobrescribe el valor actual.
"""
from django.db import transaction
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

# Mapeo de estados articulacion → poau V2 (PIP-PE-001 §5). Configurable por
# el parámetro ``mapa_estados`` de ``importar_poa_v2`` o ``--estados`` del
# comando de gestión.
MAPA_ESTADOS_ORIGEN_V2 = {
    'REFERENCIAL': EstadosPoA.BORRADOR,
    'ENVIADO': EstadosPoA.EN_REVISION,
    'APROBADO': EstadosPoA.APROBADO,
    'OBSERVADO': EstadosPoA.OBSERVADO,
}

# Estado V2 asignado ante un estado de origen desconocido (se reporta en
# ``resumen['estados_desconocidos']``).
ESTADO_DESCONOCIDO_V2 = EstadosPoA.BORRADOR

MODELO_V2_POR_NIVEL = {
    'accion': (AccionCortoPlazo, 'poa'),
    'operacion': (Operacion, 'accion'),
    'actividad': (Actividad, 'operacion'),
    'tarea': (Tarea, 'actividad'),
}


def importar_poa_v2(lote='poa', dry_run=False, gestion=None, check=False,
                    mapa_estados=None):
    """Importa la jerarquía POA legacy a los modelos V2 del SIS-POA.

    Args:
        lote: nombre del lote de migración para ``LegacyMigrationMap``.
        dry_run: no escribe; reporta la acción prevista por elemento.
        gestion: filtra la(s) gestión(es) a procesar (None = todas).
        check: modo verificación; sin escritura (igual que dry_run) y expone
            el detalle de discrepancias (origen cambió → qué reescribiría).
        mapa_estados: dict estado origen → estado V2; default
            ``MAPA_ESTADOS_ORIGEN_V2``.
    """
    if check:
        dry_run = True
    mapa_estados = dict(mapa_estados or MAPA_ESTADOS_ORIGEN_V2)
    resumen = {
        'lote': lote,
        'dry_run': dry_run,
        'check': check,
        'poas': [],
        'creados': 0,
        'actualizados': 0,
        'saltados': 0,
        'migraciones': 0,
        'errores': [],
        'discrepancias': [],
        'estados_desconocidos': [],
    }

    gestiones = list(
        AccionPOA.objects.values_list('gestion', flat=True).distinct().order_by()
    )
    if gestion:
        gestiones = [g for g in gestiones if g == gestion]

    for g in gestiones:
        try:
            with transaction.atomic():
                resumen_poa = _importar_gestion(
                    g, lote, dry_run, mapa_estados, resumen,
                )
        except Exception as exc:  # noqa: BLE001 - el puente no debe abortar todo el lote
            resumen['errores'].append({'gestion': g, 'error': str(exc)})
            continue
        resumen['poas'].append({
            'codigo': f'P-{g}', 'gestion': g, 'elementos': resumen_poa,
        })

    return resumen


def _importar_gestion(g, lote, dry_run, mapa_estados, resumen):
    poa = _sincronizar_poa(g, dry_run)
    resumen_poa = 0
    for accion in AccionPOA.objects.filter(gestion=g):
        accion_v2 = _procesar_nivel(
            'accion', poa, None, accion, lote, dry_run, mapa_estados, resumen,
        )
        resumen_poa += 1
        for operacion in OperacionPOAU.objects.filter(accion_poa=accion):
            operacion_v2 = _procesar_nivel(
                'operacion', poa, accion_v2, operacion, lote, dry_run,
                mapa_estados, resumen,
            )
            resumen_poa += 1
            for actividad in ActividadPOAU.objects.filter(operacion=operacion):
                actividad_v2 = _procesar_nivel(
                    'actividad', poa, operacion_v2, actividad, lote, dry_run,
                    mapa_estados, resumen,
                )
                resumen_poa += 1
                for tarea in TareaPOAU.objects.filter(actividad=actividad):
                    _procesar_nivel(
                        'tarea', poa, actividad_v2, tarea, lote, dry_run,
                        mapa_estados, resumen,
                    )
                    resumen_poa += 1
    return resumen_poa


def _procesar_nivel(nivel, poa, padre, obj, lote, dry_run, mapa_estados, resumen):
    """Crea o re-sincroniza el elemento V2 para un registro legacy de origen.

    Decide por checksum del origen vs ``LegacyMigrationMap``: ``saltar`` si el
    origen no cambió (no-op idempotente), ``crear`` si no hay entrada, y
    ``actualizar`` si el origen cambió (re-sincroniza campos y estado).
    """
    codigo = _codigo_origen(nivel, obj)
    modelo, campo_padre = MODELO_V2_POR_NIVEL[nivel]
    lookup = {campo_padre: (padre if padre is not None else poa), 'codigo': codigo}
    expected = {
        'nombre': _nombre_origen(obj),
        'atributos': _atributos_origen(obj),
        'estado': _estado_v2(obj, mapa_estados, resumen),
    }

    accion = _accion_para_origen(obj)

    if dry_run:
        existente = modelo.objects.filter(**lookup).first()
        if accion == 'actualizar':
            resumen['discrepancias'].append({
                'nivel': nivel,
                'modelo_legacy': obj._meta.model_name,
                'uuid_legacy': str(obj.pk),
                'codigo': codigo,
                'campos_a_reescribir': _campos_diferentes(existente, expected),
            })
        _contar(accion, resumen)
        return modelo(**lookup, **expected)

    destino = _sync_v2(modelo, lookup, expected, accion)
    _registrar_mapa(obj, destino, lote, accion)
    _contar(accion, resumen)
    resumen['migraciones'] += 1
    return destino


def _contar(accion, resumen):
    if accion == 'crear':
        resumen['creados'] += 1
    elif accion == 'actualizar':
        resumen['actualizados'] += 1
    else:
        resumen['saltados'] += 1


def _accion_para_origen(obj):
    """Acción prevista comparando el checksum del origen con el mapa.

    ``crear``: sin entrada en LegacyMigrationMap.
    ``actualizar``: el origen cambió (checksum distinto).
    ``saltar``: origen sin cambios (no-op idempotente).
    """
    entry = LegacyMigrationMap.objects.filter(
        app_legacy='articulacion',
        modelo_legacy=obj._meta.model_name,
        uuid_legacy=obj.pk,
    ).first()
    checksum = checksum_registro(obj)
    if entry is None:
        return 'crear'
    if entry.checksum != checksum:
        return 'actualizar'
    return 'saltar'


def _sync_v2(modelo, lookup, expected, accion):
    """Crea/actualiza la instancia V2 según la acción decidida por checksum."""
    if accion == 'saltar':
        instancia = modelo.objects.filter(**lookup).first()
        if instancia is not None:
            return instancia
        # V2 eliminada pese a checksum estable: recrear desde el origen.
        return modelo.objects.create(**lookup, **expected)
    instancia, _ = modelo.objects.get_or_create(**lookup, defaults=expected)
    if _campos_diferentes(instancia, expected):
        for campo, valor in expected.items():
            setattr(instancia, campo, valor)
        instancia.save()
    return instancia


def _registrar_mapa(obj, destino, lote, accion):
    """Registra/sincroniza la entrada de LegacyMigrationMap para la corrida.

    ``saltar`` no escribe (no-op). En la creación la entrada queda ``migrado``;
    en la re-sincronización (origen cambió) se actualiza el checksum y pasa a
    ``reconciliado``. Limitación: el modelo guarda un único checksum por
    registro, no el historial por corrida.
    """
    if accion == 'saltar':
        return
    checksum = checksum_registro(obj)
    entry = LegacyMigrationMap.objects.filter(
        app_legacy='articulacion',
        modelo_legacy=obj._meta.model_name,
        uuid_legacy=obj.pk,
    ).first()
    if entry is None:
        entry = LegacyMigrationMap(
            app_legacy='articulacion',
            modelo_legacy=obj._meta.model_name,
            uuid_legacy=obj.pk,
            checksum=checksum,
            lote=lote,
            estado=LegacyMigrationMap.Estados.MIGRADO,
        )
    elif entry.checksum != checksum:
        entry.checksum = checksum
        entry.estado = LegacyMigrationMap.Estados.RECONCILIADO
        entry.observaciones = ''
    entry.tipo_destino = destino.__class__.__name__
    entry.uuid_destino = destino.pk
    entry.lote = lote
    entry.save()


def _sincronizar_poa(g, dry_run):
    codigo = f'P-{g}'
    nombre = f'POA Institucional {g}'
    if dry_run:
        return PoAInstitucional.objects.filter(codigo=codigo).first() or PoAInstitucional(
            codigo=codigo, gestion=g, nombre=nombre,
        )
    poa, _ = PoAInstitucional.objects.get_or_create(
        codigo=codigo, defaults={'gestion': g, 'nombre': nombre},
    )
    if poa.nombre != nombre:
        poa.nombre = nombre
        poa.save()
    return poa


def _atributos_origen(obj):
    atributos = {}
    for campo in ('presupuesto_programado', 'meta_gestion', 'meta_anual',
                  'total_programado', 'responsable'):
        if hasattr(obj, campo):
            valor = getattr(obj, campo)
            if valor is not None and valor != '':
                atributos[campo] = str(valor)
    return atributos


def _nombre_origen(obj):
    return obj.denominacion if hasattr(obj, 'denominacion') else str(obj)


def _codigo_origen(nivel, obj):
    if nivel == 'accion':
        return obj.codigo_accion
    if nivel == 'operacion':
        return obj.codigo_operacion
    if nivel == 'actividad':
        return obj.codigo_actividad
    return obj.codigo_tarea


def _estado_v2(obj, mapa_estados, resumen=None):
    origen = getattr(obj, 'estado', None) or ''
    clave = str(origen).upper()
    if clave in mapa_estados:
        return mapa_estados[clave]
    if resumen is not None:
        resumen['estados_desconocidos'].append({
            'modelo_legacy': obj._meta.model_name,
            'uuid_legacy': str(obj.pk),
            'estado_origen': str(origen),
            'estado_asignado': ESTADO_DESCONOCIDO_V2,
        })
    return ESTADO_DESCONOCIDO_V2


def _campos_diferentes(instancia, expected):
    if instancia is None:
        return list(expected)
    return [c for c in expected if getattr(instancia, c) != expected[c]]


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