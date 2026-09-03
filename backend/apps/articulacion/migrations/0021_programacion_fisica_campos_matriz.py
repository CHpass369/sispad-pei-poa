from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('articulacion', '0020_tareapoau_campos_version_importacion'),
    ]

    operations = [
        migrations.AddField(
            model_name='operacionpoau',
            name='linea_base',
            field=models.DecimalField(
                blank=True, decimal_places=4, max_digits=20, null=True,
                verbose_name='Línea base',
            ),
        ),
        migrations.AddField(
            model_name='operacionpoau',
            name='meta_actual',
            field=models.DecimalField(
                blank=True, decimal_places=4, max_digits=20, null=True,
                verbose_name='Meta actual',
            ),
        ),
        migrations.AddField(
            model_name='operacionpoau',
            name='ponderacion',
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=5, null=True,
                verbose_name='Ponderación',
            ),
        ),
        migrations.AddField(
            model_name='actividadpoau',
            name='linea_base',
            field=models.DecimalField(
                blank=True, decimal_places=4, max_digits=20, null=True,
                verbose_name='Línea base',
            ),
        ),
        migrations.AddField(
            model_name='actividadpoau',
            name='meta_actual',
            field=models.DecimalField(
                blank=True, decimal_places=4, max_digits=20, null=True,
                verbose_name='Meta actual',
            ),
        ),
        migrations.AddField(
            model_name='actividadpoau',
            name='ponderacion',
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=5, null=True,
                verbose_name='Ponderación',
            ),
        ),
        migrations.AddField(
            model_name='tareapoau',
            name='linea_base',
            field=models.DecimalField(
                blank=True, decimal_places=4, max_digits=20, null=True,
                verbose_name='Línea base',
            ),
        ),
        migrations.AddField(
            model_name='tareapoau',
            name='meta_actual',
            field=models.DecimalField(
                blank=True, decimal_places=4, max_digits=20, null=True,
                verbose_name='Meta actual',
            ),
        ),
        migrations.AddField(
            model_name='tareapoau',
            name='ponderacion',
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=5, null=True,
                verbose_name='Ponderación',
            ),
        ),
    ]
