"""Nombres de modelo en español y el corte corriente/inversión del recurso.

Los `db_table` ya estaban en español desde el inicio ('presupuesto_techo_directivo',
'presupuesto_recurso_techo', …), asi que este renombrado NO toca la base: es
solo el nombre de la clase en Python. Los nombres nuevos salen de esos mismos
db_table, no son invención.

Dos se desambiguan con el dominio porque el nombre corto ya existe en otra app:
CategoriaProgramaticaTecho (hay una en `presupuesto`) y AsignacionObjetoGastoTecho
(hay una en `articulacion`).

`ImportError` pasa a `ImportacionError`: el nombre anterior sombreaba la
excepcion incorporada de Python.
"""
import django.db.models.deletion
from django.db import migrations, models


RENOMBRES = [
    ('DirectiveCeiling', 'TechoDirectivo'),
    ('DirectiveCeilingVersion', 'TechoVersion'),
    ('CeilingResource', 'RecursoTecho'),
    ('MandatoryExpense', 'GastoObligatorio'),
    ('BudgetDocument', 'DocumentoPresupuestario'),
    ('DistributionVersion', 'DistribucionVersion'),
    ('Allocation', 'Apertura'),
    ('AllocationSource', 'AperturaFuente'),
    ('Reserve', 'Reserva'),
    ('ProgrammaticCategory', 'CategoriaProgramaticaTecho'),
    ('BudgetImport', 'Importacion'),
    ('ImportDetalle', 'ImportacionDetalle'),
    ('TerritorialDistribution', 'DistribucionTerritorial'),
    ('TerritorialAllocation', 'AsignacionTerritorial'),
    ('ExpenseObjectAllocation', 'AsignacionObjetoGastoTecho'),
    ('ImportError', 'ImportacionError'),
    ('Reform', 'Reforma'),
    ('ReformMovement', 'ReformaMovimiento'),
]


class Migration(migrations.Migration):

    dependencies = [
        ('budget', '0012_alter_budgetimport_perfil'),
    ]

    operations = [
        *[migrations.RenameModel(old_name=v, new_name=n) for v, n in RENOMBRES],

        # El Presupuesto General de Recursos se presenta agrupado y con el
        # corte corriente/inversión al nivel del rubro agrupador.
        migrations.AddField(
            model_name='recursotecho',
            name='padre',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                related_name='componentes', to='budget.recursotecho',
                verbose_name='Rubro agrupador',
            ),
        ),
        migrations.AddField(
            model_name='recursotecho',
            name='orden',
            field=models.PositiveIntegerField(
                default=0, verbose_name='Orden de presentación'),
        ),
        migrations.AddField(
            model_name='recursotecho',
            name='monto_corriente',
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=18, null=True,
                verbose_name='Gastos corrientes (Bs)'),
        ),
        migrations.AddField(
            model_name='recursotecho',
            name='monto_inversion',
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=18, null=True,
                verbose_name='Gastos de inversión (Bs)'),
        ),
        migrations.AlterModelOptions(
            name='recursotecho',
            options={
                'ordering': ['version', 'orden', 'concepto'],
                'verbose_name': 'Recurso del techo',
                'verbose_name_plural': 'Recursos del techo',
            },
        ),
    ]
