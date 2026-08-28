"""Revoca `sis_poa.formulate` a los perfiles POAU de unidad.

La 0016 los sembro con `sis_poa.formulate` heredado de FORMULADOR_POAU. Esa
capacidad no acota: ademas de la Matriz POAU abre `sis-poa/presupuesto-gastos`
y `sis-poa/presupuesto-recursos` (las dos rutas la exigen en su guard) y
enciende Dashboard POA, Priorizacion POA y POA en el menu lateral.

Un ENCARGADO_UO / VALIDADOR_POAU solo debe alcanzar las tres pantallas POAU de
SU unidad, y esas se gobiernan por `sis_poa.poau.*`. Como la 0016 solo agrega
capacidades (`add()` aditivo), volver a correrla no las quita: hace falta esta
revocacion explicita.

Alcance deliberadamente estrecho: toca UNICAMENTE esos dos roles. Los demas
—FORMULADOR_POAU incluido— conservan `sis_poa.formulate` intacta.

Idempotente: `remove()` sobre una relacion inexistente no falla.
"""
from django.db import migrations


ROLES_ACOTADOS = ('ENCARGADO_UO', 'VALIDADOR_POAU')
CAPACIDAD = 'sis_poa.formulate'


def revocar_formulate(apps, schema_editor):
    Rol = apps.get_model('accounts', 'Rol')
    Capacidad = apps.get_model('accounts', 'Capacidad')

    capacidad = Capacidad.objects.filter(codigo=CAPACIDAD).first()
    if capacidad is None:
        return
    for rol in Rol.objects.filter(codigo__in=ROLES_ACOTADOS):
        rol.capacidades.remove(capacidad)


def restituir_formulate(apps, schema_editor):
    """Deshace la revocacion, para que la migracion sea reversible."""
    Rol = apps.get_model('accounts', 'Rol')
    Capacidad = apps.get_model('accounts', 'Capacidad')

    capacidad = Capacidad.objects.filter(codigo=CAPACIDAD).first()
    if capacidad is None:
        return
    for rol in Rol.objects.filter(codigo__in=ROLES_ACOTADOS):
        rol.capacidades.add(capacidad)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0016_encargado_unidad_organizacional'),
    ]

    operations = [
        migrations.RunPython(revocar_formulate, restituir_formulate),
    ]
