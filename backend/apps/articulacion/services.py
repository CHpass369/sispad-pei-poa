from django.db import transaction
from decimal import Decimal
from django.core.exceptions import ValidationError
from apps.auditoria.models import EventoAuditoria
from apps.codificacion.models import (
    EntidadTerritorialCGEO as EntidadTerritorialCGEOCatalogo,
    LineamientoPAD as LineamientoPADCatalogo,
    ResultadoSectorial as ResultadoSectorialCatalogo,
)
from .models import (
    BorradorMatrizPAD, ResultadoPAD, ProductoPAD, IndicadorCadena,
    AcuerdoInternacional, MetaAcuerdoInternacional,
)


def registrar_auditoria(usuario, accion, entidad, entidad_id, detalle=None):
    """Registra evento en EventoAuditoria (apps.auditoria)."""
    EventoAuditoria.objects.create(
        usuario=usuario,
        accion=accion,
        entidad=entidad,
        entidad_id=str(entidad_id),
        resumen=detalle or '',
    )


# =============================================================================
# Borrador de Matriz PAD — materialización y matrices A/B
#
# Estructura REAL de las matrices (Excel "MATRICES A Y B"):
#   Un borrador contiene VARIOS resultados territoriales PAD, cada uno con
#   VARIOS productos. Todas las filas conviven en la misma Matriz A y en la
#   misma Matriz B: por cada resultado se emite 1 fila de resultado + 1 fila
#   por cada producto.
#
# La sección ``resultados`` del borrador es una colección (formato nuevo)::
#
#   resultados: [
#     {
#       denominacion, territorializacion, responsable,
#       cuenta_con_financiamiento,
#       indicador: {indicador, formula, unidad_medida, linea_base, meta_2030},
#       programacion_fisica: {'2026': ...},
#       presupuesto_total, presupuesto_anual: {'2026': ...},
#       productos: [ {mismos campos que el resultado}, ... ],
#     },
#     ...
#   ]
#
# Las secciones p6..p10 del formato anterior (cadena única) se aceptan como
# retrocompatibilidad: ``_obtener_resultados`` las transforma a la colección
# en lectura. Los borradores nuevos solo escriben p1..p5 + resultados[].
# =============================================================================

def _seccion(datos, nombre, por_defecto=''):
    """Lee el valor de un campo de una sección del borrador.

    Preserva valores falsy (0, '', False): usa ``None`` como único
    marcador de ausencia.
    """
    datos = datos or {}
    valor = datos.get(nombre)
    return por_defecto if valor is None else valor


def _subseccion(datos, nombre):
    """Lee una sección completa del borrador; {} si no existe o no es dict."""
    seccion = _seccion(datos, nombre, {})
    return seccion if isinstance(seccion, dict) else {}


def _acuerdo_o_nada(valor):
    """Normaliza un acuerdo del wizard: 'N/A' o sin id -> {} (no aplica).

    El frontend usa el string 'N/A' para indicar que el acuerdo no aplica
    (Matriz B usa N/A en el Excel); un dict con id es el acuerdo real.
    """
    if isinstance(valor, dict) and valor.get('id'):
        return valor
    return {}


def _correlativo_resultado(lineamiento_catalogo_id, gestion):
    """Correlativo del resultado dentro del lineamiento (guía: CGEO.lineamiento.correlativo)."""
    try:
        return ResultadoPAD.objects.filter(
            lineamiento_pad_catalogo_id=lineamiento_catalogo_id,
            vigencia_desde=gestion,
        ).count() + 1
    except Exception:
        # id de catálogo inválido o ausente en el borrador: reinicia correlativo
        return 1


def _fk_id_o_none(modelo, raw_id):
    """Valida un id de FK de catálogo; None si es inválido o no existe."""
    if not raw_id:
        return None
    try:
        if modelo.objects.filter(pk=raw_id).exists():
            return raw_id
    except (ValueError, TypeError, ValidationError):
        pass
    return None


def _m2m_id_o_none(modelo, raw_id):
    """Id de M2M de catálogo si existe el registro; None en caso contrario."""
    return _fk_id_o_none(modelo, raw_id)


def _correlativo_producto(resultado_pad):
    """Correlativo del producto dentro del resultado (guía: CGEO.lineamiento.resultado.correlativo)."""
    return ProductoPAD.objects.filter(resultado_pad=resultado_pad).count() + 1


# ---------------------------------------------------------------------------
# Colección de resultados (formato nuevo) con transformación legacy p6..p10
# ---------------------------------------------------------------------------

