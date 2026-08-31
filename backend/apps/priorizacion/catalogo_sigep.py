"""Lectura de los reportes del SIGEP que alimentan el catálogo maestro.

Hay dos formatos y no se parecen en nada:

**Plano** — una fila por proyecto, cabecera en la fila 1 con las columnas
`SISIN`, `Descripcion SISIN` y `Cat. Prg.`.

**Jerárquico** (el reporte de ejecución por objeto de gasto) — no tiene columna
de proyecto. La categoría programática aparece como encabezado de bloque:

    Entidad 1312 → DA → UE → Cat. Prg. → FTE → Org. → filas de gasto

La etiqueta del bloque va en la columna 2, el código en la 5 y el nombre en la
10; las filas de gasto usan otras columnas. Buscar una cabecera plana en este
formato no encuentra nada y el archivo se omite en silencio, que es justo lo
que pasaba antes de que existiera este módulo.

El código de categoría trae el SISIN embebido —`171 13120123400000 000` es
`<programa> <sisin> <actividad>`— así que de acá sale todo lo que el catálogo
necesita sin cruzar contra ninguna otra planilla.
"""
import re

__all__ = ['ETIQUETA_CATEGORIA', 'PROGRAMAS_SIN_PROYECTO', 'Categoria',
           'parsear_categoria', 'es_obra', 'distrito_de', 'leer_ejecucion',
           'leer_plano']

# Posición de las tres celdas que forman un encabezado de bloque.
COL_ETIQUETA, COL_CODIGO, COL_NOMBRE = 2, 5, 10

ETIQUETA_CATEGORIA = 'Cat. Prg.'

# `000` es funcionamiento y `099` son las partidas no asignables a programas:
# no son proyectos y no tienen por qué aparecer en el buscador del acta.
PROGRAMAS_SIN_PROYECTO = frozenset({'000', '099'})

# `<programa> <sisin|0> <actividad>`. El segmento del medio es `0` cuando la
# categoría no cuelga de un proyecto de inversión con código SISIN.
_RE_CATEGORIA = re.compile(r'^(\d{3})\s+([0-9A-Z]{1,14})\s+(\d{3})$')

# Verbos con los que empiezan los nombres de obra. Lo que no arranca así es
# funcionamiento, servicio o transferencia: tiene categoría programática, pero
# ninguna OTB lo prioriza.
_RE_OBRA = re.compile(
    r'^(CONST|CONSTRUCCION|MEJ|MEJORAMIENTO|AMPL|AMPLIACION|IMPLEM'
    r'|IMPLEMENTACION|EQUIP|EQUIPAMIENTO|ADQ|ADQUISICION|MANTENIMIENTO'
    r'|MANTENIMINTO|REFACCION|REPOSICION|ENLOSETADO|PAVIMENTO|APERTURA'
    r'|CIERRE|EMBOVEDADO|CANALIZACION|ELECTRIFICACION|PERFORACION|ESTUDIO'
    r'|SUPERVISION)\b', re.IGNORECASE)

# El distrito escrito en el nombre. Se corta el sufijo `(OTB ...)` antes de
# buscarlo: adentro del paréntesis puede ir otro número que no es el distrito.
_RE_DISTRITO = re.compile(r'DISTRITO\s+([A-ZÑÁÉÍÓÚ0-9]+(?:\s+[A-ZÑ]+)?)')


class Categoria:
    """Una categoría programática leída de un reporte."""

    __slots__ = ('codigo', 'nombre', 'programa', 'sisin', 'actividad',
                 'unidad_ejecutora')

    def __init__(self, codigo, nombre, programa, sisin, actividad,
                 unidad_ejecutora=''):
        self.codigo = codigo
        self.nombre = nombre
        self.programa = programa
        self.sisin = sisin
        self.actividad = actividad
        self.unidad_ejecutora = unidad_ejecutora

    @property
    def es_proyecto(self):
        return self.programa not in PROGRAMAS_SIN_PROYECTO

    @property
    def es_obra(self):
        return es_obra(self.nombre)

    def __repr__(self):
        return f'<Categoria {self.codigo} {self.nombre[:40]!r}>'


