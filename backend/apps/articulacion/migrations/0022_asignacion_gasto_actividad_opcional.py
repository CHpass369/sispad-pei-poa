import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """La asignación de gasto ya no exige una actividad del POAU.

    La programación de recursos cuelga de la operación: la actividad pasa a ser
    un detalle opcional. Es una relajación de la restricción, así que las filas
    existentes conservan su actividad y no hace falta poblar nada.
    """

    dependencies = [
        ('articulacion', '0021_programacion_fisica_campos_matriz'),
    ]

    operations = [
        migrations.AlterField(
            model_name='asignacionobjetogasto',
            name='actividad',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='asignaciones_og',
                to='articulacion.actividadpoau',
                verbose_name='Actividad',
            ),
        ),
    ]