def _indicador_normalizado(raw):
    """Diccionario de indicador normalizado; tolera el formato legacy plano."""
    raw = raw if isinstance(raw, dict) else {}
    if 'indicador' in raw or 'formula' in raw:
        # Formato legacy: campos planos en la sección p8/p9
        return {
            'indicador': raw.get('indicador', ''),
            'formula': raw.get('formula', ''),
            'unidad_medida': raw.get('unidad_medida', ''),
            'linea_base': raw.get('linea_base'),
            'meta_2030': raw.get('meta_2030'),
        }
    # Formato nuevo: dict anidado
    return {
        'indicador': raw.get('indicador', ''),
        'formula': raw.get('formula', ''),
        'unidad_medida': raw.get('unidad_medida', ''),
        'linea_base': raw.get('linea_base'),
        'meta_2030': raw.get('meta_2030'),
    }


def _producto_normalizado(raw):
    """Producto normalizado (dict con claves canónicas)."""
    raw = raw if isinstance(raw, dict) else {}
    indicador = _indicador_normalizado(raw.get('indicador') or {})
    return {
        'denominacion': raw.get('denominacion', ''),
        'territorializacion': raw.get('territorializacion', ''),
        'responsable': raw.get('responsable', ''),
        'cuenta_con_financiamiento': bool(raw.get('cuenta_con_financiamiento', False)),
        'indicador': indicador,
        'programacion_fisica': raw.get('programacion_fisica') or {},
        'presupuesto_total': raw.get('presupuesto_total'),
        'presupuesto_anual': raw.get('presupuesto_anual') or {},
    }


def _resultado_normalizado(raw):
    """Resultado normalizado (claves canónicas + productos[] normalizados)."""
    raw = raw if isinstance(raw, dict) else {}
    productos = raw.get('productos')
    if not isinstance(productos, list):
        productos = []
    return {
        'denominacion': raw.get('denominacion', ''),
        'territorializacion': raw.get('territorializacion', ''),
        'responsable': raw.get('responsable', ''),
        'cuenta_con_financiamiento': bool(raw.get('cuenta_con_financiamiento', False)),
        'indicador': _indicador_normalizado(raw.get('indicador') or {}),
        'programacion_fisica': raw.get('programacion_fisica') or {},
        'presupuesto_total': raw.get('presupuesto_total'),
        'presupuesto_anual': raw.get('presupuesto_anual') or {},
        'productos': [_producto_normalizado(p) for p in productos],
    }


def _obtener_resultados(datos):
    """Colección de resultados del borrador.

    Formato nuevo: ``datos['resultados']`` (lista). Si el borrador fue
    creado antes de la colección (p6..p10, cadena única), la transforma a
    una colección de un resultado con un producto (retrocompatibilidad).
    """
    resultados = (datos or {}).get('resultados')
    if isinstance(resultados, list):
        return [_resultado_normalizado(r) for r in resultados]

    # Legacy: cadena única en p6_resultado/p7_producto/p8..p10
    resultado_sec = _subseccion(datos, 'p6_resultado')
    producto_sec = _subseccion(datos, 'p7_producto')
    ind_resultado = _subseccion(datos, 'p8_indicador_resultado')
    ind_producto = _subseccion(datos, 'p9_indicador_producto')
    financiera = _subseccion(datos, 'p10_financiera')
    if not resultado_sec and not producto_sec:
        return []

    ind_planos_resultado = {
        'indicador': ind_resultado.get('indicador', ''),
        'formula': ind_resultado.get('formula', ''),
        'unidad_medida': ind_resultado.get('unidad_medida', ''),
        'linea_base': ind_resultado.get('linea_base'),
        'meta_2030': ind_resultado.get('meta_2030'),
    }
    ind_planos_producto = {
        'indicador': ind_producto.get('indicador', ''),
        'formula': ind_producto.get('formula', ''),
        'unidad_medida': ind_producto.get('unidad_medida', ''),
        'linea_base': ind_producto.get('linea_base'),
        'meta_2030': ind_producto.get('meta_2030'),
    }
    return [{
        'denominacion': _seccion(resultado_sec, 'denominacion'),
        'territorializacion': _seccion(resultado_sec, 'territorializacion'),
        'responsable': _seccion(resultado_sec, 'responsable'),
        'cuenta_con_financiamiento': bool(
            _seccion(resultado_sec, 'cuenta_con_financiamiento', por_defecto=False),
        ),
        'indicador': ind_planos_resultado,
        'programacion_fisica': ind_resultado.get('programacion_fisica') or {},
        'presupuesto_total': _seccion(financiera, 'presupuesto_total', None),
        'presupuesto_anual': financiera.get('presupuesto_anual') or {},
        'productos': [{
            'denominacion': _seccion(producto_sec, 'denominacion'),
            'territorializacion': _seccion(producto_sec, 'territorializacion'),
            'responsable': _seccion(producto_sec, 'responsable'),
            'cuenta_con_financiamiento': bool(
                _seccion(producto_sec, 'cuenta_con_financiamiento', por_defecto=False),
            ),
            'indicador': ind_planos_producto,
            'programacion_fisica': ind_producto.get('programacion_fisica') or {},
            'presupuesto_total': _seccion(financiera, 'presupuesto_total', None),
            'presupuesto_anual': financiera.get('presupuesto_anual') or {},
        }],
    }]


