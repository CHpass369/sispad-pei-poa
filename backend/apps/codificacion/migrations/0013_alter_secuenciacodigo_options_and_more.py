# PIP-DB-003: codificacion — gestion (año int) → FK GestionFiscal en
# SecuenciaCodigo, HomologacionCodigo y EjecucionMigracionSIM (tablas vacías).
# VersionCatalogoPlan NO se FK-iza (excepción plurianual: año de vigencia del plan).

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0002_alter_gestionfiscal_estado'),
        ('codificacion', '0012_componentepdesa_objetivo_efecto_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='secuenciacodigo',
            options={'ordering': ['nivel', 'gestion__anio'], 'verbose_name': 'Secuencia de código', 'verbose_name_plural': 'Secuencias de códigos'},
        ),
        migrations.AddField(
            model_name='ejecucionmigracionsim',
            name='gestion_fk',
            field=models.ForeignKey(db_column='gestion_fk', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión fiscal'),
        ),
        migrations.AddField(
            model_name='homologacioncodigo',
            name='gestion_fk',
            field=models.ForeignKey(db_column='gestion_fk', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión fiscal'),
        ),
        migrations.AddField(
            model_name='secuenciacodigo',
            name='gestion_fk',
            field=models.ForeignKey(db_column='gestion_fk', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión fiscal'),
        ),
        migrations.RemoveField(model_name='ejecucionmigracionsim', name='gestion'),
        migrations.RemoveField(model_name='homologacioncodigo', name='gestion'),
        migrations.RemoveField(model_name='secuenciacodigo', name='gestion'),
        migrations.RenameField(model_name='ejecucionmigracionsim', old_name='gestion_fk', new_name='gestion'),
        migrations.RenameField(model_name='homologacioncodigo', old_name='gestion_fk', new_name='gestion'),
        migrations.RenameField(model_name='secuenciacodigo', old_name='gestion_fk', new_name='gestion'),
        migrations.AlterField(
            model_name='ejecucionmigracionsim',
            name='gestion',
            field=models.ForeignKey(db_column='gestion', on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión fiscal'),
        ),
        migrations.AlterField(
            model_name='homologacioncodigo',
            name='gestion',
            field=models.ForeignKey(db_column='gestion', on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión fiscal'),
        ),
        migrations.AlterField(
            model_name='secuenciacodigo',
            name='gestion',
            field=models.ForeignKey(db_column='gestion', on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión fiscal'),
        ),
    ]