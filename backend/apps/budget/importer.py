"""Importador Excel del ciclo presupuestario SIS-POA (Fase 5).

Flujo (staging, nunca aplicar directo — decisión 13 del plan de implementación):

    1. `parsear_libro`      — lee la planilla, detecta el header (puede estar
                              desplazado: logos, títulos, filas vacías, celdas
                              combinadas), clasifica las filas (P/SP/TS/T) y
                              construye `ImportDetalle` con datos normalizados.
    2. `validar_importacion`— severidades INFO/WARNING/ERROR/CRITICAL por fila;
                              con ERROR/CRITICAL la importación NO pasa a
                              VALIDADO (queda en STAGING con los hallazgos).
    3. `aplicar_importacion`— SOLO sin CRITICAL sin resolver; crea aperturas
                              BORRADOR (sin consumir disponibilidad — la
                              fijación de la Fase 7 valida el total) y registra
                              auditoría.

Perfiles (`PERFILES`): cada perfil define las columnas esperadas, el mapeo
columna->campo por defecto y el mapeo de fuentes de financiamiento por columna
de monto (CT/RE/ORE/IDH/TGN). El usuario puede corregir el mapeo (POST map);
el mapeo efectivo = defaults del perfil + overrides del usuario.

Convenciones:
    - Códigos (programa/subprograma/sisin/actividad) SIEMPRE string: se
      preservan ceros iniciales ('097' -> '097'); si la celda vino numérica se
      intenta reconstruir con el formato de celda (number_format '000') y se
      advierte.
    - Montos: Decimal, nunca float. Se aceptan '1.234.567,89' (coma decimal),
      '1,234,567.89', prefijos tipo 'Bs', '(123)' -> negativo y '' -> 0. Los
      errores de Excel (#REF!/#VALUE!/#DIV/0!/#N/A) son CRITICAL.
    - SUBTOTAL/TOTAL se conservan como candidatas pero NO generan aperturas.
"""
from __future__ import annotations

import re
import unicodedata
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.auditoria.models import EventoAuditoria
from apps.auditoria.services import registrar_evento

from .models import (
    AccionError,
    Allocation,
    AllocationSource,
    ClasificacionFila,
    EstadoApertura,
    EstadoDetalle,
    EstadoImportacion,
    ImportDetalle,
    ImportError,
    PerfilImportacion,
    SeveridadError,
)
from .services import registrar_auditoria, version_distribucion_activa

# ---------------------------------------------------------------------------
# Perfiles
# ---------------------------------------------------------------------------

# Errores de Excel que pueden aparecer en celdas de monto.
ERRORES_EXCEL = {
    '#REF!', '#VALUE!', '#DIV/0!', '#N/A', '#NAME?', '#NULL!', '#NUM!',
}

# Campos de monto de `datos_json` (normalizados a Decimal).
CAMPOS_MONTO = ('saldo', 'ct', 're', 'ore', 'idh', 'tgn', 'total')
# Campos de código (string, ceros iniciales preservados).
CAMPOS_CODIGO = ('programa', 'subprograma', 'sisin', 'actividad', 'da', 'ue')
# Campos de texto libre (trim + colapso de espacios).
CAMPOS_TEXTO = ('unidad', 'distrito', 'denominacion', 'tipo')

# Fuentes de financiamiento por defecto por columna de monto (por perfil;
# configurable en mapeo_json['fuentes']). La validación verifica que el código
# exista en `catalogos.FuenteFinanciamiento` para la gestión.
FUENTES_DEFAULT = {'ct': '41', 're': '20', 'ore': '20', 'idh': '41', 'tgn': '11'}

# Columnas de la planilla GASTOS (estructura oficial 2023 y planilla actual).
_COLUMNAS_GASTOS = [
    'N°', 'UNIDAD EJECUTIVA', 'DISTRITO URBANO Y RURAL',
    'DIRECCIÓN ADMINISTRATIVA', 'UNIDAD EJECUTORA', 'V', 'PROG.',
    'CODIGO SISIN WEB', 'ACT.', 'DENOMINACIÓN DEL PROYECTO',
    'Saldo gestión anterior', 'CT', 'RE', 'ORE', 'IDH', 'TGN',
    'Total Presupuesto',
]

