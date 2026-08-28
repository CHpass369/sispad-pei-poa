"""Repair stale physical NOT NULL left behind by an edited recorded 0013."""

from copy import copy

from django.db import migrations


def repair_fiscal_year_nullability(apps, schema_editor):
    Alcance = apps.get_model('accounts', 'AlcanceOrganizacional')
    nullable_field = Alcance._meta.get_field('fiscal_year')
    table = Alcance._meta.db_table
    column = nullable_field.column
    connection = schema_editor.connection

    with connection.cursor() as cursor:
        if table not in connection.introspection.table_names(cursor):
            raise RuntimeError(f'Missing required table: {table}.')
        columns = {
            description.name: description
            for description in connection.introspection.get_table_description(
                cursor, table,
            )
        }
    if column not in columns:
        raise RuntimeError(f'Missing required column: {table}.{column}.')
    if columns[column].null_ok:
        return

    old_field = copy(nullable_field)
    old_field.null = False
    schema_editor.alter_field(
        Alcance, old_field, nullable_field, strict=True,
    )


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0013_poau_scope_backfill'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(
                    repair_fiscal_year_nullability,
                    migrations.RunPython.noop,
                ),
            ],
            state_operations=[],
        ),
    ]
