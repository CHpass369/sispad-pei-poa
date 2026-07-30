"""Seed inicial de catálogos territoriales y entidad codificadora (T1.4).

Carga la cadena CGEO 03 Cochabamba -> 0310 Chapare -> 031001 Sacaba como
PROVISIONAL y la única entidad codificadora 1312 (GAM Sacaba).
Idempotente: usa get_or_create, una segunda corrida no cambia nada.
"""
from django.db import migrations


def seed_catalogos(apps, schema_editor):
    EntidadTerritorialCGEO = apps.get_model('codificacion', 'EntidadTerritorialCGEO')
    EntidadCodificadora = apps.get_model('codificacion', 'EntidadCodificadora')

    cochabamba, _ = EntidadTerritorialCGEO.objects.get_or_create(
        codigo='03',
        defaults={
            'nombre': 'Cochabamba',
            'nivel': 'departamento',
            'estado': 'provisional',
        },
    )
    chapare, _ = EntidadTerritorialCGEO.objects.get_or_create(
        codigo='0310',
        defaults={
            'nombre': 'Chapare',
            'nivel': 'provincia',
            'padre': cochabamba,
            'estado': 'provisional',
        },
    )
    EntidadTerritorialCGEO.objects.get_or_create(
        codigo='031001',
        defaults={
            'nombre': 'Sacaba',
            'nivel': 'municipio',
            'padre': chapare,
            'estado': 'provisional',
        },
    )

    EntidadCodificadora.objects.get_or_create(
        codigo='1312',
        defaults={
            'denominacion': 'Gobierno Autónomo Municipal de Sacaba',
            'activo': True,
        },
    )


def revertir_seed(apps, schema_editor):
    EntidadTerritorialCGEO = apps.get_model('codificacion', 'EntidadTerritorialCGEO')
    EntidadCodificadora = apps.get_model('codificacion', 'EntidadCodificadora')
    EntidadTerritorialCGEO.objects.filter(
        codigo__in=['03', '0310', '031001'],
    ).delete()
    EntidadCodificadora.objects.filter(codigo='1312').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('codificacion', '0003_entidadcodificadora_entidadterritorialcgeo_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_catalogos, revertir_seed),
    ]
