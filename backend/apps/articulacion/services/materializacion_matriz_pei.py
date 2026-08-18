"""Materialización y armado de filas del Borrador de Matriz PEI.

Espejo de ``materializacion_matriz`` (PAD) para el instrumento institucional:
convierte las secciones del asistente en ResultadoPEI → ProductoPEI →
IndicadorCadena, y arma las filas de la matriz oficial de 46 columnas.
"""
from django.db import transaction

from ..models import (
    BorradorMatrizPEI, IndicadorCadena, ProductoPEI, ResultadoPEI,
)

GESTIONES = ('2026', '2027', '2028', '2029', '2030')

NO_APLICA = 'NO APLICA'


def _seccion(datos, clave):
    valor = (datos or {}).get(clave)
    return valor if isinstance(valor, dict) else {}


def _resultados(datos):
    valor = (datos or {}).get('resultados')
    return valor if isinstance(valor, list) else []


def _dec(valor):
    return valor if valor not in ('', None) else None


def _texto(valor):
    return '' if valor is None else str(valor)


def _programacion(origen):
    origen = origen or {}
    return {anio: _dec(origen.get(anio)) for anio in GESTIONES}


def _suma(origen):
    total = 0
    for anio in GESTIONES:
        try:
            total += float((origen or {}).get(anio) or 0)
        except (TypeError, ValueError):
            continue
    return total


def _codigo_resultado(institucional, resultado, indice):
    cod_entidad = _texto(institucional.get('cod_entidad'))
    correlativo = resultado.get('correlativo') or (indice + 1)
    return f'{cod_entidad}.{correlativo}' if cod_entidad else ''


# ---------------------------------------------------------------------------
# Filas de la matriz (46 columnas, 8 secciones)
# ---------------------------------------------------------------------------

def _cabecera(datos):
    nacional = _seccion(datos, 's1_nacional')
    acuerdos = _seccion(datos, 's2_acuerdos')
    sector = _seccion(datos, 's3_sector')
    territorial = _seccion(datos, 's4_territorial')
    institucional = _seccion(datos, 's5_institucional')

    return {
        'cod_eje_pgdesa': _texto((nacional.get('eje') or {}).get('codigo')),
        'objetivo_impacto': _texto(nacional.get('objetivo_impacto')),
        'cod_componente_pdesa': _texto((nacional.get('componente') or {}).get('codigo')),
        'objetivo_efecto': _texto(nacional.get('objetivo_efecto')),
        'cod_ods': _texto(acuerdos.get('ods')),
        'cod_ndc': _texto(acuerdos.get('ndc')),
        'cod_ndt': _texto(acuerdos.get('ndt')),
        'cod_meta_3030': _texto(acuerdos.get('kmgbf')),
        'cod_sector': _texto((sector.get('sector') or {}).get('codigo')),
        'sector': _texto((sector.get('sector') or {}).get('denominacion')),
        'cod_resultado_sectorial': _texto(
            (sector.get('resultado_sectorial') or {}).get('codigo')
        ),
        'resultado_sectorial': _texto(
            (sector.get('resultado_sectorial') or {}).get('denominacion')
        ),
        'cod_resultado_territorial': _texto(territorial.get('cod_resultado_territorial')),
        'cod_entidad': _texto(institucional.get('cod_entidad')),
        'entidad': _texto(institucional.get('entidad')),
        'cod_oei': _texto(institucional.get('cod_oei')),
    }


def _bloque_indicador(indicador, fisica, inversion, corriente):
    indicador = indicador or {}
    inversion_total = _suma(inversion)
    corriente_total = _suma(corriente)
    return {
        'indicador': _texto(indicador.get('indicador')),
        'tipo_indicador': _texto(indicador.get('tipo_indicador')),
        'unidad_medida': _texto(indicador.get('unidad_medida')),
        'formula': _texto(indicador.get('formula')),
        'linea_base': _dec(indicador.get('linea_base')),
        'meta_2030': _dec(indicador.get('meta_2030')),
        **{f'fisica_{a}': _dec((fisica or {}).get(a)) for a in GESTIONES},
        'presupuesto_total': inversion_total + corriente_total,
        'inversion_total': inversion_total,
        **{f'inversion_{a}': _dec((inversion or {}).get(a)) for a in GESTIONES},
        'corriente_total': corriente_total,
        **{f'corriente_{a}': _dec((corriente or {}).get(a)) for a in GESTIONES},
    }


