from django.db import migrations, models


CONSTRAINT_NUEVO = r"""
ALTER TABLE catalogos_versionclasificador
DROP CONSTRAINT clasificador_vigente_fuente_oficial;
ALTER TABLE catalogos_versionclasificador
ADD CONSTRAINT clasificador_vigente_fuente_oficial
CHECK (
    ((NOT vigente) AND clasificacion_fuente <> 'oficial')
    OR (
        clasificacion_fuente = 'oficial'
        AND norma ~ '.*\S.*'
        AND fecha_norma IS NOT NULL
        AND codigo_fuente ~ '.*\S.*'
        AND procedencia_normativa ~ '.*\S.*'
        AND hash_fuente ~ '^[0-9a-f]{64}$'
    )
) NOT VALID;
"""


CONSTRAINT_ANTERIOR = r"""
ALTER TABLE catalogos_versionclasificador
DROP CONSTRAINT clasificador_vigente_fuente_oficial;
ALTER TABLE catalogos_versionclasificador
ADD CONSTRAINT clasificador_vigente_fuente_oficial
CHECK (
    (NOT vigente)
    OR (
        clasificacion_fuente = 'oficial'
        AND norma <> ''
        AND fecha_norma IS NOT NULL
        AND codigo_fuente <> ''
        AND procedencia_normativa <> ''
        AND hash_fuente <> ''
    )
) NOT VALID;
"""


class Migration(migrations.Migration):
    dependencies = [
        ('catalogos', '0003_seed_clasificadores_oficiales_2026'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(CONSTRAINT_NUEVO, CONSTRAINT_ANTERIOR),
            ],
            state_operations=[
                migrations.RemoveConstraint(
                    model_name='versionclasificador',
                    name='clasificador_vigente_fuente_oficial',
                ),
                migrations.AddConstraint(
                    model_name='versionclasificador',
                    constraint=models.CheckConstraint(
                        condition=(
                            (
                                models.Q(vigente=False)
                                & ~models.Q(clasificacion_fuente='oficial')
                            )
                            | (
                                models.Q(clasificacion_fuente='oficial')
                                & models.Q(norma__regex=r'.*\S.*')
                                & models.Q(fecha_norma__isnull=False)
                                & models.Q(codigo_fuente__regex=r'.*\S.*')
                                & models.Q(procedencia_normativa__regex=r'.*\S.*')
                                & models.Q(hash_fuente__regex=r'^[0-9a-f]{64}$')
                            )
                        ),
                        name='clasificador_vigente_fuente_oficial',
                    ),
                ),
            ],
        ),
    ]