def _resultados_del_borrador(borrador):
    """Resultados operativos materializados del borrador (0..N).

    La materialización crea N ResultadoPAD con ``id_cadena`` de prefijo
    ``M1{hex10}`` (el primero conserva el formato histórico); la consulta
    por prefijo recupera TODOS los resultados del borrador.
    """
    prefijo = f'M1{borrador.id.hex[:10]}'
    return ResultadoPAD.objects.filter(
        id_cadena__startswith=prefijo,
    ).order_by('codigo_resultado')


# ---------------------------------------------------------------------------
# Materialización (transacción atómica)
# ---------------------------------------------------------------------------

@transaction.atomic
def materializar_borrador_matriz(borrador, usuario=None):
    """Materializa el borrador en ResultadoPAD → ProductoPAD → IndicadorCadena.

    Crea UN ResultadoPAD por cada elemento de la colección ``resultados``
    (código compuesto ``CGEO.lineamiento.correlativo`` con correlativo
    incremental por resultado) y, por cada resultado, UN ProductoPAD por
    producto (código ``CGEO.lineamiento.resultado.correlativo`` con
    correlativo incremental por producto). Cada resultado y cada producto
    genera su IndicadorCadena (nivel RESULTADO_PAD / PRODUCTO_PAD) con
    programacion_fisica, presupuesto_total y presupuesto_anual.

    Transacción atómica: si falla cualquier paso no queda ningún registro
    operativo a medias. Devuelve un resumen con los registros creados.
    """
    if borrador.estado == BorradorMatrizPAD.ESTADO_COMPLETO and borrador.id_resultado_pad_id:
        raise ValueError('El borrador ya fue materializado.')

    datos = borrador.datos or {}
    gestion = borrador.gestion
    resultados_data = _obtener_resultados(datos)
    if not resultados_data:
        raise ValueError(
            'El borrador no tiene resultados para materializar. '
            'Complete la sección "resultados" (resultado + productos).'
        )

    nacional = _subseccion(datos, 'p1_nacional')
    acuerdos = _subseccion(datos, 'p2_acuerdos')
    sectorial = _subseccion(datos, 'p3_sectorial')
    territorial = _subseccion(datos, 'p4_territorial')
    lineamiento_sec = _subseccion(datos, 'p5_lineamiento')

    eje = nacional.get('eje') or {}
    componente = nacional.get('componente') or {}
    ods = _acuerdo_o_nada(acuerdos.get('ods'))
    ndc = _acuerdo_o_nada(acuerdos.get('ndc'))
    ndt = _acuerdo_o_nada(acuerdos.get('ndt'))
    kmgbf = _acuerdo_o_nada(acuerdos.get('kmgbf'))
    sector = sectorial.get('sector') or {}
    resultado_sectorial = sectorial.get('resultado_sectorial') or {}
    cgeo = territorial.get('cgeo') or {}
    lineamiento = lineamiento_sec.get('lineamiento') or {}

    lineamiento_id = _fk_id_o_none(LineamientoPADCatalogo, lineamiento.get('id'))
    correlativo_base = _correlativo_resultado(lineamiento_id, gestion)

    creados = {'resultados': [], 'productos': [], 'indicadores': []}

    for i, res_data in enumerate(resultados_data):
        codigo_resultado = (
            f"{cgeo.get('codigo', '')}.{lineamiento.get('codigo', '')}."
            f"{correlativo_base + i}"
        )
        id_cadena = f'M1{borrador.id.hex[:10]}'
        if i > 0:
            id_cadena = f'{id_cadena}-{i + 1}'
        resultado = ResultadoPAD.objects.create(
            id_cadena=id_cadena,
            codigo_resultado=codigo_resultado,
            denominacion=_seccion(res_data, 'denominacion'),
            lineamiento_pad=lineamiento.get('codigo', ''),
            politica=_seccion(territorial, 'politica'),
            territorializacion=_seccion(res_data, 'territorializacion'),
            responsable_pad=_seccion(res_data, 'responsable'),
            cuenta_con_financiamiento=_seccion(
                res_data, 'cuenta_con_financiamiento', por_defecto=False,
            ),
            vigencia_desde=gestion,
            vigencia_hasta=2030,
            cod_geografico=cgeo.get('codigo', ''),
            eta=_seccion(territorial, 'eta'),
            resultado_sectorial_catalogo_id=_fk_id_o_none(
                ResultadoSectorialCatalogo, resultado_sectorial.get('id'),
            ),
            entidad_territorial_cgeo_id=_fk_id_o_none(
                EntidadTerritorialCGEOCatalogo, cgeo.get('id'),
            ),
            lineamiento_pad_catalogo_id=lineamiento_id,
            cod_eje_pgdesa=eje.get('codigo', ''),
            objetivo_impacto=_seccion(nacional, 'objetivo_impacto'),
            cod_componente_pdesa=componente.get('codigo', ''),
            objetivo_efecto=_seccion(nacional, 'objetivo_efecto'),
            cod_sector=sector.get('codigo', ''),
            sector=sector.get('denominacion', ''),
            cod_resultado_pds=resultado_sectorial.get('codigo', ''),
            resultado_pds=resultado_sectorial.get('denominacion', ''),
            estado='REFERENCIAL',
        )
        id_ods = _m2m_id_o_none(AcuerdoInternacional, ods.get('id'))
        if id_ods:
            resultado.acuerdo_ods.add(id_ods)
        id_ndc = _m2m_id_o_none(MetaAcuerdoInternacional, ndc.get('id'))
        if id_ndc:
            resultado.acuerdo_ndc.add(id_ndc)
        id_ndt = _m2m_id_o_none(MetaAcuerdoInternacional, ndt.get('id'))
        if id_ndt:
            resultado.acuerdo_ndt.add(id_ndt)
        id_kmgbf = _m2m_id_o_none(MetaAcuerdoInternacional, kmgbf.get('id'))
        if id_kmgbf:
            resultado.acuerdo_kmgbf.add(id_kmgbf)

        creados['resultados'].append(resultado)

        ind_res = res_data.get('indicador') or {}
        indicador_resultado = IndicadorCadena.objects.create(
            nivel_indicador='RESULTADO_PAD',
            resultado_pad=resultado,
            indicador=_seccion(ind_res, 'indicador'),
            formula=_seccion(ind_res, 'formula'),
            unidad_medida=_seccion(ind_res, 'unidad_medida'),
            linea_base=_seccion(ind_res, 'linea_base', None),
            meta_2030=_seccion(ind_res, 'meta_2030', None),
            programacion_fisica=res_data.get('programacion_fisica') or None,
            presupuesto_total=_seccion(res_data, 'presupuesto_total', None),
            presupuesto_anual=res_data.get('presupuesto_anual') or None,
        )
        creados['indicadores'].append(indicador_resultado)

        for producto_data in res_data.get('productos') or []:
            correlativo_producto = _correlativo_producto(resultado)
            producto = ProductoPAD.objects.create(
                codigo_producto=f'{codigo_resultado}.{correlativo_producto}',
                denominacion=_seccion(producto_data, 'denominacion'),
                resultado_pad=resultado,
                territorializacion=_seccion(producto_data, 'territorializacion'),
                responsable=_seccion(producto_data, 'responsable'),
                cuenta_con_financiamiento=_seccion(
                    producto_data, 'cuenta_con_financiamiento', por_defecto=False,
                ),
            )
            creados['productos'].append(producto)

            ind_prod = producto_data.get('indicador') or {}
            indicador_producto = IndicadorCadena.objects.create(
                nivel_indicador='PRODUCTO_PAD',
                producto_pad=producto,
                indicador=_seccion(ind_prod, 'indicador'),
                formula=_seccion(ind_prod, 'formula'),
                unidad_medida=_seccion(ind_prod, 'unidad_medida'),
                linea_base=_seccion(ind_prod, 'linea_base', None),
                meta_2030=_seccion(ind_prod, 'meta_2030', None),
                programacion_fisica=producto_data.get('programacion_fisica') or None,
                presupuesto_total=_seccion(producto_data, 'presupuesto_total', None),
                presupuesto_anual=producto_data.get('presupuesto_anual') or None,
            )
            creados['indicadores'].append(indicador_producto)

    if usuario is not None:
        registrar_auditoria(
            usuario=usuario, accion='crear', entidad='ResultadoPAD',
            entidad_id=str(creados['resultados'][0].id),
            detalle=(
                f'Materializado desde borrador {borrador.id}: '
                f'{len(creados["resultados"])} resultado(s), '
                f'{len(creados["productos"])} producto(s)'
            ),
        )

    return creados


