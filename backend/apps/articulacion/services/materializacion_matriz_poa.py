"""Materialización y armado de filas del Borrador de Matriz POA.

Espejo de ``materializacion_matriz_pei`` para el instrumento operativo anual:
convierte las secciones del asistente en la cadena AccionPOA → OperacionPOAU →
ActividadPOAU → TareaPOAU, y arma las filas de la matriz oficial de 15 columnas
(fusión de los Cuadros 1 y 2 del RE-SPO, Artículo 14).

Cada fila lleva además las claves de ``m2_pei_poa`` (views_matrices), de modo
que la misma respuesta sirve a las dos vistas del listado: la matriz POA
completa y la proyección "Articulación PEI → POA".
"""
from decimal import Decimal, InvalidOperation

from django.db import transaction

from ..models import (
    AccionPOA, ActividadPOAU, BorradorMatrizPOA, OperacionPOAU, TareaPOAU,
)

ANCHO_PROGRAMA = 3
ANCHO_PROYECTO = 1
ANCHO_ACTIVIDAD = 3


def _seccion(datos, clave):
    valor = (datos or {}).get(clave)
    return valor if isinstance(valor, dict) else {}


def _acciones(datos):
    valor = (datos or {}).get('acciones')
    return valor if isinstance(valor, list) else []


def _lista(origen, clave):
    valor = (origen or {}).get(clave)
    return valor if isinstance(valor, list) else []


def _texto(valor):
    return '' if valor is None else str(valor)


def _fecha(valor):
    """Las fechas viajan como 'YYYY-MM-DD'; vacío es NULL, no cadena vacía."""
    texto = _texto(valor).strip()
    return texto or None


def _decimal(valor):
    if valor in ('', None):
        return None
    try:
        return Decimal(str(valor))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _segmento(valor, ancho):
    """Normaliza un segmento de la categoría programática: '1' → '001'."""
    limpio = ''.join(c for c in _texto(valor) if c.isdigit())
    if not limpio:
        return ''
    return limpio[-ancho:].zfill(ancho)


def categoria_programatica(accion):
    """La categoría programática es una concatenación, nunca un dato suelto."""
    programa = _segmento(accion.get('programa'), ANCHO_PROGRAMA)
    proyecto = _segmento(accion.get('proyecto'), ANCHO_PROYECTO)
    actividad = _segmento(accion.get('actividad'), ANCHO_ACTIVIDAD)
    if not (programa and proyecto and actividad):
        return ''
    return f'{programa} {proyecto} {actividad}'


def _codigo_accion(cod_producto_pei, accion, indice):
    """El código de la acción cuelga del producto institucional del PEI."""
    guardado = _texto(accion.get('codigo')).strip()
    if guardado:
        return guardado
    if not cod_producto_pei:
        return ''
    return f'{cod_producto_pei}.{indice + 1}'


# ---------------------------------------------------------------------------
# Filas de la matriz (15 columnas, 5 bloques)
# ---------------------------------------------------------------------------

def _cabecera(datos):
    articulacion = _seccion(datos, 's1_articulacion')
    responsable = _seccion(datos, 's2_responsable')
    return {
        'cod_producto_pei': _texto(articulacion.get('cod_producto_pei')),
        'accion_institucional_especifica': _texto(
            articulacion.get('accion_institucional_especifica')
        ),
        'indicador_proceso': _texto(articulacion.get('indicador_proceso')),
        'area_responsable': _texto(responsable.get('area_responsable')),
        # Contexto PEI: solo lo consume la vista "Articulación PEI → POA".
        'cod_resultado_pei': _texto(articulacion.get('cod_resultado_pei')),
        'resultado_pei': _texto(articulacion.get('resultado_pei')),
    }