# Mapeo por defecto de la planilla histórica: columna_excel -> campo.
_MAPEO_GASTOS_HISTORICO = {
    'UNIDAD EJECUTIVA': 'unidad',
    'DISTRITO URBANO Y RURAL': 'distrito',
    'DIRECCIÓN ADMINISTRATIVA': 'da',
    'UNIDAD EJECUTORA': 'ue',
    'V': 'tipo',
    'PROG.': 'programa',
    'CODIGO SISIN WEB': 'sisin',
    'ACT.': 'actividad',
    'DENOMINACIÓN DEL PROYECTO': 'denominacion',
    'Saldo gestión anterior': 'saldo',
    'CT': 'ct',
    'RE': 're',
    'ORE': 'ore',
    'IDH': 'idh',
    'TGN': 'tgn',
    'Total Presupuesto': 'total',
}

PERFILES = {
    PerfilImportacion.PIP_GASTOS_HISTORICO: {
        'columnas': _COLUMNAS_GASTOS,
        'mapeo': dict(_MAPEO_GASTOS_HISTORICO),
        'fuentes': dict(FUENTES_DEFAULT),
    },
    PerfilImportacion.PIP_GASTOS_ACTUAL: {
        # La planilla actual es similar a la histórica; se reutiliza el mismo
        # mapeo y el usuario puede corregirlo desde la UI (POST map).
        'columnas': _COLUMNAS_GASTOS,
        'mapeo': dict(_MAPEO_GASTOS_HISTORICO),
        'fuentes': dict(FUENTES_DEFAULT),
    },
    PerfilImportacion.OTRO: {
        'columnas': [],
        'mapeo': {},
        'fuentes': dict(FUENTES_DEFAULT),
    },
}


# ---------------------------------------------------------------------------
# Normalización
# ---------------------------------------------------------------------------

def es_error_excel(v) -> bool:
    """¿El valor es un error de Excel (#REF!, #VALUE!, #DIV/0!, #N/A…)?"""
    if not isinstance(v, str):
        return False
    return any(token in v.strip().upper() for token in ERRORES_EXCEL)


def normalizar_texto(v):
    """Trim + colapso de espacios múltiples; None -> ''."""
    if v is None:
        return ''
    s = str(v).strip()
    return re.sub(r'\s+', ' ', s)


def _normalizar_nombre_columna(nombre):
    """Nombre de columna normalizado para comparar (sin acentos/puntuación)."""
    s = normalizar_texto(nombre).lower()
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = ''.join(c if c.isalnum() or c.isspace() else ' ' for c in s)
    return re.sub(r'\s+', ' ', s).strip()


def normalizar_codigo(v, numero_formato=''):
    """Código a string preservando ceros iniciales; nunca int.

    Si la celda vino numérica (Excel) y el formato de celda pide ceros
    ('000'), se reconstruyen; el resto se normaliza a str sin ceros extra.
    """
    if v is None:
        return ''
    if isinstance(v, str):
        return v.strip()
    if isinstance(v, Decimal):
        if v == v.to_integral_value():
            v = int(v)
        else:
            return str(v)
    if isinstance(v, float) and not v.is_integer():
        return str(v)
    entero = int(v)
    texto = str(entero)
    if numero_formato:
        ceros = len(numero_formato.split('.')[0].replace('?', '').replace('#', ''))
        if ceros and len(texto) < ceros:
            texto = texto.zfill(ceros)
    return texto