# ---------------------------------------------------------------------------
# Filas de Matriz A (27 columnas)
# ---------------------------------------------------------------------------

def _fila_matriz_a_resultado(resultado, indicador, es_borrador=False):
    """Fila de resultado de la Matriz A (columnas según guía)."""
    prog = indicador.programacion_fisica if indicador else {}
    presupuesto_anual = indicador.presupuesto_anual if indicador else {}
    return {
        'nivel': 'RESULTADO_PAD' if not es_borrador else 'RESULTADO',
        'tipo_fila': 'resultado',
        'sector': resultado.sector or resultado.cod_sector or '',
        'cod_sector': resultado.cod_sector or '',
        'cod_geografico': resultado.cod_geografico or '',
        'politica': resultado.politica or '',
        'cod_lineamiento_pad': resultado.lineamiento_pad or '',
        'codigo_resultado_pad': resultado.codigo_resultado or '',
        'resultado_pad': resultado.denominacion or '',
        'codigo_producto_pad': '',
        'producto_pad': '',
        'territorializacion': resultado.territorializacion or '',
        'responsable_pad': resultado.responsable_pad or '',
        'cuenta_con_financiamiento': bool(resultado.cuenta_con_financiamiento),
        'indicador': (indicador.indicador if indicador else '') or '',
        'formula': (indicador.formula if indicador else '') or '',
        'unidad_medida': (indicador.unidad_medida if indicador else '') or '',
        'linea_base': _dec(indicador.linea_base if indicador else None),
        'meta_2030': _dec(indicador.meta_2030 if indicador else None),
        **{f'pf_{anio}': _dec(prog.get(str(anio))) for anio in range(2026, 2031)},
        'presupuesto_total': _dec(
            indicador.presupuesto_total if indicador else None
        ),
        **{f'presupuesto_{anio}': _dec(
            (presupuesto_anual or {}).get(str(anio))
        ) for anio in range(2026, 2031)},
    }


