from datetime import date

from django.db import migrations


HASH_CLASIFICADORES_2026 = (
    '9719fd35d33a4ce0278aef96a5599cb93aa4d9f148d45f57adf81730d5a90ccf'
)
NORMA = 'RM MEFP N.º 249/2025'
PROCEDENCIA = 'Clasificadores Presupuestarios Gestión 2026, RM 249, PDF pp. 3-4'
TIPOS_OFICIALES = (
    'institucional',
    'objeto_gasto',
    'fuente_financiamiento',
    'organismo_financiador',
    'geografico_presupuestario',
)


def registrar_versiones_2026(apps, schema_editor):
    VersionClasificador = apps.get_model('catalogos', 'VersionClasificador')
    Geografico = apps.get_model('catalogos', 'ClasificadorGeograficoPresupuestario')

    versiones = {}
    for tipo in TIPOS_OFICIALES:
        version, _ = VersionClasificador.objects.update_or_create(
            tipo=tipo,
            gestion=2026,
            defaults={
                'norma': NORMA,
                'fecha_norma': date(2025, 6, 24),
                'codigo_fuente': f'RM-249-2025-{tipo.upper()}',
                'procedencia_normativa': PROCEDENCIA,
                'hash_fuente': HASH_CLASIFICADORES_2026,
                'clasificacion_fuente': 'oficial',
                'vigente': True,
            },
        )
        versiones[tipo] = version

    VersionClasificador.objects.update_or_create(
        tipo='categoria_programatica',
        gestion=2026,
        defaults={
            'norma': '',
            'fecha_norma': None,
            'codigo_fuente': 'PENDIENTE-DIRECTRICES-SIGEP-2026',
            'procedencia_normativa': (
                'DA, UE y apertura programática no constan en el resumen '
                'normativo de Clasificadores 2026'
            ),
            'hash_fuente': '',
            'clasificacion_fuente': 'incierta',
            'vigente': False,
        },
    )

    Geografico.objects.update_or_create(
        version_clasificador=versiones['geografico_presupuestario'],
        departamento='3',
        provincia='5',
        municipio='1',
        defaults={
            'codigo_fuente': '3|5|1',
            'denominacion': 'Sacaba',
            'procedencia_normativa': 'Clasificadores 2026, PDF pp. 155, 159',
        },
    )


def retirar_versiones_2026(apps, schema_editor):
    VersionClasificador = apps.get_model('catalogos', 'VersionClasificador')
    Geografico = apps.get_model('catalogos', 'ClasificadorGeograficoPresupuestario')

    Geografico.objects.filter(
        version_clasificador__gestion=2026,
        codigo_fuente='3|5|1',
    ).delete()
    VersionClasificador.objects.filter(
        gestion=2026,
        codigo_fuente__in=[
            *(f'RM-249-2025-{tipo.upper()}' for tipo in TIPOS_OFICIALES),
            'PENDIENTE-DIRECTRICES-SIGEP-2026',
        ],
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('catalogos', '0002_objetogasto_nivel_objetogasto_padre_and_more'),
    ]

    operations = [
        migrations.RunPython(registrar_versiones_2026, retirar_versiones_2026),
    ]
