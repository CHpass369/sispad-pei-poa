"""El rango es el PROGRAMA y el código de tres dígitos es el SUBPROGRAMA.

La migración 0020 invirtió la jerarquía: tomó el código de tres dígitos como
programa y movió el rango a un catálogo aparte. Es al revés.

    170-179                   INFRAESTRUCTURA URBANA Y RURAL          PROGRAMA
      170                     ... - INFRAESTRUCTURAS MUNICIPALES      SUBPROGRAMA
        170 0 001             MANTENIMIENTO Y MEJORAMIENTO ...        ACTIVIDAD
      171                     ... - VIAS URBANAS                      SUBPROGRAMA
        171 13120104700000 000  CONST. PAVIMENTO ZONA SUDESTE D1      PROYECTO

El nombre propio de cada subprograma ya vivía en las filas `<n> 0`, así que
alcanza con renombrarlas: la actividad y el proyecto siguen colgando de la
misma fila y no se toca su relación.
"""
from django.db import migrations

NIVEL_MUNICIPAL = 'MUNICIPAL'


def _codigo(rango):
    """El modelo histórico no trae las @property del modelo vivo."""
    return (str(rango.desde) if rango.desde == rango.hasta
            else f'{rango.desde}-{rango.hasta}')


def _rango_de(rangos, numero):
    """El rango que agrupa al subprograma: el más amplio que lo contiene.

    La directriz singulariza algún programa dentro de un rango —el 251 dentro
    de 250-259— para darle su propia finalidad y su propio sector. Eso califica
    al subprograma, no crea un nivel: si se tomara el más específico, el
    programa y el subprograma 251 compartirían código.
    """
    candidatos = [r for r in rangos if r.desde <= numero <= r.hasta]
    return max(candidatos, key=lambda r: r.hasta - r.desde) if candidatos else None


def enderezar(apps, schema_editor):
    Categoria = apps.get_model('budget', 'CategoriaProgramaticaTecho')
    Rango = apps.get_model('budget', 'RangoProgramaDirectriz')

    for gestion_id in set(Categoria.objects.values_list('gestion_id', flat=True)):
        subprogramas = list(Categoria.objects.filter(
            gestion_id=gestion_id, nivel='SUBPROGRAMA'))
        if not subprogramas:
            continue
        gestion = Categoria.objects.filter(gestion_id=gestion_id).first().gestion
        anio = getattr(gestion, 'anio', None)
        rangos = list(Rango.objects.filter(gestion=anio,
                                           nivel_entidad=NIVEL_MUNICIPAL)) \
            if anio else []

        # 1. Se desengancha el subprograma antes de tocar los PROGRAMA: si se
        #    borra un programa con hijos, la cascada llega a las actividades y
        #    ahí las aperturas las protegen.
        for subprograma in subprogramas:
            subprograma.parent = None
            subprograma.save(update_fields=['parent'])

        # 2. Los PROGRAMA que quedaron mal dejan lugar: los de tres dígitos que
        #    creó 0020 y los rangos viejos, escritos con espaciado irregular.
        #    Ya no tienen hijos, así que la baja es limpia.
        Categoria.objects.filter(gestion_id=gestion_id, nivel='PROGRAMA').delete()

        # 3. El subprograma pasa a ser el código de tres dígitos, conservando
        #    su denominación propia.
        por_numero = {}
        for subprograma in subprogramas:
            crudo = subprograma.codigo.split(' ')[0]
            if not crudo.isdigit():
                continue
            subprograma.codigo = crudo
            subprograma.save(update_fields=['codigo'])
            por_numero[int(crudo)] = subprograma

        # 4. El programa es el rango, y de él cuelgan sus subprogramas.
        programas = {}
        for numero, subprograma in sorted(por_numero.items()):
            rango = _rango_de(rangos, numero)
            if rango is None:
                continue
            codigo = _codigo(rango)
            if codigo not in programas:
                programas[codigo] = Categoria.objects.create(
                    gestion_id=gestion_id, codigo=codigo,
                    nivel='PROGRAMA', denominacion=rango.denominacion[:300],
                    rango_directriz=rango,
                )
            subprograma.parent = programas[codigo]
            subprograma.save(update_fields=['parent'])


class Migration(migrations.Migration):

    dependencies = [('budget', '0021_denominacion_normativa')]

    # Sin reversa: 0020 ya había perdido la forma original y devolverla seria
    # reconstruir de memoria una jerarquia que era incorrecta.
    operations = [migrations.RunPython(enderezar, migrations.RunPython.noop)]
