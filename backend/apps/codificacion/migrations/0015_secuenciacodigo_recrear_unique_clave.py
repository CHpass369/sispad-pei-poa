# PIP-DB-003: la migración 0013 (gestion int → FK GestionFiscal) eliminó la
# constraint única `uniq_secuencia_codigo_clave` al remover la columna
# `gestion` (PostgreSQL descarta constraints que referencian la columna
# borrada) y no la recreó. El modelo la declara (Meta.constraints); se
# restaura para preservar la unicidad (nivel, padre, gestión, entidad).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('codificacion', '0014_alter_versioncatalogoplan_gestion'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='secuenciacodigo',
            constraint=models.UniqueConstraint(
                fields=('nivel', 'padre_id', 'gestion', 'entidad'),
                name='uniq_secuencia_codigo_clave',
                nulls_distinct=False,
            ),
        ),
    ]
