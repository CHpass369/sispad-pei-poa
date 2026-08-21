"""El nivel PROGRAMA toma la denominación que fija la directriz.

Los cuatro programas que ya existían antes de la reestructuración conservaban
el nombre cargado por la entidad, sin tildes y con variantes propias
—«SERVICIOS DE FAENEADO» donde la norma dice «SERVICIO DE FAENADO»—. El nombre
del programa es normativo; el propio de la entidad se conserva en el
subprograma, que es donde tiene sentido.
"""
from django.db import migrations


def normalizar(apps, schema_editor):
    Categoria = apps.get_model('budget', 'CategoriaProgramaticaTecho')
    for programa in Categoria.objects.filter(
            nivel='PROGRAMA', rango_directriz__isnull=False
    ).select_related('rango_directriz'):
        normativa = programa.rango_directriz.denominacion[:300]
        if programa.denominacion != normativa:
            programa.denominacion = normativa
            programa.save(update_fields=['denominacion'])


class Migration(migrations.Migration):

    dependencies = [('budget', '0020_programa_real')]

    # Sin reversa: no se guardó el nombre anterior y reconstruirlo a mano
    # sería inventarlo.
    operations = [migrations.RunPython(normalizar, migrations.RunPython.noop)]