def _fila_matriz_a_producto(producto, indicador):
    """Fila de producto de la Matriz A (incluye programación financiera)."""
    resultado = producto.resultado_pad
    prog = indicador.programacion_fisica if indicador else {}
    presupuesto_anual = indicador.presupuesto_anual if indicador else {}
    return {
        'nivel': 'PRODUCTO_PAD',
        'tipo_fila': 'producto',
        'sector': resultado.sector or resultado.cod_sector or '',
        'cod_sector': resultado.cod_sector or '',
        'cod_geografico': resultado.cod_geografico or '',
        'politica': resultado.politica or '',
        'cod_lineamiento_pad': resultado.lineamiento_pad or '',
        'codigo_resultado_pad': resultado.codigo_resultado or '',
        'resultado_pad': resultado.denominacion or '',
        'codigo_producto_pad': producto.codigo_producto or '',
        'producto_pad': producto.denominacion or '',
        'territorializacion': producto.territorializacion or '',
        'responsable_pad': producto.responsable or '',
        'cuenta_con_financiamiento': bool(producto.cuenta_con_financiamiento),
        'indicador': (indicador.indicador if indicador else '') or '',
        'formula': (indicador.formula if indicador else '') or '',
        'unidad_medida': (indicador.unidad_medida if indicador else '') or '',
        'linea_base': _dec(indicador.linea_base if indicador else None),
        'meta_2030': _dec(indicador.meta_2030 if indicador else None),
        **{f'pf_{anio}': _dec(prog.get(str(anio))) for anio in range(2026, 2031)},
        'presupuesto_total': _dec(
            indicador.presupuesto_total if indicador else None
        ),
        **{f'presupuesto_{anio}': _dec(
            (presupuesto_anual or {}).get(str(anio))
        ) for anio in range(2026, 2031)},
    }


def _filas_matriz_a_borrador(datos, gestion):
    """Filas de Matriz A desde el borrador (1 por resultado + 1 por producto)."""
    nacional = _subseccion(datos, 'p1_nacional')
    sectorial = _subseccion(datos, 'p3_sectorial')
    territorial = _subseccion(datos, 'p4_territorial')
    lineamiento_sec = _subseccion(datos, 'p5_lineamiento')

    sector = sectorial.get('sector') or {}
    cgeo = territorial.get('cgeo') or {}
    lineamiento = lineamiento_sec.get('lineamiento') or {}

    lineamiento_id = _fk_id_o_none(LineamientoPADCatalogo, lineamiento.get('id'))
    correlativo_base = _correlativo_resultado(lineamiento_id, gestion)

    filas = []
    for i, res in enumerate(_obtener_resultados(datos)):
        codigo_resultado = (
            f"{cgeo.get('codigo', '')}.{lineamiento.get('codigo', '')}."
            f"{correlativo_base + i}"
        )
        ind_res = res.get('indicador') or {}
        pf_resultado = res.get('programacion_fisica') or {}
        base = {
            'nivel': 'RESULTADO',
            'tipo_fila': 'resultado',
            'sector': sector.get('denominacion', ''),
            'cod_sector': sector.get('codigo', ''),
            'cod_geografico': cgeo.get('codigo', ''),
            'politica': territorial.get('politica', ''),
            'cod_lineamiento_pad': lineamiento.get('codigo', ''),
            'codigo_resultado_pad': codigo_resultado,
            'resultado_pad': res.get('denominacion', ''),
            'codigo_producto_pad': '',
            'producto_pad': '',
            'territorializacion': res.get('territorializacion', ''),
            'responsable_pad': res.get('responsable', ''),
            'cuenta_con_financiamiento': bool(
                res.get('cuenta_con_financiamiento', False)
            ),
            'indicador': ind_res.get('indicador', ''),
            'formula': ind_res.get('formula', ''),
            'unidad_medida': ind_res.get('unidad_medida', ''),
            'linea_base': _dec(ind_res.get('linea_base')),
            'meta_2030': _dec(ind_res.get('meta_2030')),
            **{f'pf_{anio}': _dec(pf_resultado.get(str(anio))) for anio in range(2026, 2031)},
            'presupuesto_total': _dec(res.get('presupuesto_total')),
            **{f'presupuesto_{anio}': _dec(
                (res.get('presupuesto_anual') or {}).get(str(anio))
            ) for anio in range(2026, 2031)},
        }
        filas.append(base)
        for j, prod in enumerate(res.get('productos') or [], start=1):
            ind_prod = prod.get('indicador') or {}
            pf_producto = prod.get('programacion_fisica') or {}
            fila_producto = {
                **base,
                'nivel': 'PRODUCTO',
                'tipo_fila': 'producto',
                'codigo_producto_pad': f'{codigo_resultado}.{j}',
                'producto_pad': prod.get('denominacion', ''),
                'territorializacion': prod.get('territorializacion', ''),
                'responsable_pad': prod.get('responsable', ''),
                'cuenta_con_financiamiento': bool(
                    prod.get('cuenta_con_financiamiento', False)
                ),
                'indicador': ind_prod.get('indicador', ''),
                'formula': ind_prod.get('formula', ''),
                'unidad_medida': ind_prod.get('unidad_medida', ''),
                'linea_base': _dec(ind_prod.get('linea_base')),
                'meta_2030': _dec(ind_prod.get('meta_2030')),
                **{f'pf_{anio}': _dec(pf_producto.get(str(anio))) for anio in range(2026, 2031)},
                'presupuesto_total': _dec(prod.get('presupuesto_total')),
                **{f'presupuesto_{anio}': _dec(
                    (prod.get('presupuesto_anual') or {}).get(str(anio))
                ) for anio in range(2026, 2031)},
            }
            filas.append(fila_producto)
    return filas