def normalizar_monto(v):
    """Monto a Decimal; '' -> 0; '(123)' -> negativo; errores de Excel -> raise.

    Acepta '1.234.567,89' (coma decimal), '1,234,567.89' (punto decimal),
    prefijos como 'Bs 1.234' y errores de Excel que se detectan y rechazan.
    """
    if v is None:
        return Decimal('0.00')
    if isinstance(v, Decimal):
        return v
    if isinstance(v, bool):
        raise ValueError(f'Monto booleano no válido: {v!r}')
    if isinstance(v, (int, float)):
        if isinstance(v, float) and (v != v or v in (float('inf'), float('-inf'))):
            raise ValueError('Monto no numérico (NaN/Infinito).')
        return Decimal(str(v)).quantize(Decimal('0.01'))

    s = str(v).strip()
    if s == '':
        return Decimal('0.00')
    if es_error_excel(s):
        raise ValueError(f'Error de Excel en monto: {s}')

    negativo = False
    if s.startswith('(') and s.endswith(')'):
        negativo = True
        s = s[1:-1]
    elif s.startswith('-'):
        negativo = True
        s = s[1:]

    # Quitar prefijos de moneda y separadores no numéricos ('Bs 1.234').
    partes = re.findall(r'[\d.,]+', s)
    if not partes:
        raise ValueError(f'Monto no numérico: {v!r}')
    s = partes[-1]
    if s in ('', '.', ','):
        raise ValueError(f'Monto no numérico: {v!r}')

    # Decidir separador decimal: el último de los dos (o único ',' con 1-2
    # decimales → coma decimal; resto → separador de miles).
    if ',' in s and '.' in s:
        if s.rfind(',') > s.rfind('.'):
            s = s.replace('.', '').replace(',', '.')
        else:
            s = s.replace(',', '')
    elif ',' in s:
        trozos = s.split(',')
        if len(trozos) == 2 and len(trozos[1]) in (1, 2):
            s = s.replace(',', '.')
        else:
            s = s.replace(',', '')
    elif '.' in s:
        # Único separador '.': con exactamente 3 decimales es miles
        # ('Bs 1.234' → 1234.00); con 1-2 decimales es separador decimal.
        entero, _, dec = s.partition('.')
        if len(dec) == 3:
            s = s.replace('.', '')
    try:
        monto = Decimal(s)
    except InvalidOperation as exc:
        raise ValueError(f'Monto no numérico: {v!r}') from exc
    if negativo:
        monto = -monto
    return monto.quantize(Decimal('0.01'))


# ---------------------------------------------------------------------------
# Header y clasificación de filas
# ---------------------------------------------------------------------------

def detectar_header(filas, columnas_esperadas):
    """Índice de la fila del header dentro de `filas` (lista de filas).

    Coincidencia por nombre normalizado (mayúsculas/espacios tolerados); la
    fila con más columnas esperadas presentes es el header. None si no hay
    una coincidencia razonable (>= 3 columnas).
    """
    esperadas = {
        _normalizar_nombre_columna(c)
        for c in columnas_esperadas if c
    }
    mejor_indice, mejor_puntaje = None, 0
    for i, fila in enumerate(filas):
        puntaje = sum(
            1 for celda in fila
            if _normalizar_nombre_columna(str(celda)) in esperadas
        )
        if puntaje > mejor_puntaje:
            mejor_indice, mejor_puntaje = i, puntaje
    if mejor_puntaje < 3:
        return None
    return mejor_indice


def clasificar_fila(valores):
    """Clasifica una fila (dict campo->valor) según el tipo (columna V).

    P/PROGRAMA -> PROGRAM_HEADER; SP -> SUBPROGRAM_HEADER; TS -> SUBTOTAL;
    T/TOTAL -> TOTAL; fila completamente vacía -> EMPTY; resto -> DETAIL.
    """
    tipo = normalizar_texto(valores.get('tipo')).upper()
    if tipo in ('P', 'PROGRAMA'):
        return ClasificacionFila.PROGRAM_HEADER
    if tipo in ('SP', 'SUBPROGRAMA'):
        return ClasificacionFila.SUBPROGRAM_HEADER
    if tipo in ('TS', 'SUBTOTAL'):
        return ClasificacionFila.SUBTOTAL
    if tipo in ('T', 'TOTAL'):
        return ClasificacionFila.TOTAL
    if tipo:
        return ClasificacionFila.DETAIL
    if all(_celda_vacia(v) for v in valores.values()):
        return ClasificacionFila.EMPTY
    return ClasificacionFila.DETAIL


def _celda_vacia(v) -> bool:
    if v is None:
        return True
    if isinstance(v, str):
        return v.strip() == ''
    return False


def _decimal(datos, campo):
    """Monto de `datos_json` (str o None) como Decimal; None si no hay."""
    v = datos.get(campo)
    if v in (None, ''):
        return None
    try:
        return Decimal(str(v))
    except InvalidOperation:
        return None


# ---------------------------------------------------------------------------
# Parseo
# ---------------------------------------------------------------------------

