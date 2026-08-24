"""El blindaje de fuente oficial pasa de `NOT VALID` a verificado.

`0004_blindaje_fuente_oficial` creó el CHECK como `NOT VALID` a propósito: así la
regla se aplica a las filas nuevas sin que la migración reviente con las que ya
estaban. La contra es que PostgreSQL nunca revisó las existentes, y una
restricción sin validar no garantiza nada sobre ellas.

Con los clasificadores de la gestión 2027 cargados (RM MEFP N° 271 de
31/07/2026), las siete versiones marcadas oficiales llevan su norma, su fecha,
su código de fuente, su procedencia y el sha256 del PDF. Ya no queda ninguna
fila que incumpla, así que se puede validar.

`VALIDATE CONSTRAINT` recorre la tabla y falla si encuentra una violación: si
esta migración pasa, la regla quedó probada sobre todo lo que hay, no solo
sobre lo que venga. No mueve un solo dato ni cambia el esquema —solo marca la
restricción como verificada—, por eso no hay `state_operations`.

No tiene reversa real: PostgreSQL no sabe "desvalidar" una restricción. Volver
atrás es un no-op, y `0004` sigue siendo quien la crea y la borra.

El nombre de la tabla se resuelve del modelo histórico y no se escribe a mano:
`0004` decía `catalogos_versionclasificador`, que después se renombró a
`catalogo_version_clasificador`.
"""
from django.db import migrations

CONSTRAINT = 'clasificador_vigente_fuente_oficial'


def validar(apps, schema_editor):
    modelo = apps.get_model('catalogos', 'VersionClasificador')
    tabla = modelo._meta.db_table
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            f'ALTER TABLE "{tabla}" VALIDATE CONSTRAINT "{CONSTRAINT}";'
        )


class Migration(migrations.Migration):
    dependencies = [
        ('catalogos', '0009_clasificadorinstitucional_version_clasificador_and_more'),
    ]

    operations = [
        migrations.RunPython(validar, migrations.RunPython.noop),
    ]
