"""Elimina índice redundante en AsignacionPresupuestariaUnidad.

El índice FK automático ``presupuesto_asignacionpres_categoria_programatica_id_e27958f4``
duplica al índice declarado ``presupuesto_categor_3e54f5_idx`` sobre la misma
columna. Documentado en docs/auditoria_postgres.md §2.

Nota: se usa RunSQL (DROP INDEX) en lugar de RemoveIndex porque es un
índice FK automático que no forma parte del estado de migraciones de
Django (RemoveIndex fallaría con "No index named ... on model").
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('presupuesto', '0005_renombrar_catalogos_en_funciones_trigger'),
    ]

    operations = [
        migrations.RunSQL(
            sql='DROP INDEX IF EXISTS presupuesto_asignacionpres_categoria_programatica_id_e27958f4;',
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