def construir_matriz_a(borrador):
    """Matriz A (27 columnas) del borrador.

    Si el borrador está materializado, las filas salen de los modelos
    (ResultadoPAD/ProductoPAD/IndicadorCadena); si no, se arman server-side
    desde ``borrador.datos`` (lectura en vivo del wizard incremental).

    Contrato de filas: por cada resultado 1 fila de resultado + 1 fila por
    cada producto (los resultados y productos de TODA la colección conviven
    en la misma matriz, tal como el Excel).
    """
    if borrador.id_resultado_pad_id and borrador.estado == BorradorMatrizPAD.ESTADO_COMPLETO:
        filas = []
        for resultado in _resultados_del_borrador(borrador).prefetch_related(
            'productos__indicadores',
        ).select_related(
            'resultado_sectorial_catalogo', 'entidad_territorial_cgeo',
        ):
            ind_resultado = resultado.indicadores.filter(
                nivel_indicador='RESULTADO_PAD',
            ).first()
            filas.append(_fila_matriz_a_resultado(resultado, ind_resultado))
            for producto in resultado.productos.all():
                ind_producto = producto.indicadores.filter(
                    nivel_indicador='PRODUCTO_PAD',
                ).first()
                filas.append(_fila_matriz_a_producto(producto, ind_producto))
        return filas

    return _filas_matriz_a_borrador(borrador.datos or {}, borrador.gestion)


# ---------------------------------------------------------------------------
# Filas de Matriz B (34 columnas)
# ---------------------------------------------------------------------------

def _bloque_nacional_b(resultado):
    """Bloques A-D de la Matriz B desde el modelo ResultadoPAD."""
    return {
        'cod_eje_pgdesa': resultado.cod_eje_pgdesa or '',
        'objetivo_impacto': resultado.objetivo_impacto or '',
        'cod_componente_pdesa': resultado.cod_componente_pdesa or '',
        'objetivo_efecto': resultado.objetivo_efecto or '',
        'ods': ', '.join(a.codigo for a in resultado.acuerdo_ods.all()),
        'ndc': ', '.join(a.codigo for a in resultado.acuerdo_ndc.all()),
        'ndt': ', '.join(a.codigo for a in resultado.acuerdo_ndt.all()),
        'compromiso_3030': ', '.join(
            a.codigo for a in resultado.acuerdo_kmgbf.all()
        ),
        'cod_sector': resultado.cod_sector or '',
        'sector': resultado.sector or '',
        'cod_resultado_pds': resultado.cod_resultado_pds or '',
        'resultado_pds': resultado.resultado_pds or '',
        'cod_geografico': resultado.cod_geografico or '',
        'eta': resultado.eta or '',
        'cod_lineamiento_pad': resultado.lineamiento_pad or '',
        'codigo_resultado_pad': resultado.codigo_resultado or '',
        'resultado_pad': resultado.denominacion or '',
    }