def construir_filas_pei(borrador):
    """Filas de la matriz: una por resultado y una por cada producto."""
    datos = borrador.datos or {}
    institucional = _seccion(datos, 's5_institucional')
    cabecera = _cabecera(datos)
    filas = []

    for indice, resultado in enumerate(_resultados(datos)):
        cod_resultado = _codigo_resultado(institucional, resultado, indice)
        productos = resultado.get('productos') or []

        # El presupuesto del resultado consolida el de sus productos.
        inversion = {a: sum(
            float((p.get('inversion') or {}).get(a) or 0) for p in productos
        ) for a in GESTIONES}
        corriente = {a: sum(
            float((p.get('corriente') or {}).get(a) or 0) for p in productos
        ) for a in GESTIONES}

        filas.append({
            'nivel': 'resultado',
            'tipo_fila': 'resultado',
            **cabecera,
            'cod_resultado_pei': cod_resultado,
            'resultado_institucional': _texto(resultado.get('denominacion')),
            'cod_programa_presup': NO_APLICA,
            'programa_presup': NO_APLICA,
            'cod_producto': NO_APLICA,
            'nombre_producto': NO_APLICA,
            **_bloque_indicador(
                resultado.get('indicador'),
                resultado.get('programacion_fisica'),
                inversion, corriente,
            ),
        })

        for j, producto in enumerate(productos, start=1):
            filas.append({
                'nivel': 'producto',
                'tipo_fila': 'producto',
                **cabecera,
                'cod_resultado_pei': cod_resultado,
                'resultado_institucional': _texto(resultado.get('denominacion')),
                'cod_programa_presup': _texto(producto.get('cod_programa_presup')),
                'programa_presup': _texto(producto.get('programa_presup')),
                'cod_producto': f'{cod_resultado}.{j}' if cod_resultado else '',
                'nombre_producto': _texto(producto.get('denominacion')),
                **_bloque_indicador(
                    producto.get('indicador'),
                    producto.get('programacion_fisica'),
                    producto.get('inversion'),
                    producto.get('corriente'),
                ),
            })

    return filas


# ---------------------------------------------------------------------------
# Materialización
# ---------------------------------------------------------------------------

