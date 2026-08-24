"""Candado de gestión fiscal: una sola gestión habilitada (ADR-007).

Tres pasos en orden, y el orden importa: primero `activa` deja de nacer en
True (si no, cada gestión nueva pelearía por el candado), después se normaliza
lo que hay, y recién entonces se crea el índice único parcial. Al revés, la
constraint fallaría contra los datos sembrados por `0003_crear_gestiones_seed`,
que crea 2026 y 2027 con el default viejo.
"""
from django.db import migrations, models

# Los dos vocabularios del mismo campo `estado` (ver `models.py:25-32`).
ESTADOS_HABILITADOS = ('HABILITADA', 'abierta')


def normalizar_candado(apps, schema_editor):
    """Deja el candado en la gestión habilitada, o en ninguna.

    Antes de esta migración `activa` era un default suelto en True: en la base
    de desarrollo quedó coherente (2027 habilitada y activa, 2026 cerrada e
    inactiva), pero en una base recién migrada las dos gestiones sembradas
    nacen activas. La regla es la semántica nueva: el candado lo tiene la
    gestión cuyo estado es de habilitación, y ninguna otra.
    """
    GestionFiscal = apps.get_model('gestion', 'GestionFiscal')
    habilitada = (
        GestionFiscal.objects
        .filter(estado__in=ESTADOS_HABILITADOS)
        .order_by('-anio')
        .first()
    )
    GestionFiscal.objects.exclude(
        pk=habilitada.pk if habilitada else None
    ).filter(activa=True).update(activa=False)
    if habilitada is not None and not habilitada.activa:
        habilitada.activa = True
        habilitada.save(update_fields=['activa'])


def soltar_candado(apps, schema_editor):
    """Reversa: sin constraint, el estado previo era `activa=True` en todas."""
    GestionFiscal = apps.get_model('gestion', 'GestionFiscal')
    GestionFiscal.objects.update(activa=True)


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0004_gestionfiscal_fiscal_year_metadata'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gestionfiscal',
            name='activa',
            field=models.BooleanField(
                default=False,
                help_text=(
                    'Única gestión habilitada para planificar y programar en SIS-POA.'
                ),
                verbose_name='Gestión habilitada',
            ),
        ),
        migrations.RunPython(normalizar_candado, soltar_candado),
        migrations.AddConstraint(
            model_name='gestionfiscal',
            constraint=models.UniqueConstraint(
                condition=models.Q(activa=True),
                fields=('activa',),
                name='unica_gestion_habilitada',
                violation_error_message=(
                    'Ya hay una gestión habilitada; ciérrela antes de habilitar otra.'
                ),
            ),
        ),
    ]