def parsear_categoria(codigo, nombre='', unidad_ejecutora=''):
    """Parte `171 13120123400000 000` en sus tres segmentos.

    Devuelve `None` si el código no tiene la forma esperada, que es lo que pasa
    con las filas de totales y con los pocos códigos de arrastre del sistema
    viejo que el SIGEP no migró.
    """
    m = _RE_CATEGORIA.match(' '.join(str(codigo or '').split()))
    if not m:
        return None
    programa, medio, actividad = m.groups()
    return Categoria(
        codigo=f'{programa} {medio} {actividad}',
        nombre=' '.join(str(nombre or '').split()),
        programa=programa,
        # `0` no es un SISIN: marca que la categoría no cuelga de un proyecto
        # de inversión.
        sisin='' if medio == '0' else medio,
        actividad=actividad,
        unidad_ejecutora=' '.join(str(unidad_ejecutora or '').split()),
    )


def es_obra(nombre):
    """¿El nombre corresponde a una obra que una OTB podría priorizar?"""
    return bool(_RE_OBRA.match(str(nombre or '').strip()))


def distrito_de(nombre):
    """El distrito escrito en el nombre, o cadena vacía si no lo declara.

    `... DISTRITO 4 (OTB ESMERALDA NORTE)` devuelve `4`, no `ESMERALDA`.
    """
    sin_sufijo = re.sub(r'\s*\(.*$', '', str(nombre or '').upper())
    m = _RE_DISTRITO.search(sin_sufijo)
    return m.group(1).strip() if m else ''


def leer_ejecucion(hoja):
    """Recorre un reporte jerárquico y devuelve sus categorías programáticas.

    Se queda con la última UE vista para poder atribuir cada categoría a su
    unidad ejecutora, que es dato de contexto útil al revisar el catálogo.
    """
    unidad = ''
    categorias = []
    for fila in range(hoja.nrows):
        etiqueta = str(hoja.cell_value(fila, COL_ETIQUETA)).strip()
        if etiqueta == 'UE':
            unidad = ' '.join(str(hoja.cell_value(fila, COL_NOMBRE)).split())
        elif etiqueta == ETIQUETA_CATEGORIA:
            cat = parsear_categoria(
                hoja.cell_value(fila, COL_CODIGO),
                hoja.cell_value(fila, COL_NOMBRE),
                unidad,
            )
            if cat and cat.nombre:
                categorias.append(cat)
    return categorias


def leer_plano(hoja):
    """Recorre un reporte plano y devuelve sus categorías programáticas.

    El SIGEP repite la cabecera cada 63 filas por los saltos de página: sin
    descartarla se cuela como un proyecto llamado `Descripcion SISIN`.
    """
    cabecera = [str(hoja.cell_value(1, c)).strip() for c in range(hoja.ncols)]
    try:
        i_sisin = cabecera.index('SISIN')
        i_desc = cabecera.index('Descripcion SISIN')
        i_cat = cabecera.index(ETIQUETA_CATEGORIA)
    except ValueError:
        return None

    rotulos = {cabecera[i_sisin], cabecera[i_desc]}
    categorias = []
    for fila in range(2, hoja.nrows):
        sisin = str(hoja.cell_value(fila, i_sisin)).strip()
        nombre = ' '.join(str(hoja.cell_value(fila, i_desc)).split())
        if not sisin or not nombre or sisin in rotulos or nombre in rotulos:
            continue
        cat = parsear_categoria(hoja.cell_value(fila, i_cat), nombre)
        if cat is None:
            # Sin categoría legible no hay fila de catálogo, pero el SISIN y el
            # nombre siguen siendo buenos: se arma la categoría a mano.
            cat = Categoria(codigo='', nombre=nombre, programa='',
                            sisin=sisin, actividad='')
        else:
            cat.sisin = cat.sisin or sisin
        categorias.append(cat)
    return categorias
