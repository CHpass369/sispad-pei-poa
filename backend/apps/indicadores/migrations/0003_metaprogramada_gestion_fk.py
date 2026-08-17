# PIP-DB-004: indicadores.MetaProgramada.gestion (año int) → FK GestionFiscal.
# Tabla vacía: Add→Remove→Rename→Alter (sin RunPython).

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0002_alter_gestionfiscal_estado'),
        ('indicadores', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='metaprogramada',
            name='gestion_fk',
            field=models.ForeignKey(db_column='gestion_fk', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión fiscal'),
        ),
        migrations.RemoveField(
            model_name='metaprogramada',
            name='gestion',
        ),
        migrations.RenameField(
            model_name='metaprogramada',
            old_name='gestion_fk',
            new_name='gestion',
        ),
        migrations.AlterField(
            model_name='metaprogramada',
            name='gestion',
            field=models.ForeignKey(db_column='gestion', on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión fiscal'),
        ),
    ]