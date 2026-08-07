from datetime import date
from uuid import UUID

from django.db import migrations


HASH_CLASIFICADORES_2026 = (
    '9719fd35d33a4ce0278aef96a5599cb93aa4d9f148d45f57adf81730d5a90ccf'
)
NORMA = 'RM MEFP N.º 249/2025'
PROCEDENCIA = 'Clasificadores Presupuestarios Gestión 2026, RM 249, PDF pp. 3-4'
SEEDS_OFICIALES = (
    ('7b600000-0000-4000-8000-000000000001', 'institucional'),
    ('7b600000-0000-4000-8000-000000000002', 'objeto_gasto'),
    ('7b600000-0000-4000-8000-000000000003', 'fuente_financiamiento'),
    ('7b600000-0000-4000-8000-000000000004', 'organismo_financiador'),
    ('7b600000-0000-4000-8000-000000000005', 'geografico_presupuestario'),
)
SEED_CATEGORIA_ID = '7b600000-0000-4000-8000-000000000006'
SEED_GEOGRAFIA_ID = '7b600000-0000-4000-8000-000000000101'


CREAR_TABLA_PROPIEDAD = """
CREATE TABLE catalogos_seed_t4_propiedad (
    tipo_objeto varchar(20) NOT NULL,
    objeto_id uuid NOT NULL,
    PRIMARY KEY (tipo_objeto, objeto_id)
)
"""


ELIMINAR_TABLA_PROPIEDAD = 'DROP TABLE IF EXISTS catalogos_seed_t4_propiedad'


def _registrar_propiedad(schema_editor, tipo_objeto, objeto_id):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            'INSERT INTO catalogos_seed_t4_propiedad (tipo_objeto, objeto_id) '
            'VALUES (%s, %s) ON CONFLICT DO NOTHING',
            [tipo_objeto, str(objeto_id)],
        )


def registrar_versiones_2026(apps, schema_editor):
    Version = apps.get_model('catalogos', 'VersionClasificador')
    Geografico = apps.get_model('catalogos', 'ClasificadorGeograficoPresupuestario')

    versiones = {}
    for seed_id, tipo in SEEDS_OFICIALES:
        pk = UUID(seed_id)
        version = Version.objects.filter(pk=pk).first()
        if version is None:
            version = Version.objects.create(
                id=pk,
                tipo=tipo,
                gestion=2026,
                norma=NORMA,
                fecha_norma=date(2025, 6, 24),
                codigo_fuente=f'SEED-T4-RM249-{tipo.upper()}',
                procedencia_normativa=PROCEDENCIA,
                hash_fuente=HASH_CLASIFICADORES_2026,
                clasificacion_fuente='oficial',
                vigente=not Version.objects.filter(
                    tipo=tipo,
                    gestion=2026,
                    vigente=True,
                ).exists(),
            )
            _registrar_propiedad(schema_editor, 'version', pk)
        versiones[tipo] = version

    categoria_pk = UUID(SEED_CATEGORIA_ID)
    if not Version.objects.filter(pk=categoria_pk).exists():
        Version.objects.create(
            id=categoria_pk,
            tipo='categoria_programatica',
            gestion=2026,
            norma='',
            fecha_norma=None,
            codigo_fuente='SEED-T4-CATEGORIA-INCIERTA',
            procedencia_normativa=(
                'DA, UE y apertura programática no constan en el resumen '
                'normativo de Clasificadores 2026'
            ),
            hash_fuente='',
            clasificacion_fuente='incierta',
            vigente=False,
        )
        _registrar_propiedad(schema_editor, 'version', categoria_pk)

    geografia_pk = UUID(SEED_GEOGRAFIA_ID)
    version_geografica = versiones['geografico_presupuestario']
    if (
        version_geografica.tipo == 'geografico_presupuestario'
        and version_geografica.gestion == 2026
        and not Geografico.objects.filter(pk=geografia_pk).exists()
        and not Geografico.objects.filter(
            version_clasificador=version_geografica,
            departamento='3',
            provincia='5',
            municipio='1',
        ).exists()
    ):
        Geografico.objects.create(
            id=geografia_pk,
            version_clasificador=version_geografica,
            departamento='3',
            provincia='5',
            municipio='1',
            codigo_fuente='3|5|1',
            denominacion='Sacaba',
            procedencia_normativa='Clasificadores 2026, PDF pp. 155, 159',
        )
        _registrar_propiedad(schema_editor, 'geografia', geografia_pk)


def retirar_versiones_2026(apps, schema_editor):
    Version = apps.get_model('catalogos', 'VersionClasificador')
    Geografico = apps.get_model('catalogos', 'ClasificadorGeograficoPresupuestario')
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            "SELECT objeto_id FROM catalogos_seed_t4_propiedad "
            "WHERE tipo_objeto = 'geografia'"
        )
        geografia_ids = [row[0] for row in cursor.fetchall()]
        cursor.execute(
            "SELECT objeto_id FROM catalogos_seed_t4_propiedad "
            "WHERE tipo_objeto = 'version'"
        )
        version_ids = [row[0] for row in cursor.fetchall()]

    Geografico.objects.filter(pk__in=geografia_ids).delete()
    Version.objects.filter(pk__in=version_ids).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('catalogos', '0002_objetogasto_nivel_objetogasto_padre_and_more'),
    ]

    operations = [
        migrations.RunSQL(CREAR_TABLA_PROPIEDAD, ELIMINAR_TABLA_PROPIEDAD),
        migrations.RunPython(registrar_versiones_2026, retirar_versiones_2026),
    ]
