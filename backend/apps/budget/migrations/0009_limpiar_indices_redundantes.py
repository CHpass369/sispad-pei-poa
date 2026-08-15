"""Elimina índices redundantes heredados del rename de tablas a español.

El rename (commit 9961550) dejó los índices FK automáticos con prefijo
``budget_*`` conviviendo con los nuevos ``presupuesto_*`` sobre la misma
columna. Documentado en docs/auditoria_postgres.md §2.

Nota: se usa RunSQL (DROP INDEX) en lugar de RemoveIndex porque estos
índices son creados automáticamente por PostgreSQL al crear las FK y no
forman parte del estado de migraciones de Django (RemoveIndex fallaría
con "No index named ... on model").

Excluido de esta limpieza: ``presupuesto_allocat_c5ae8a_idx`` (cubierto por
``uniq_allocation_objeto_gasto``) porque sigue declarado en el Meta de
``ExpenseObjectAllocation``; eliminarlo sin quitar la declaración del modelo
haría que Django lo recree en el próximo ``makemigrations``.
"""

from django.db import migrations

_INDICES = [
    'budget_territorialdistribution_gestion_id_8bcca733',
    'budget_budgetdocument_gestion_id_c28cf903',
    'budget_budgetimport_gestion_id_36e918d5',
    'budget_reform_gestion_id_e2cc3ea9',
]


class Migration(migrations.Migration):

    dependencies = [
        ('budget', '0008_rename_budget_allo_gestion_6281d0_idx_presupuesto_gestion_022f14_idx_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql=[f'DROP INDEX IF EXISTS {nombre};' for nombre in _INDICES],
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
