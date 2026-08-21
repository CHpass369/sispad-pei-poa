"""El nivel PROGRAMA pasa a ser el programa real, no el rango.

Hasta acá las filas PROGRAMA guardaban el rango de la directriz —`170 - 179`—,
de modo que el programa que la entidad realmente usa (171) no existía como
registro y un proyecto tenía que colgarse del rango. Además los rangos venían
escritos de tres formas distintas (`100-109`, `130 - 139`, `190 -199`), lo que
rompía el orden.

El rango pasa a vivir en su propio catálogo normativo
(`RangoProgramaDirectriz`) y PROGRAMA queda con el código real de tres dígitos,
apuntando al rango que le corresponde. Las filas de rango quedan INACTIVA en
vez de borrarse: son catálogo, y antes de borrarlas conviene que alguien las mire.
"""
from django.db import migrations

NIVEL_MUNICIPAL = 'MUNICIPAL'


def _rango_de(rangos, numero):
    """El rango más específico que contiene al programa."""
    candidatos = [r for r in rangos if r.desde <= numero <= r.hasta]
    return min(candidatos, key=lambda r: r.hasta - r.desde) if candidatos else None


def programas_reales(apps, schema_editor):
    Categoria = apps.get_model('budget', 'CategoriaProgramaticaTecho')
    Rango = apps.get_model('budget', 'RangoProgramaDirectriz')

    for gestion_id in set(Categoria.objects.values_list('gestion_id', flat=True)):
        subprogramas = list(Categoria.objects.filter(
            gestion_id=gestion_id, nivel='SUBPROGRAMA'))
        if not subprogramas:
            continue
        anio = getattr(
            Categoria.objects.filter(gestion_id=gestion_id).first().gestion,
            'anio', None)
        rangos = list(Rango.objects.filter(gestion=anio,
                                           nivel_entidad=NIVEL_MUNICIPAL)) \
            if anio else []

        programas = {}
        for subprograma in subprogramas:
            crudo = subprograma.codigo.split(' ')[0]
            if not crudo.isdigit():
                continue
            codigo = f'{int(crudo):03d}'
            if codigo not in programas:
                rango = _rango_de(rangos, int(crudo))
                programa, _ = Categoria.objects.get_or_create(
                    gestion_id=gestion_id, codigo=codigo,
                    defaults={
                        'nivel': 'PROGRAMA',
                        # El nombre normativo; el propio de la entidad se
                        # conserva en el subprograma.
                        'denominacion': (rango.denominacion if rango
                                         else subprograma.denominacion)[:300],
                    },
                )
                if rango and programa.rango_directriz_id != rango.id:
                    programa.rango_directriz = rango
                    programa.nivel = 'PROGRAMA'
                    programa.save(update_fields=['rango_directriz', 'nivel'])
                programas[codigo] = programa
            subprograma.parent = programas[codigo]
            subprograma.save(update_fields=['parent'])

        # Las filas que guardaban un rango dejan de usarse.
        Categoria.objects.filter(
            gestion_id=gestion_id, nivel='PROGRAMA', codigo__contains='-'
        ).update(estado='INACTIVA')


def revertir(apps, schema_editor):
    """No se reconstruye la jerarquía anterior: se reactivan los rangos."""
    Categoria = apps.get_model('budget', 'CategoriaProgramaticaTecho')
    Categoria.objects.filter(nivel='PROGRAMA', codigo__contains='-').update(
        estado='ACTIVA')


class Migration(migrations.Migration):

    dependencies = [('budget', '0019_categoria_rango_directriz')]

    operations = [migrations.RunPython(programas_reales, revertir)]
