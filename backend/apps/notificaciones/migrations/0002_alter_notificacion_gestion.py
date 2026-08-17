# PIP-DB-008: gestion (año int) → FK GestionFiscal (UUID). Secuencia Add→Remove→Rename→Alter
# porque PostgreSQL no castea int→uuid en ALTER COLUMN TYPE (tabla vacía incluida).

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notificaciones', '0001_initial'),
        ('gestion', '0002_alter_gestionfiscal_estado'),
    ]

    operations = [
        migrations.AddField(
            model_name='notificacion',
            name='gestion_fk',
            field=models.ForeignKey(blank=True, db_column='gestion_fk', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión fiscal'),
        ),
        migrations.RemoveField(
            model_name='notificacion',
            name='gestion',
        ),
        migrations.RenameField(
            model_name='notificacion',
            old_name='gestion_fk',
            new_name='gestion',
        ),
        migrations.AlterField(
            model_name='notificacion',
            name='gestion',
            field=models.ForeignKey(db_column='gestion', on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión fiscal'),
        ),
    ]