def _fila_matriz_b_resultado(resultado):
    ind = resultado.indicadores.filter(
        nivel_indicador='RESULTADO_PAD',
    ).first()
    prog = ind.programacion_fisica if ind else {}
    presupuesto_anual = ind.presupuesto_anual if ind else {}
    return {
        **_bloque_nacional_b(resultado),
        'nivel': 'RESULTADO_PAD',
        'tipo_fila': 'resultado',
        'codigo_producto_pad': '',
        'producto_pad': '',
        'indicador': (ind.indicador if ind else '') or '',
        'formula': (ind.formula if ind else '') or '',
        'unidad_medida': (ind.unidad_medida if ind else '') or '',
        'linea_base': _dec(ind.linea_base if ind else None),
        'meta_2030': _dec(ind.meta_2030 if ind else None),
        **{f'pf_{anio}': _dec(prog.get(str(anio))) for anio in range(2026, 2031)},
        'presupuesto_total': _dec(ind.presupuesto_total if ind else None),
        **{f'presupuesto_{anio}': _dec(
            (presupuesto_anual or {}).get(str(anio))
        ) for anio in range(2026, 2031)},
    }


def _fila_matriz_b_producto(producto, ind):
    resultado = producto.resultado_pad
    prog = ind.programacion_fisica if ind else {}
    presupuesto_anual = ind.presupuesto_anual if ind else {}
    return {
        **_bloque_nacional_b(resultado),
        'nivel': 'PRODUCTO_PAD',
        'tipo_fila': 'producto',
        'codigo_producto_pad': producto.codigo_producto or '',
        'producto_pad': producto.denominacion or '',
        'indicador': (ind.indicador if ind else '') or '',
        'formula': (ind.formula if ind else '') or '',
        'unidad_medida': (ind.unidad_medida if ind else '') or '',
        'linea_base': _dec(ind.linea_base if ind else None),
        'meta_2030': _dec(ind.meta_2030 if ind else None),
        **{f'pf_{anio}': _dec(prog.get(str(anio))) for anio in range(2026, 2031)},
        'presupuesto_total': _dec(ind.presupuesto_total if ind else None),
        **{f'presupuesto_{anio}': _dec(
            (presupuesto_anual or {}).get(str(anio))
        ) for anio in range(2026, 2031)},
    }


def _filas_matriz_b_borrador(datos, gestion):
    """Filas de Matriz B desde el borrador (1 por resultado + 1 por producto)."""
    nacional = _subseccion(datos, 'p1_nacional')
    acuerdos = _subseccion(datos, 'p2_acuerdos')
    sectorial = _subseccion(datos, 'p3_sectorial')
    territorial = _subseccion(datos, 'p4_territorial')
    lineamiento_sec = _subseccion(datos, 'p5_lineamiento')

    eje = nacional.get('eje') or {}
    componente = nacional.get('componente') or {}
    ods = _acuerdo_o_nada(acuerdos.get('ods'))
    ndc = _acuerdo_o_nada(acuerdos.get('ndc'))
    ndt = _acuerdo_o_nada(acuerdos.get('ndt'))
    kmgbf = _acuerdo_o_nada(acuerdos.get('kmgbf'))
    sector = sectorial.get('sector') or {}
    resultado_sectorial = sectorial.get('resultado_sectorial') or {}
    cgeo = territorial.get('cgeo') or {}
    lineamiento = lineamiento_sec.get('lineamiento') or {}

    lineamiento_id = _fk_id_o_none(LineamientoPADCatalogo, lineamiento.get('id'))
    correlativo_base = _correlativo_resultado(lineamiento_id, gestion)

    filas = []
    for i, res in enumerate(_obtener_resultados(datos)):
        codigo_resultado = (
            f"{cgeo.get('codigo', '')}.{lineamiento.get('codigo', '')}."
            f"{correlativo_base + i}"
        )
        ind_res = res.get('indicador') or {}
        pf_resultado = res.get('programacion_fisica') or {}
        base = {
            'cod_eje_pgdesa': eje.get('codigo', ''),
            'objetivo_impacto': nacional.get('objetivo_impacto', ''),
            'cod_componente_pdesa': componente.get('codigo', ''),
            'objetivo_efecto': nacional.get('objetivo_efecto', ''),
            'ods': ods.get('codigo', ''),
            'ndc': ndc.get('codigo', ''),
            'ndt': ndt.get('codigo', ''),
            'compromiso_3030': kmgbf.get('codigo', ''),
            'cod_sector': sector.get('codigo', ''),
            'sector': sector.get('denominacion', ''),
            'cod_resultado_pds': resultado_sectorial.get('codigo', ''),
            'resultado_pds': resultado_sectorial.get('denominacion', ''),
            'cod_geografico': cgeo.get('codigo', ''),
            'eta': territorial.get('eta', ''),
            'cod_lineamiento_pad': lineamiento.get('codigo', ''),
            'codigo_resultado_pad': codigo_resultado,
            'resultado_pad': res.get('denominacion', ''),
            'nivel': 'RESULTADO',
            'tipo_fila': 'resultado',
            'codigo_producto_pad': '',
            'producto_pad': '',
            'indicador': ind_res.get('indicador', ''),
            'formula': ind_res.get('formula', ''),
            'unidad_medida': ind_res.get('unidad_medida', ''),
            'linea_base': _dec(ind_res.get('linea_base')),
            'meta_2030': _dec(ind_res.get('meta_2030')),
            **{f'pf_{anio}': _dec(pf_resultado.get(str(anio))) for anio in range(2026, 2031)},
            'presupuesto_total': _dec(res.get('presupuesto_total')),
            **{f'presupuesto_{anio}': _dec(
                (res.get('presupuesto_anual') or {}).get(str(anio))
            ) for anio in range(2026, 2031)},
        }
        filas.append(base)
    return filas


