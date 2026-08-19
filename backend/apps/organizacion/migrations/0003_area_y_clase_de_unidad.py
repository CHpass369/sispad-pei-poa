"""Cuarto nivel organizacional (Área) y clase funcional de la unidad.

La codificación oficial del GAMS 2026 baja un nivel más que los tres que
existían (Secretaría → Dirección → Unidad) y clasifica cada unidad como
sustantiva, administrativa o de asesoramiento. Ambos datos vienen del
catálogo maestro y no tenían dónde guardarse.
"""
from django.db import migrations, models


TIPOS = [
    ('SEC', 'Secretaría', 1),
    ('DIR', 'Dirección', 2),
    ('UNI', 'Unidad', 3),
    ('ARE', 'Área', 4),
]


def sembrar_tipos(apps, schema_editor):
    TipoUnidad = apps.get_model('organizacion', 'TipoUnidad')
    for codigo, nombre, nivel in TIPOS:
        TipoUnidad.objects.get_or_create(
            codigo=codigo, defaults={'nombre': nombre, 'nivel': nivel},
        )


def quitar_area(apps, schema_editor):
    """Solo borra el nivel Área si ninguna unidad lo usa."""
    TipoUnidad = apps.get_model('organizacion', 'TipoUnidad')
    area = TipoUnidad.objects.filter(codigo='ARE').first()
    if area and not area.unidades.exists():
        area.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('organizacion', '0002_alter_direccionadministrativa_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='unidadorganizacional',
            name='clase',
            field=models.CharField(
                max_length=20, blank=True, default='',
                choices=[
                    ('SUSTANTIVA', 'Sustantiva'),
                    ('ADMINISTRATIVA', 'Administrativa'),
                    ('ASESORAMIENTO', 'De asesoramiento'),
                ],
                verbose_name='Clase funcional',
            ),
        ),
        migrations.RunPython(sembrar_tipos, quitar_area),
    ]