@transaction.atomic
def materializar_borrador_pei(borrador, usuario=None):
    """Crea ResultadoPEI → ProductoPEI → IndicadorCadena desde el borrador."""
    if (borrador.estado == BorradorMatrizPEI.ESTADO_COMPLETO
            and borrador.id_resultado_pei_id):
        raise ValueError('El borrador ya fue materializado.')

    datos = borrador.datos or {}
    institucional = _seccion(datos, 's5_institucional')
    nacional = _seccion(datos, 's1_nacional')
    acuerdos = _seccion(datos, 's2_acuerdos')
    sector = _seccion(datos, 's3_sector')
    territorial = _seccion(datos, 's4_territorial')

    lista = _resultados(datos)
    if not lista:
        raise ValueError('El borrador no tiene resultados institucionales.')

    creados = {'resultados': [], 'productos': [], 'indicadores': []}

    for indice, resultado in enumerate(lista):
        cod_resultado = _codigo_resultado(institucional, resultado, indice)
        if not cod_resultado:
            raise ValueError('Falta el código de entidad para codificar el resultado.')

        registro = ResultadoPEI.objects.create(
            codigo_resultado=cod_resultado,
            denominacion=_texto(resultado.get('denominacion')),
            cod_entidad=_texto(institucional.get('cod_entidad')),
            entidad=_texto(institucional.get('entidad')),
            cod_oei=_texto(institucional.get('cod_oei')),
            objetivo_estrategico=_texto(institucional.get('objetivo_estrategico')),
            vigencia_desde=int(institucional.get('vigencia_desde') or borrador.gestion),
            vigencia_hasta=int(institucional.get('vigencia_hasta') or 2030),
            cod_eje_pgdesa=_texto((nacional.get('eje') or {}).get('codigo')),
            objetivo_impacto=_texto(nacional.get('objetivo_impacto')),
            cod_componente_pdesa=_texto((nacional.get('componente') or {}).get('codigo')),
            objetivo_efecto=_texto(nacional.get('objetivo_efecto')),
            cod_ods=_texto(acuerdos.get('ods')),
            cod_ndc=_texto(acuerdos.get('ndc')),
            cod_ndt=_texto(acuerdos.get('ndt')),
            cod_meta_3030=_texto(acuerdos.get('kmgbf')),
            cod_sector=_texto((sector.get('sector') or {}).get('codigo')),
            sector=_texto((sector.get('sector') or {}).get('denominacion')),
            cod_resultado_sectorial=_texto(
                (sector.get('resultado_sectorial') or {}).get('codigo')
            ),
            resultado_sectorial=_texto(
                (sector.get('resultado_sectorial') or {}).get('denominacion')
            ),
            cod_resultado_territorial=_texto(
                territorial.get('cod_resultado_territorial')
            ),
            created_by=usuario, updated_by=usuario,
        )
        creados['resultados'].append(registro)

        productos = resultado.get('productos') or []
        indicador_res = resultado.get('indicador') or {}
        inversion = {a: sum(
            float((p.get('inversion') or {}).get(a) or 0) for p in productos
        ) for a in GESTIONES}
        corriente = {a: sum(
            float((p.get('corriente') or {}).get(a) or 0) for p in productos
        ) for a in GESTIONES}

        creados['indicadores'].append(IndicadorCadena.objects.create(
            nivel_indicador='resultado_pei',
            resultado_pei=registro,
            indicador=_texto(indicador_res.get('indicador')),
            tipo_indicador='Resultado',
            unidad_medida=_texto(indicador_res.get('unidad_medida')),
            formula=_texto(indicador_res.get('formula')),
            linea_base=_dec(indicador_res.get('linea_base')),
            meta_2030=_dec(indicador_res.get('meta_2030')),
            programacion_fisica=_programacion(resultado.get('programacion_fisica')),
            presupuesto_inversion_total=_suma(inversion),
            presupuesto_corriente_total=_suma(corriente),
            **{f'inversion_{a}': inversion.get(a) or 0 for a in GESTIONES},
            **{f'corriente_{a}': corriente.get(a) or 0 for a in GESTIONES},
            created_by=usuario, updated_by=usuario,
        ))

        for j, producto in enumerate(productos, start=1):
            registro_producto = ProductoPEI.objects.create(
                codigo_producto=f'{cod_resultado}.{j}',
                denominacion=_texto(producto.get('denominacion')),
                resultado_pei=registro,
                tipo_producto=_texto(producto.get('tipo_producto')),
                cod_programa_presup=_texto(producto.get('cod_programa_presup')),
                programa_presup=_texto(producto.get('programa_presup')),
                created_by=usuario, updated_by=usuario,
            )
            creados['productos'].append(registro_producto)

            indicador_prod = producto.get('indicador') or {}
            creados['indicadores'].append(IndicadorCadena.objects.create(
                nivel_indicador='producto_pei',
                producto_pei=registro_producto,
                indicador=_texto(indicador_prod.get('indicador')),
                tipo_indicador='Producto',
                unidad_medida=_texto(indicador_prod.get('unidad_medida')),
                formula=_texto(indicador_prod.get('formula')),
                linea_base=_dec(indicador_prod.get('linea_base')),
                meta_2030=_dec(indicador_prod.get('meta_2030')),
                programacion_fisica=_programacion(producto.get('programacion_fisica')),
                presupuesto_inversion_total=_suma(producto.get('inversion')),
                presupuesto_corriente_total=_suma(producto.get('corriente')),
                **{f'inversion_{a}': (producto.get('inversion') or {}).get(a) or 0
                   for a in GESTIONES},
                **{f'corriente_{a}': (producto.get('corriente') or {}).get(a) or 0
                   for a in GESTIONES},
                created_by=usuario, updated_by=usuario,
            ))

    return creados