def construir_matriz_b(borrador):
    """Matriz B (34 columnas) del borrador.

    Igual contrato que ``construir_matriz_a``: modelos si está materializado,
    borrador.datos en caso contrario (lectura en vivo). La Matriz B oficial
    (guía 4.5.2 / Excel MATRICES A Y B) solo muestra filas a NIVEL DE
    RESULTADO territorial: 1 fila por resultado, SIN desglosar productos.
    """
    if borrador.id_resultado_pad_id and borrador.estado == BorradorMatrizPAD.ESTADO_COMPLETO:
        filas = []
        for resultado in _resultados_del_borrador(borrador).prefetch_related(
            'productos__indicadores', 'acuerdo_ods', 'acuerdo_ndc',
            'acuerdo_ndt', 'acuerdo_kmgbf',
        ):
            filas.append(_fila_matriz_b_resultado(resultado))
        return filas

    return _filas_matriz_b_borrador(borrador.datos or {}, borrador.gestion)


# ---------------------------------------------------------------------------
# Vista acumulada de la gestión (todas las matrices materializadas)
# ---------------------------------------------------------------------------

def _resultados_gestion(gestion):
    """Resultados PAD materializados de la gestión completa.

    Acumula TODOS los ResultadoPAD con ``vigencia_desde=gestion``: los que
    provienen de borradores COMPLETO materializados más cualquier otro
    ResultadoPAD existente de la gestión (sin migraciones ni supuestos sobre
    el origen). Orden estable: cgeo, lineamiento, resultado.
    """
    return ResultadoPAD.objects.filter(
        vigencia_desde=gestion,
    ).order_by(
        'cod_geografico', 'lineamiento_pad', 'codigo_resultado',
    )


def construir_matriz_a_gestion(gestion):
    """Matriz A (27 columnas) ACUMULADA de la gestión completa.

    Una sola Matriz A con TODOS los resultados/productos materializados de la
    gestión (todos los borradores COMPLETO + cualquier ResultadoPAD existente
    con ``vigencia_desde=gestion``). Reutiliza la misma lógica de filas que
    ``construir_matriz_a`` (modelos materializados): por cada resultado 1 fila
    de resultado + 1 fila por producto. Orden: cgeo, lineamiento, resultado,
    producto.
    """
    filas = []
    resultados = _resultados_gestion(gestion).prefetch_related(
        'productos__indicadores',
    ).select_related(
        'resultado_sectorial_catalogo', 'entidad_territorial_cgeo',
    )
    for resultado in resultados:
        ind_resultado = resultado.indicadores.filter(
            nivel_indicador='RESULTADO_PAD',
        ).first()
        filas.append(_fila_matriz_a_resultado(resultado, ind_resultado))
        for producto in resultado.productos.order_by('codigo_producto'):
            ind_producto = producto.indicadores.filter(
                nivel_indicador='PRODUCTO_PAD',
            ).first()
            filas.append(_fila_matriz_a_producto(producto, ind_producto))
    return filas


def construir_matriz_b_gestion(gestion):
    """Matriz B (34 columnas) ACUMULADA de la gestión completa.

    Igual contrato que ``construir_matriz_a_gestion`` pero para la Matriz B:
    acumula las filas a NIVEL DE RESULTADO (1 por resultado, sin productos,
    según la Matriz B oficial de la guía 4.5.2) de todos los resultados
    materializados de la gestión en una sola matriz.
    """
    filas = []
    resultados = _resultados_gestion(gestion).prefetch_related(
        'productos__indicadores', 'acuerdo_ods', 'acuerdo_ndc',
        'acuerdo_ndt', 'acuerdo_kmgbf',
    )
    for resultado in resultados:
        filas.append(_fila_matriz_b_resultado(resultado))
    return filas


def _dec(value):
    """Numérico a string normalizado para las matrices; '' si es None.

    Normaliza decimales (34000000.00 → '34000000'; 10.5000 → '10.5'):
    las matrices PAD se capturan sin decimales en la guía.
    """
    if value is None or value == '':
        return ''
    try:
        num = Decimal(str(value))
    except (ValueError, TypeError):
        return str(value)
    if num == num.to_integral():
        return str(int(num))
    return str(num.normalize())
