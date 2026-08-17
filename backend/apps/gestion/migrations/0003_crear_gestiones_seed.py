# PIP-DB-003: materializa las GestionFiscal que las migraciones de seed
# referencian (catalogos.0003 siembra VersionClasificador 2026/2027 oficiales
# sin GestionFiscal; en producción la canónica las tiene).
#
# Corre TEMPRANO en el lote (antes de que otras apps creen FKs hacia
# gestion_gestionfiscal): los INSERTs en la tabla referenciada dentro de la
# misma transacción de creación de la test DB bloquean el rollback de
# constraints (PostgreSQL: pending trigger events).

from django.db import migrations

ANIOS_SEED = [2026, 2027]


def crear_gestiones_seed(apps, schema_editor):
    GestionFiscal = apps.get_model('gestion', 'GestionFiscal')
    for anio in ANIOS_SEED:
        GestionFiscal.objects.get_or_create(
            anio=anio, defaults={'estado': 'preparacion'},
        )


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0002_alter_gestionfiscal_estado'),
    ]

    operations = [
        migrations.RunPython(crear_gestiones_seed, migrations.RunPython.noop),
    ]