def _mapeo_efectivo(importacion, mapeo=None):
    """Mapeo efectivo {columna_excel_norm: campo}: defaults del perfil + usuario."""
    perfil = PERFILES.get(importacion.perfil, PERFILES[PerfilImportacion.OTRO])
    columnas = dict(perfil['mapeo'])
    fuentes = dict(perfil['fuentes'])
    if mapeo:
        if isinstance(mapeo.get('columnas'), dict):
            for col, campo in mapeo['columnas'].items():
                if campo is None or campo == '':
                    columnas.pop(col, None)
                else:
                    columnas[col] = campo
        if isinstance(mapeo.get('fuentes'), dict):
            for campo_monto, codigo in mapeo['fuentes'].items():
                if codigo is None or codigo == '':
                    fuentes.pop(campo_monto, None)
                else:
                    fuentes[campo_monto] = str(codigo)
    return columnas, fuentes


def _normalizar_campo(campo, valor, numero_formato=''):
    """Normaliza un valor según el tipo de campo (texto/código/monto)."""
    if campo in CAMPOS_MONTO:
        return normalizar_monto(valor)
    if campo in CAMPOS_CODIGO:
        return normalizar_codigo(valor, numero_formato)
    return normalizar_texto(valor)


def parsear_libro(importacion, workbook, hoja=None, mapeo=None, usuario=None):
    """Parsea el libro: detecta header, clasifica filas y crea ImportDetalle.

    Solo DETAIL/SUBTOTAL/TOTAL se conservan (los headers P/SP y las filas
    vacías se descartan; SUBTOTAL/TOTAL quedan marcados y no generan
    aperturas). Devuelve la importación actualizada (mapeo_json efectivo,
    hoja_seleccionada). No crea ImportError: eso lo hace `validar_importacion`.
    Registra auditoría (importar) con el resultado del parseo (Fase 11).
    """
    columnas_efectivas, fuentes_efectivas = _mapeo_efectivo(importacion, mapeo)
    columnas_esperadas = (
        PERFILES.get(importacion.perfil, PERFILES[PerfilImportacion.OTRO])
        ['columnas']
    )

    importacion.detalles.all().delete()
    importacion.errores.all().delete()

    hojas = workbook.sheetnames
    hoja_objetivo = hoja or importacion.hoja_seleccionada or (
        hojas[0] if hojas else ''
    )
    if hoja_objetivo not in hojas:
        raise ValidationError(
            f'La hoja "{hoja_objetivo}" no existe en el libro '
            f'(hojas: {", ".join(hojas)}).'
        )

    header_por_hoja = {}
    for nombre in hojas:
        ws = workbook[nombre]
        filas = list(ws.iter_rows(values_only=True))
        idx = detectar_header(filas, columnas_esperadas)
        if idx is not None:
            header_por_hoja[nombre] = idx

    if hoja_objetivo not in header_por_hoja:
        # Buscar header también en la hoja seleccionada manualmente.
        ws = workbook[hoja_objetivo]
        filas = list(ws.iter_rows(values_only=True))
        idx = detectar_header(filas, columnas_esperadas)
        if idx is not None:
            header_por_hoja[hoja_objetivo] = idx

    if hoja_objetivo not in header_por_hoja:
        raise ValidationError(
            'No se pudo detectar la fila de encabezados en la hoja '
            f'"{hoja_objetivo}" (¿el perfil de columnas es correcto?).'
        )

    hoja_final = hoja_objetivo
    ws = workbook[hoja_final]
    header_idx = header_por_hoja[hoja_final]
    header_row = list(ws.iter_rows(min_row=header_idx + 1, max_row=header_idx + 1,
                                   values_only=True))[0]
    # Columna por campo: {campo: indice}. El usuario mapea por nombre de
    # columna; los nombres se normalizan para tolerar diferencias menores.
    indice_por_nombre = {
        _normalizar_nombre_columna(str(v)): i
        for i, v in enumerate(header_row) if not _celda_vacia(v)
    }
    mapeo_columnas = {}
    for col, campo in columnas_efectivas.items():
        indice = indice_por_nombre.get(_normalizar_nombre_columna(str(col)))
        if indice is not None:
            mapeo_columnas[campo] = indice

    for num_fila, row in enumerate(
        ws.iter_rows(min_row=header_idx + 2), start=header_idx + 2
    ):
        valores = {}
        raw_valores = {}
        raw_tipos = {}
        raw_formatos = {}
        for campo, indice in mapeo_columnas.items():
            celda = row[indice] if indice < len(row) else None
            valor = celda.value if celda is not None else None
            if _celda_vacia(valor):
                raw_valores[campo] = ''
                valores[campo] = ''
                continue
            raw_valores[campo] = valor
            raw_tipos[campo] = getattr(celda, 'data_type', '')
            raw_formatos[campo] = getattr(celda, 'number_format', '')
            try:
                valores[campo] = _normalizar_campo(
                    campo, valor, raw_formatos.get(campo, ''),
                )
            except ValueError:
                # Monto ilegible (error de Excel, texto no numérico…): se
                # conserva la fila y la validación registra el CRITICAL.
                valores[campo] = None

        clasificacion = clasificar_fila(valores)
        if clasificacion in (
            ClasificacionFila.PROGRAM_HEADER,
            ClasificacionFila.SUBPROGRAM_HEADER,
            ClasificacionFila.EMPTY,
            ClasificacionFila.UNKNOWN,
        ):
            continue

        datos = {
            campo: valores.get(campo, '')
            for campo in CAMPOS_TEXTO + CAMPOS_CODIGO
        }
        # Montos: str(Decimal) para que JSONField sea serializable
        # (PostgreSQL/psycopg2 no acepta Decimal en JSON).
        for campo in CAMPOS_MONTO:
            monto = valores.get(campo)
            datos[campo] = str(monto) if isinstance(monto, Decimal) else monto
        datos['_hoja'] = hoja_final
        datos['_raw'] = {
            'valores': raw_valores,
            'tipos': raw_tipos,
            'formatos': raw_formatos,
        }
        ImportDetalle.objects.create(
            importacion=importacion,
            fila=num_fila,
            clasificacion=clasificacion,
            datos_json=datos,
            estado=EstadoDetalle.PENDIENTE,
        )

    importacion.mapeo_json = {
        'hoja': hoja_final,
        'columnas': {
            col: campo for campo, col in reversed(list(mapeo_columnas.items()))
        },
        'fuentes': fuentes_efectivas,
    }
    importacion.hoja_seleccionada = hoja_final
    importacion.save(update_fields=['mapeo_json', 'hoja_seleccionada', 'updated_at'])
    registrar_auditoria(
        usuario,
        'IMPORT',
        'BudgetImport',
        importacion.id,
        {'hoja': None, 'detalles': 0},
        {
            'hoja': hoja_final,
            'detalles': importacion.detalles.count(),
            'estado': importacion.estado,
        },
        gestion=importacion.gestion.anio,
        motivo=(
            f'Planilla "{importacion.filename}" parseada: '
            f'{importacion.detalles.count()} fila(s) en la hoja {hoja_final} '
            f'(gestión {importacion.gestion.anio})'
        ),
    )
    return importacion


