"""Migración de datos: renombra values de PerfilImportacion (SISPOA_GASTOS_* → PIP_GASTOS_*)."""
from django.db import migrations


def renombrar_perfiles(apps, schema_editor):
    BudgetImport = apps.get_model('budget', 'BudgetImport')
    BudgetImport.objects.filter(perfil='SISPOA_GASTOS_HISTORICO').update(perfil='PIP_GASTOS_HISTORICO')
    BudgetImport.objects.filter(perfil='SISPOA_GASTOS_ACTUAL').update(perfil='PIP_GASTOS_ACTUAL')


def revertir_perfiles(apps, schema_editor):
    BudgetImport = apps.get_model('budget', 'BudgetImport')
    BudgetImport.objects.filter(perfil='PIP_GASTOS_HISTORICO').update(perfil='SISPOA_GASTOS_HISTORICO')
    BudgetImport.objects.filter(perfil='PIP_GASTOS_ACTUAL').update(perfil='SISPOA_GASTOS_ACTUAL')


class Migration(migrations.Migration):
    dependencies = [
        ('budget', '0010_remove_expenseobjectallocation_presupuesto_allocat_c5ae8a_idx'),
    ]

    operations = [
        migrations.RunPython(renombrar_perfiles, revertir_perfiles),
    ]
