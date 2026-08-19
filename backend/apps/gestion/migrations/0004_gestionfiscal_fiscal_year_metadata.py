from django.db import migrations, models

import apps.gestion.models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0003_crear_gestiones_seed'),
    ]

    operations = [
        migrations.AddField(
            model_name='gestionfiscal',
            name='documento_habilitacion',
            field=models.FileField(
                blank=True,
                null=True,
                upload_to=apps.gestion.models.gestion_fiscal_documento_upload_to,
            ),
        ),
        migrations.AddField(
            model_name='gestionfiscal',
            name='fecha_cierre_programada',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='gestionfiscal',
            name='fecha_inicio',
            field=models.DateField(blank=True, null=True),
        ),
    ]