# ---------------------------------------------------------------------------
# Validación
# ---------------------------------------------------------------------------

def _crear_error(importacion, detalle, severidad, mensaje, campo='',
                 valor_original='', valor_normalizado='', accion=None):
    return ImportError.objects.create(
        importacion=importacion,
        detalle=detalle,
        fila=detalle.fila if detalle else 0,
        campo=campo,
        valor_original=str(valor_original) if valor_original not in (None, '') else '',
        valor_normalizado=str(valor_normalizado) if valor_normalizado not in (None, '') else '',
        severidad=severidad,
        mensaje=mensaje,
        accion=accion or AccionError.NINGUNA,
    )


def _fuentes_codigos_validos(importacion):
    from apps.catalogos.models import FuenteFinanciamiento
    return set(
        FuenteFinanciamiento.objects
        .filter(gestion=importacion.gestion.anio)
        .values_list('codigo', flat=True)
    )


def _codigos_programaticos(importacion):
    from .models import ProgrammaticCategory
    return set(
        ProgrammaticCategory.objects
        .filter(gestion=importacion.gestion)
        .values_list('codigo', flat=True)
    )


def _nombres_distritos():
    from apps.territorio.models import Distrito
    return {d.nombre.strip().lower(): d for d in Distrito.objects.all()}


