"""El código de subprograma deja de ser `<programa>.SP`.

`.SP` era un invento del importador: no existe en el clasificador y al ordenar
por código se intercala mal —`000`, `000 0 001`, `000.SP`, `001`—, de modo que
la lista no sale secuencial por categoría programática.

En el clasificador el subprograma es el segmento del medio, el mismo lugar donde
un proyecto lleva su SISIN y una actividad de funcionamiento lleva un 0. Con
`<programa> 0` la secuencia queda `000`, `000 0`, `000 0 001`, `001`, …
"""
from django.db import migrations


def quitar_sp(apps, schema_editor):
    Categoria = apps.get_model('budget', 'CategoriaProgramaticaTecho')
    for categoria in Categoria.objects.filter(codigo__endswith='.SP'):
        categoria.codigo = f"{categoria.codigo[:-3].strip()} 0"
        categoria.save(update_fields=['codigo'])


def devolver_sp(apps, schema_editor):
    Categoria = apps.get_model('budget', 'CategoriaProgramaticaTecho')
    for categoria in Categoria.objects.filter(nivel='SUBPROGRAMA',
                                              codigo__endswith=' 0'):
        categoria.codigo = f"{categoria.codigo[:-2].strip()}.SP"
        categoria.save(update_fields=['codigo'])


class Migration(migrations.Migration):

    dependencies = [('budget', '0016_categoria_codigo_largo')]

    operations = [migrations.RunPython(quitar_sp, devolver_sp)]
