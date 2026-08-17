# PIP-DB-004: evaluacion.Evaluacion.fiscal_year (año int) → gestion (FK a
# GestionFiscal). Tabla vacía: re-alinear Meta → Add → Remove → Rename →
# re-alinear Meta → Alter final.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0002_alter_gestionfiscal_estado'),
        ('evaluacion', '0003_alter_evaluacion_plan'),
    ]

    operations = [
        # AddField primero (los Alter* con gestion_fk requieren el campo vivo).
        migrations.AddField(
            model_name='evaluacion',
            name='gestion_fk',
            field=models.ForeignKey(db_column='gestion_fk', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión'),
        ),
        migrations.AlterUniqueTogether(
            name='evaluacion',
            unique_together={('plan', 'gestion_fk', 'evaluation_type', 'period')},
        ),
        migrations.RemoveField(
            model_name='evaluacion',
            name='fiscal_year',
        ),
        migrations.RenameField(
            model_name='evaluacion',
            old_name='gestion_fk',
            new_name='gestion',
        ),
        # Estado final alineado con el modelo.
        migrations.AlterModelOptions(
            name='evaluacion',
            options={'ordering': ['-gestion__anio', 'evaluation_type'], 'verbose_name': 'Evaluación', 'verbose_name_plural': 'Evaluaciones'},
        ),
        migrations.AlterUniqueTogether(
            name='evaluacion',
            unique_together={('plan', 'gestion', 'evaluation_type', 'period')},
        ),
        migrations.AlterField(
            model_name='evaluacion',
            name='gestion',
            field=models.ForeignKey(db_column='gestion', on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión'),
        ),
    ]