def validar_importacion(importacion, usuario=None):
    """Valida los detalles DETAIL y crea ImportError por hallazgo.

    Severidades:
        CRITICAL — monto negativo, fuente inexistente en catálogos, programa/
                   subprograma inexistente en ProgrammaticCategory, error de
                   Excel o monto no numérico.
        ERROR    — denominación vacía, duplicado (sisin+actividad+denominacion).
        WARNING  — distrito no encontrado, códigos numéricos (ceros perdidos),
                   campos opcionales faltantes.
        INFO     — normalizaciones aplicadas (trim/espacios).

    La importación pasa a VALIDADO solo sin ERROR/CRITICAL (queda STAGING con
    los hallazgos en caso contrario). Re-ejecutable: borra errores previos.
    Registra auditoría (modificar) con los conteos por severidad (Fase 11).
    """
    from apps.catalogos.models import FuenteFinanciamiento

    importacion.errores.all().delete()
    gestion = importacion.gestion
    fuentes_validas = _fuentes_codigos_validos(importacion)
    codigos_prog = _codigos_programaticos(importacion)
    distritos = _nombres_distritos()
    _, fuentes_efectivas = _mapeo_efectivo(importacion, importacion.mapeo_json)

    vistos = set()
    tiene_error = False

    for detalle in importacion.detalles.filter(
        clasificacion=ClasificacionFila.DETAIL
    ).order_by('fila'):
        datos = detalle.datos_json
        raw = datos.get('_raw', {})
        valores_raw = raw.get('valores', {})
        tipos_raw = raw.get('tipos', {})
        hallazgos = []

        def error(*args, **kwargs):
            hallazgos.append(_crear_error(
                importacion, detalle, *args, **kwargs,
            ))

        # -- CRITICAL: error de Excel / monto no numérico -------------------
        for campo in CAMPOS_MONTO:
            bruto = valores_raw.get(campo, '')
            if es_error_excel(bruto):
                error(
                    SeveridadError.CRITICAL,
                    f'Error de Excel ({bruto}) en el campo {campo}.',
                    campo=campo, valor_original=bruto,
                    accion=AccionError.REEMPLAZAR,
                )
            elif not _celda_vacia(bruto) and _decimal(datos, campo) is None:
                error(
                    SeveridadError.CRITICAL,
                    f'Monto no numérico en el campo {campo} ({bruto!r}).',
                    campo=campo, valor_original=bruto,
                    accion=AccionError.REEMPLAZAR,
                )

        # -- CRITICAL: monto negativo ---------------------------------------
        for campo in CAMPOS_MONTO:
            monto = _decimal(datos, campo)
            if monto is not None and monto < 0:
                error(
                    SeveridadError.CRITICAL,
                    f'Monto negativo ({monto}) en el campo {campo}.',
                    campo=campo, valor_original=valores_raw.get(campo, ''),
                    valor_normalizado=str(monto),
                )

        # -- CRITICAL: fuente de financiamiento inexistente ------------------
        for campo_monto, codigo in fuentes_efectivas.items():
            if campo_monto not in CAMPOS_MONTO:
                continue
            monto = _decimal(datos, campo_monto)
            if monto is not None and monto > 0 and codigo not in fuentes_validas:
                error(
                    SeveridadError.CRITICAL,
                    f'La fuente de financiamiento "{codigo}" del campo '
                    f'{campo_monto} no existe en los catálogos para la '
                    f'gestión {gestion.anio}.',
                    campo=campo_monto, valor_original=codigo,
                    accion=AccionError.ASIGNAR,
                )

        # -- CRITICAL: programa/subprograma inexistente ----------------------
        for nivel, campo in (('programa', 'programa'), ('subprograma', 'subprograma')):
            codigo = normalizar_codigo(datos.get(campo))
            if codigo and codigo not in codigos_prog:
                error(
                    SeveridadError.CRITICAL,
                    f'{nivel.capitalize()} "{codigo}" no existe en las '
                    'categorías programáticas de la gestión.',
                    campo=campo, valor_original=valores_raw.get(campo, ''),
                    valor_normalizado=codigo,
                    accion=AccionError.ASIGNAR,
                )

        # -- ERROR: denominación vacía ---------------------------------------
        denominacion = normalizar_texto(datos.get('denominacion'))
        if not denominacion:
            error(
                SeveridadError.ERROR,
                'La denominación del proyecto está vacía.',
                campo='denominacion',
                valor_original=valores_raw.get('denominacion', ''),
            )

        # -- ERROR: duplicado (sisin + actividad + denominacion) -------------
        clave = (
            normalizar_codigo(datos.get('sisin')),
            normalizar_codigo(datos.get('actividad')),
            denominacion,
        )
        if clave in vistos:
            error(
                SeveridadError.ERROR,
                'Fila duplicada (misma combinación SISIN + actividad + '
                'denominación).',
                campo='denominacion',
                valor_original=valores_raw.get('denominacion', ''),
                accion=AccionError.IGNORAR,
            )
        else:
            vistos.add(clave)

        # -- ERROR: códigos numéricos en Excel (ceros posiblemente perdidos) -
        for campo in CAMPOS_CODIGO:
            if tipos_raw.get(campo) == 'n' and not _celda_vacia(valores_raw.get(campo)):
                error(
                    SeveridadError.WARNING,
                    f'El campo {campo} vino numérico en Excel; si tenía ceros '
                    'iniciales se perdieron. Verifique el dato.',
                    campo=campo, valor_original=valores_raw.get(campo, ''),
                    valor_normalizado=datos.get(campo) or '',
                    accion=AccionError.NORMALIZAR,
                )

        # -- WARNING: distrito no encontrado ---------------------------------
        distrito = normalizar_texto(datos.get('distrito'))
        if distrito and distrito.lower() not in distritos:
            error(
                SeveridadError.WARNING,
                f'Distrito "{distrito}" no encontrado; la apertura quedará '
                'sin distrito.',
                campo='distrito', valor_original=valores_raw.get('distrito', ''),
                accion=AccionError.IGNORAR,
            )

        # -- WARNING: campos opcionales faltantes ----------------------------
        for campo in ('unidad', 'da', 'ue', 'programa'):
            if _celda_vacia(datos.get(campo)):
                error(
                    SeveridadError.WARNING,
                    f'Campo opcional {campo} sin valor.',
                    campo=campo, accion=AccionError.NINGUNA,
                )

        # -- INFO: normalizaciones aplicadas ---------------------------------
        for campo in CAMPOS_TEXTO:
            bruto = valores_raw.get(campo)
            if isinstance(bruto, str) and bruto != normalizar_texto(bruto):
                error(
                    SeveridadError.INFO,
                    f'Texto normalizado (trim/espacios) en {campo}.',
                    campo=campo, valor_original=bruto,
                    valor_normalizado=normalizar_texto(bruto),
                    accion=AccionError.NORMALIZAR,
                )

        criticos = [h for h in hallazgos if h.severidad in (
            SeveridadError.ERROR, SeveridadError.CRITICAL,
        )]
        if criticos:
            detalle.estado = EstadoDetalle.ERROR
            tiene_error = True
        else:
            detalle.estado = EstadoDetalle.VALIDO
        detalle.errores_json = [
            {'campo': h.campo, 'severidad': h.severidad, 'mensaje': h.mensaje}
            for h in hallazgos
        ]
        detalle.save(update_fields=['estado', 'errores_json', 'updated_at'])

    importacion.estado = (
        EstadoImportacion.STAGING if tiene_error else EstadoImportacion.VALIDADO
    )
    importacion.save(update_fields=['estado', 'updated_at'])
    conteos = _conteos_errores(importacion)
    registrar_auditoria(
        usuario,
        'UPDATE',
        'BudgetImport',
        importacion.id,
        {'estado': (
            EstadoImportacion.STAGING
            if tiene_error else EstadoImportacion.VALIDADO
        )},
        {'estado': importacion.estado, 'errores': conteos},
        gestion=importacion.gestion.anio,
        motivo=(
            f'Planilla "{importacion.filename}" validada: '
            f'{conteos["ERROR"] + conteos["CRITICAL"]} error(es) — '
            f'estado {importacion.get_estado_display()} '
            f'(gestión {importacion.gestion.anio})'
        ),
    )
    return conteos