def construir_filas_poa(borrador):
    """Una fila por acción de corto plazo programada en el borrador."""
    datos = borrador.datos or {}
    cabecera = _cabecera(datos)
    filas = []

    for indice, accion in enumerate(_acciones(datos)):
        codigo = _codigo_accion(cabecera['cod_producto_pei'], accion, indice)
        presupuesto = _decimal(accion.get('presupuesto_programado'))
        operaciones = _lista(accion, 'operaciones')
        actividades = sum(len(_lista(o, 'actividades')) for o in operaciones)
        tareas = sum(
            len(_lista(a, 'tareas'))
            for o in operaciones for a in _lista(o, 'actividades')
        )

        filas.append({
            'nivel': 'accion_poa',
            'tipo_fila': 'accion',
            'gestion': borrador.gestion,
            **cabecera,
            # Alias de m2_pei_poa: el nombre de la AIE es el producto PEI.
            'producto_pei': cabecera['accion_institucional_especifica'],
            'indicador': cabecera['indicador_proceso'],
            'cod_accion_poa': codigo,
            'accion_corto_plazo': _texto(accion.get('denominacion')),
            'resultado_esperado': _texto(accion.get('resultado_esperado')),
            'programa': _segmento(accion.get('programa'), ANCHO_PROGRAMA),
            'proyecto': _segmento(accion.get('proyecto'), ANCHO_PROYECTO),
            'actividad': _segmento(accion.get('actividad'), ANCHO_ACTIVIDAD),
            'categoria_programatica': categoria_programatica(accion),
            'presupuesto_programado': presupuesto,
            'cargo_reacp': _texto(accion.get('cargo_reacp')),
            'fecha_inicio': _fecha(accion.get('fecha_inicio')) or '',
            'fecha_fin': _fecha(accion.get('fecha_fin')) or '',
            'total_operaciones': len(operaciones),
            'total_actividades': actividades,
            'total_tareas': tareas,
        })

    return filas


def total_operaciones(borrador):
    """Operaciones programadas en todo el borrador (columna del listado)."""
    return sum(
        len(_lista(accion, 'operaciones'))
        for accion in _acciones(borrador.datos or {})
    )


# ---------------------------------------------------------------------------
# Materialización
# ---------------------------------------------------------------------------

def siguiente_correlativo(producto_pei_id, cod_producto_pei):
    """Primer correlativo libre para las acciones de esta AIE.

    ``AccionPOA.codigo_accion`` es único en toda la tabla y la restricción
    ``(producto_pei, gestion, correlativo)`` también: reiniciar la numeración
    en 1 choca contra ambas. Se consulta lo ya registrado y se continúa.
    """
    registradas = AccionPOA.objects.filter(producto_pei_id=producto_pei_id)
    usados = [c for c in registradas.values_list('correlativo', flat=True) if c]

    prefijo = f'{cod_producto_pei}.' if cod_producto_pei else None
    if prefijo:
        for codigo in registradas.values_list('codigo_accion', flat=True):
            if not codigo or not codigo.startswith(prefijo):
                continue
            cola = codigo[len(prefijo):].split('.')[0]
            if cola.isdigit() and int(cola) > 0:
                usados.append(int(cola))

    return max(usados) + 1 if usados else 1


def _codigo_libre(modelo, campo, base):
    """Evita el choque contra el unique cuando la rama ya fue codificada."""
    candidato = base
    sufijo = 1
    while modelo.objects.filter(**{campo: candidato}).exists():
        sufijo += 1
        candidato = f'{base}-{sufijo}'
    return candidato


