"""Elimina los índices declarados que duplican al índice automático de la FK.

Django ya crea un índice por cada `ForeignKey` (`db_index=True` es el valor por
omisión). Además de eso, estos modelos declaraban a mano un
`models.Index(fields=['<fk>'])` sobre la misma columna sola: dos índices
idénticos, y cada `INSERT` pagando los dos.

Medido antes del cambio: 10 pares exactos (misma tabla, mismas columnas,
misma unicidad), sobre un total de 980 índices que pesaban 15 MB contra 14 MB
de datos.

Se quita la **declaración** en lugar de dropear el índice automático por SQL,
que fue el camino de `presupuesto/0006_limpiar_indices_redundantes`. El motivo
es la durabilidad: el índice automático no está en el estado de migraciones de
Django, así que cualquier `AlterField` futuro sobre la FK lo vuelve a crear y
el duplicado reaparece. Quitando la declaración, el estado queda consistente y
el índice que sobrevive es el que Django administra.

Ningún plan de consulta cambia: el índice que queda cubre exactamente la misma
columna. La reversa la genera Django sola (`AddIndex`).
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('articulacion', '0014_circuito_revision_poau'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='accionpoa',
            name='articulacio_product_a44bcb_idx',
        ),
        migrations.RemoveIndex(
            model_name='actividadpoau',
            name='articulacio_operaci_a73b8e_idx',
        ),
        migrations.RemoveIndex(
            model_name='operacionpoau',
            name='articulacio_accion__2d2b2d_idx',
        ),
        migrations.RemoveIndex(
            model_name='productopad',
            name='articulacio_resulta_8b277b_idx',
        ),
        migrations.RemoveIndex(
            model_name='productopei',
            name='articulacio_resulta_b15980_idx',
        ),
        migrations.RemoveIndex(
            model_name='seguimientopresupuesto',
            name='articulacio_accion__d4f580_idx',
        ),
        migrations.RemoveIndex(
            model_name='tareapoau',
            name='articulacio_activid_8bb1e7_idx',
        ),
    ]