def _conteos_errores(importacion):
    """{severidad: cantidad} de errores de la importación."""
    from django.db.models import Count
    conteos = {s: 0 for s, _ in SeveridadError.CHOICES}
    for fila in importacion.errores.values('severidad').annotate(n=Count('id')):
        conteos[fila['severidad']] = fila['n']
    return conteos


# ---------------------------------------------------------------------------
# Aplicación
# ---------------------------------------------------------------------------

@transaction.atomic
def aplicar_importacion(importacion, usuario):
    """Aplica la importación: crea aperturas BORRADOR + fuentes + auditoría.

    DECISIÓN (documentada): las aperturas se crean directamente en BORRADOR
    SIN pasar por `crear_allocation` — no consumen disponibilidad (no se
    valida contra el techo distribuible). La fijación de la Fase 7 valida el
    total (Σfuente = techo − reservas) antes de inmutar la versión. Solo los
    detalles DETAIL válidos generan aperturas; SUBTOTAL/TOTAL no.

    Requisito: sin errores CRITICAL sin resolver (la validación los marca).
    """
    from apps.catalogos.models import FuenteFinanciamiento
    from .models import ProgrammaticCategory

    criticos = importacion.errores.filter(
        severidad=SeveridadError.CRITICAL, resuelto=False,
    )
    if criticos.exists():
        raise ValidationError(
            f'No se puede aplicar la importación: hay {criticos.count()} '
            'error(es) crítico(s) sin resolver.'
        )
    if importacion.estado == EstadoImportacion.APLICADO:
        raise ValidationError('La importación ya fue aplicada.')

    gestion = importacion.gestion
    _, fuentes_efectivas = _mapeo_efectivo(importacion, importacion.mapeo_json)
    fuentes_por_codigo = {
        f.codigo: f for f in
        FuenteFinanciamiento.objects.filter(gestion=gestion.anio)
    }
    distritos = _nombres_distritos()
    version = version_distribucion_activa(gestion)

    creadas = 0
    total_montos = Decimal('0.00')
    for detalle in importacion.detalles.filter(
        clasificacion=ClasificacionFila.DETAIL,
        estado=EstadoDetalle.VALIDO,
    ).order_by('fila'):
        datos = detalle.datos_json
        denominacion = normalizar_texto(datos.get('denominacion'))
        if not denominacion:
            continue

        distrito = normalizar_texto(datos.get('distrito'))
        distrito_obj = distritos.get(distrito.lower()) if distrito else None
        programa = normalizar_codigo(datos.get('programa'))
        categoria = (
            ProgrammaticCategory.objects
            .filter(gestion=gestion, codigo=programa)
            .first()
            if programa else None
        )

        allocation = Allocation.objects.create(
            gestion=gestion,
            version=version,
            distrito=distrito_obj,
            categoria=categoria,
            codigo_sisin=normalizar_codigo(datos.get('sisin')),
            actividad_codigo=normalizar_codigo(datos.get('actividad')),
            denominacion=denominacion,
            tipo_apertura='DETAIL',
            estado=EstadoApertura.BORRADOR,
            created_by=usuario,
            updated_by=usuario,
        )
        # Montos por fuente (CT e IDH pueden mapear al mismo código de
        # catálogo → se suman en una sola fila AllocationSource).
        por_fuente = {}
        for campo_monto in ('ct', 're', 'ore', 'idh', 'tgn'):
            monto = _decimal(datos, campo_monto)
            if monto is None or monto <= 0:
                continue
            codigo = fuentes_efectivas.get(campo_monto)
            fuente = fuentes_por_codigo.get(codigo) if codigo else None
            if fuente is None:
                raise ValidationError(
                    f'La fuente de financiamiento "{codigo or "-"}" del campo '
                    f'{campo_monto} no existe en los catálogos de la gestión '
                    f'{gestion.anio}.'
                )
            por_fuente[fuente] = por_fuente.get(fuente, Decimal('0.00')) + monto
        for fuente, monto in por_fuente.items():
            AllocationSource.objects.create(
                allocation=allocation,
                fuente=fuente,
                monto=monto,
                created_by=usuario,
                updated_by=usuario,
            )
            total_montos += monto
        creadas += 1

    importacion.estado = EstadoImportacion.APLICADO
    importacion.save(update_fields=['estado', 'updated_at'])
    registrar_evento(
        usuario,
        EventoAuditoria.Accion.CREAR,
        'BudgetImport',
        importacion.id,
        resumen=(
            f'Importación "{importacion.filename}" aplicada: {creadas} '
            f'aperturas BORRADOR (gestión {gestion.anio})'
        ),
        datos_posteriores={
            'aperturas_creadas': creadas,
            'total_importado': str(total_montos),
            'perfil': importacion.perfil,
        },
        gestion=gestion.anio,
    )
    return {
        'aperturas_creadas': creadas,
        'total_importado': total_montos,
        'estado': importacion.estado,
    }
