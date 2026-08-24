"""«S/N» no es una categoría programática: queda como vacío.

Una acción POA quedó con `categoria_programatica = 'S/N'`. La escribió el
importador de POAUs copiando tal cual lo que traía la planilla en la columna de
categoría: «S/N», sin número. No es un código y no va a serlo nunca.

Guardado así se comporta peor que un vacío, porque parece un valor: aparece en
los listados, no cae en ningún filtro de «sin asignar», y bloquea la conversión
de la columna en clave foránea —que es el destino de este campo— sin razón real.

Se pasa a cadena vacía, que es lo que el modelo ya usa para «sin asignar» y lo
que el propio campo declara con `blank=True`. La acción no se toca: conserva su
denominación, su unidad responsable y la operación que le cuelga; lo único que
cambia es que deja de afirmar una categoría que no tiene.

Tras esto quedan **cero** referencias a categorías inexistentes, después de que
`importar_catalogo_programatico_2027` completara el catálogo con las 236
categorías oficiales que le faltaban.

La reversa devuelve el literal, para que la migración sea simétrica aunque
restaurar el valor no tenga valor práctico.
"""
from django.db import migrations

SIN_NUMERO = 'S/N'


def vaciar(apps, schema_editor):
    AccionPOA = apps.get_model('articulacion', 'AccionPOA')
    AccionPOA.objects.filter(categoria_programatica=SIN_NUMERO).update(
        categoria_programatica='',
    )


def restaurar(apps, schema_editor):
    # No se puede distinguir esta fila de las que siempre estuvieron vacías,
    # así que la reversa es deliberadamente un no-op: deshacerla a ciegas
    # marcaría como «S/N» filas que nunca lo fueron.
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('articulacion', '0016_normalizar_meses_de_programacion_mensual'),
    ]

    operations = [
        migrations.RunPython(vaciar, restaurar),
    ]
