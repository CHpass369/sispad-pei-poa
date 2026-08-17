# PIP-DB-008: gestion (año int) → FK GestionFiscal (UUID). Secuencia Add→Remove→Rename→Alter
# porque PostgreSQL no castea int→uuid en ALTER COLUMN TYPE (tabla vacía incluida).

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('acciones_correctivas', '0002_initial'),
        ('gestion', '0002_alter_gestionfiscal_estado'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='accioncorrectiva',
            options={'ordering': ['-gestion__anio', 'status', 'due_date'], 'verbose_name': 'Acción Correctiva', 'verbose_name_plural': 'Acciones Correctivas'},
        ),
        migrations.AddField(
            model_name='accioncorrectiva',
            name='gestion_fk',
            field=models.ForeignKey(blank=True, db_column='gestion_fk', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión'),
        ),
        migrations.RemoveField(
            model_name='accioncorrectiva',
            name='gestion',
        ),
        migrations.RenameField(
            model_name='accioncorrectiva',
            old_name='gestion_fk',
            new_name='gestion',
        ),
        migrations.AlterField(
            model_name='accioncorrectiva',
            name='gestion',
            field=models.ForeignKey(db_column='gestion', on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión'),
        ),
    ]

