# F3a: campo `estado` en Usuario para el ciclo de vida del registro público
# (PENDIENTE/ACTIVO/INACTIVO). Convive con el booleano legacy `activo`.
#
# Alineación de datos existentes: los usuarios con activo=False migran a
# estado=INACTIVO. Sin este paso quedarían con estado ACTIVO pese a conservar
# activo=False hasta su siguiente escritura mediante el modelo.
# Determinista: deriva solo del propio campo `activo`, sin datos externos.
from django.db import migrations, models


def alinear_estado_con_activo(apps, schema_editor):
    Usuario = apps.get_model('accounts', 'Usuario')
    Usuario.objects.filter(activo=False).update(estado='INACTIVO')


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0011_unir_candado_y_scope'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='estado',
            field=models.CharField(
                choices=[
                    ('PENDIENTE', 'Pendiente de aprobación'),
                    ('ACTIVO', 'Activo'),
                    ('INACTIVO', 'Inactivo'),
                ],
                default='ACTIVO',
                max_length=12,
            ),
        ),
        migrations.RunPython(alinear_estado_con_activo, migrations.RunPython.noop),
    ]
