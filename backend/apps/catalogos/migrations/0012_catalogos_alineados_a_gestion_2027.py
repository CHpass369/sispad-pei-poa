"""Deja todos los catálogos con su edición de la gestión 2027.

Al comparar catálogo por catálogo aparecieron dos situaciones distintas, y cada
una pide un tratamiento distinto.

**1. Cinco catálogos etiquetados en 2026 que en realidad son de 2027.**

`unidad_medida` (13), `tipo_producto` (6), `tipo_proyecto` (5),
`tipo_financiamiento` (4) y `tipo_operacion` (2) colgaban de la gestión 2026,
pero su propio campo `fuente_normativa` dice:

    'RM N. 271/2026 - Clasificadores Presupuestarios Gestion 2027'

La RM 271 de 31/07/2026 es la norma que rige la gestión 2027 —es la misma con la
que se cargaron los demás clasificadores 2027—. Así que no falta cargarlos: están
mal etiquetados. Se corrige la gestión, no se duplica nada. En 2027 esas cinco
tablas tenían cero filas, así que el movimiento no puede chocar contra
`UNIQUE(codigo, gestion)`.

**2. El clasificador institucional de 2027 quedó incompleto.**

2026 tiene 568 entidades y 2027 sólo una. La carga oficial 2027 nunca se pudo
hacer: la columna COD. del PDF de la RM 271 viene en blanco para el grueso de las
entidades. Como la plataforma opera sobre la gestión 2027, se arrastra el juego
de 2026 —que es el más completo disponible— **sin borrar el de 2026** y dejando
constancia explícita en `fuente_normativa` de que es un arrastre y no una carga
oficial. El código 1312 ya existe en 2027 y no se toca.

Las copias arrastradas quedan **sin** `version_clasificador`: atarlas a la versión
2027 diría que provienen de la RM 271, y no es cierto. Que no tengan versión es
precisamente la señal de que falta la carga oficial.

**3. De paso, las 568 filas de 2026 se enlazan a su versión.**

La versión institucional de la gestión 2026 ya existe (RM MEFP N.º 249/2025) y
esas filas nunca quedaron enlazadas. Es un relleno probable y sin invención.

No se tocan los catálogos donde 2027 ya está completo (`objeto_gasto`,
`rubro_recurso`, `finalidad_funcion`, `organismo_financiador`,
`sector_economico`, `fuente_financiamiento`, `categoria_programatica`).
`entidad_transferencia` está vacío en las dos gestiones: no hay de dónde
completarlo.

La reversa deshace exactamente lo hecho: devuelve los cinco catálogos a 2026 y
borra sólo las filas arrastradas, que se reconocen por su marca.
"""
from django.db import migrations

MARCA_ARRASTRE = (
    'Arrastrado de la gestión 2026 — pendiente de carga oficial 2027'
)

CATALOGOS_MAL_ETIQUETADOS = [
    'UnidadMedida',
    'TipoProducto',
    'TipoProyecto',
    'TipoFinanciamiento',
    'TipoOperacion',
]


def _gestiones(apps):
    GestionFiscal = apps.get_model('gestion', 'GestionFiscal')
    return (
        GestionFiscal.objects.filter(anio=2026).first(),
        GestionFiscal.objects.filter(anio=2027).first(),
    )


def alinear(apps, schema_editor):
    g2026, g2027 = _gestiones(apps)
    if g2026 is None or g2027 is None:
        return

    for nombre in CATALOGOS_MAL_ETIQUETADOS:
        modelo = apps.get_model('catalogos', nombre)
        modelo.objects.filter(gestion=g2026).update(gestion=g2027)

    Institucional = apps.get_model('catalogos', 'ClasificadorInstitucional')
    ya_en_2027 = set(
        Institucional.objects.filter(gestion=g2027).values_list('codigo', flat=True)
    )
    # Se construyen instancias nuevas en lugar de mutar las cargadas: el default
    # del UUID se aplica en __init__, no en bulk_create, así que reutilizar la
    # fila con `pk = None` intentaría insertar un id nulo.
    copiables = [
        f.name for f in Institucional._meta.concrete_fields
        if f.name not in ('id', 'gestion', 'version_clasificador',
                          'fuente_normativa')
    ]
    arrastradas = [
        Institucional(
            gestion=g2027,
            version_clasificador=None,
            fuente_normativa=MARCA_ARRASTRE,
            **{nombre: getattr(fila, nombre) for nombre in copiables},
        )
        for fila in Institucional.objects.filter(gestion=g2026)
        if fila.codigo not in ya_en_2027
    ]
    Institucional.objects.bulk_create(arrastradas, batch_size=200)

    # Las 568 de 2026 se enlazan a la versión que ya existe para su gestión.
    Version = apps.get_model('catalogos', 'VersionClasificador')
    version_2026 = Version.objects.filter(
        tipo='institucional', gestion=g2026,
    ).first()
    if version_2026 is not None:
        Institucional.objects.filter(
            gestion=g2026, version_clasificador__isnull=True,
        ).update(version_clasificador=version_2026)


def revertir(apps, schema_editor):
    g2026, g2027 = _gestiones(apps)
    if g2026 is None or g2027 is None:
        return

    Institucional = apps.get_model('catalogos', 'ClasificadorInstitucional')
    Institucional.objects.filter(
        gestion=g2027, fuente_normativa=MARCA_ARRASTRE,
    ).delete()
    Institucional.objects.filter(
        gestion=g2026, fuente_normativa='',
    ).update(version_clasificador=None)

    for nombre in CATALOGOS_MAL_ETIQUETADOS:
        modelo = apps.get_model('catalogos', nombre)
        modelo.objects.filter(gestion=g2027).update(gestion=g2026)


class Migration(migrations.Migration):
    dependencies = [
        ('catalogos', '0011_heredar_clave_natural_de_catalogobase'),
        ('gestion', '0004_gestionfiscal_fiscal_year_metadata'),
    ]

    operations = [
        migrations.RunPython(alinear, revertir),
    ]