@transaction.atomic
def materializar_borrador_poa(borrador, usuario=None):
    """Crea AccionPOA → OperacionPOAU → ActividadPOAU → TareaPOAU.

    Devuelve los registros creados y reescribe en el borrador el código
    realmente asignado a cada acción, para que la matriz y la base coincidan.
    """
    if (borrador.estado == BorradorMatrizPOA.ESTADO_COMPLETO
            and borrador.id_accion_poa_id):
        raise ValueError('El borrador ya fue materializado.')

    datos = borrador.datos or {}
    articulacion = _seccion(datos, 's1_articulacion')
    responsable = _seccion(datos, 's2_responsable')

    producto_pei_id = articulacion.get('producto_pei')
    if not producto_pei_id:
        raise ValueError(
            'El borrador no está articulado con el PEI: falta la acción '
            'institucional específica de origen.'
        )

    acciones = _acciones(datos)
    if not acciones:
        raise ValueError('El borrador no tiene acciones de corto plazo.')

    cod_producto_pei = _texto(articulacion.get('cod_producto_pei'))
    correlativo = siguiente_correlativo(producto_pei_id, cod_producto_pei)

    creados = {
        'acciones': [], 'operaciones': [], 'actividades': [], 'tareas': [],
    }
    codigos_asignados = []

    for accion in acciones:
        base = (
            f'{cod_producto_pei}.{correlativo}' if cod_producto_pei
            else f'ACP.{borrador.gestion}.{correlativo}'
        )
        codigo_accion = _codigo_libre(AccionPOA, 'codigo_accion', base)

        registro = AccionPOA.objects.create(
            codigo_accion=codigo_accion,
            correlativo=correlativo,
            segmento=AccionPOA.generar_segmento(correlativo),
            denominacion=_texto(accion.get('denominacion')),
            resultado_esperado=_texto(accion.get('resultado_esperado')),
            producto_pei_id=producto_pei_id,
            gestion=borrador.gestion,
            indicador=_texto(articulacion.get('indicador_proceso')),
            cargo_responsable=_texto(accion.get('cargo_reacp')),
            fecha_inicio=_fecha(accion.get('fecha_inicio')),
            fecha_fin=_fecha(accion.get('fecha_fin')),
            programa=_segmento(accion.get('programa'), ANCHO_PROGRAMA),
            proyecto_sisin=_segmento(accion.get('proyecto'), ANCHO_PROYECTO),
            actividad_presupuestaria=_segmento(
                accion.get('actividad'), ANCHO_ACTIVIDAD
            ),
            categoria_programatica=categoria_programatica(accion),
            presupuesto_programado=_decimal(accion.get('presupuesto_programado')),
            unidad_responsable_id=responsable.get('unidad_responsable') or None,
            created_by=usuario, updated_by=usuario,
        )
        creados['acciones'].append(registro)
        codigos_asignados.append(codigo_accion)

        for j, operacion in enumerate(_lista(accion, 'operaciones'), start=1):
            registro_operacion = OperacionPOAU.objects.create(
                codigo_operacion=_codigo_libre(
                    OperacionPOAU, 'codigo_operacion', f'{codigo_accion}.{j}',
                ),
                correlativo=j,
                segmento=OperacionPOAU.generar_segmento(j),
                denominacion=_texto(operacion.get('denominacion')),
                tipo_operacion=_texto(operacion.get('tipo_operacion')),
                producto_entregable=_texto(operacion.get('producto_entregable')),
                accion_poa=registro,
                unidad_ejecutora=_texto(operacion.get('unidad_ejecutora')),
                responsable=_texto(operacion.get('responsable')),
                meta_anual=_decimal(operacion.get('meta_anual')),
                fecha_inicio=_fecha(operacion.get('fecha_inicio')),
                fecha_fin=_fecha(operacion.get('fecha_fin')),
                created_by=usuario, updated_by=usuario,
            )
            creados['operaciones'].append(registro_operacion)

            for k, actividad in enumerate(_lista(operacion, 'actividades'), start=1):
                registro_actividad = ActividadPOAU.objects.create(
                    codigo_actividad=_codigo_libre(
                        ActividadPOAU, 'codigo_actividad',
                        f'{registro_operacion.codigo_operacion}.{k}',
                    ),
                    correlativo=k,
                    segmento=ActividadPOAU.generar_segmento(k),
                    denominacion=_texto(actividad.get('denominacion')),
                    operacion=registro_operacion,
                    producto_entregable=_texto(actividad.get('producto_entregable')),
                    meta_anual=_decimal(actividad.get('meta_anual')),
                    fecha_inicio=_fecha(actividad.get('fecha_inicio')),
                    fecha_fin=_fecha(actividad.get('fecha_fin')),
                    created_by=usuario, updated_by=usuario,
                )
                creados['actividades'].append(registro_actividad)

                for m, tarea in enumerate(_lista(actividad, 'tareas'), start=1):
                    creados['tareas'].append(TareaPOAU.objects.create(
                        codigo_tarea=_codigo_libre(
                            TareaPOAU, 'codigo_tarea',
                            f'{registro_actividad.codigo_actividad}.{m}',
                        ),
                        correlativo=m,
                        segmento=TareaPOAU.generar_segmento(m),
                        denominacion=_texto(tarea.get('denominacion')),
                        actividad=registro_actividad,
                        responsable=_texto(tarea.get('responsable')),
                        metas=_decimal(tarea.get('metas')),
                        fecha_inicio=_fecha(tarea.get('fecha_inicio')),
                        fecha_fin=_fecha(tarea.get('fecha_fin')),
                        created_by=usuario, updated_by=usuario,
                    ))

        correlativo += 1

    # El borrador guarda el código real: si no, la matriz mostraría uno y la
    # base tendría otro en cuanto la numeración continúe desde lo registrado.
    persistidas = list(acciones)
    for indice, codigo in enumerate(codigos_asignados):
        persistidas[indice] = {**persistidas[indice], 'codigo': codigo}
    borrador.datos = {**datos, 'acciones': persistidas}

    return creados
