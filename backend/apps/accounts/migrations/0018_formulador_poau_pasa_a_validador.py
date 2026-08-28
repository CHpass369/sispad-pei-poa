"""Reasigna los usuarios de FORMULADOR_POAU a VALIDADOR_POAU.

FORMULADOR_POAU lleva `sis_poa.formulate`, que no acota: ademas de la Matriz
POAU abre `sis-poa/presupuesto-gastos` y `sis-poa/presupuesto-recursos` (ambas
rutas la exigen en su guard) y enciende Dashboard POA, Priorizacion POA y POA
en el menu lateral. VALIDADOR_POAU cubre el mismo trabajo de unidad —formular,
editar, enviar y revisar el POAU— sin ese arrastre.

Que hace, por usuario que tenga FORMULADOR_POAU:

1. Cambia el rol asignado a VALIDADOR_POAU (quita uno, pone el otro).
2. Reapunta sus `AlcanceOrganizacional` con `rol=FORMULADOR_POAU`.

El paso 2 respeta `uniq_alcance_usuario_rol_unidad_gestion`
(usuario, rol, unidad, fiscal_year; `nulls_distinct=False`): si el usuario ya
tenia un alcance VALIDADOR equivalente, el de FORMULADOR se retira en vez de
reapuntarse, porque reapuntarlo violaria la unicidad.

`scope_type` NO se toca. Ambos roles usan SELF en
`SCOPES_FIJOS_ROLES_SISTEMA`, pero un alcance concreto pudo guardarse con otro
valor por decision de un administrador: cambiarlo aca alteraria en silencio el
alcance territorial de alguien.

El rol FORMULADOR_POAU se conserva: sigue existiendo y es asignable. Esta
migracion mueve a los usuarios que ya lo tenian, no retira el perfil.

Irreversible por diseño: despues de correrla no queda registro de cuales
VALIDADOR_POAU fueron antes FORMULADOR_POAU, asi que revertir devolveria el rol
a quien nunca lo tuvo. El reverso es no-op y deja a todos como VALIDADOR.
"""
from django.db import migrations


ORIGEN = 'FORMULADOR_POAU'
DESTINO = 'VALIDADOR_POAU'


def pasar_a_validador(apps, schema_editor):
    Rol = apps.get_model('accounts', 'Rol')
    Usuario = apps.get_model('accounts', 'Usuario')
    Alcance = apps.get_model('accounts', 'AlcanceOrganizacional')

    origen = Rol.objects.filter(codigo=ORIGEN).first()
    destino = Rol.objects.filter(codigo=DESTINO).first()
    if origen is None or destino is None:
        # Instalacion sin alguno de los dos perfiles: nada que mover.
        return

    for usuario in Usuario.objects.filter(roles=origen).distinct():
        usuario.roles.remove(origen)
        usuario.roles.add(destino)

    for alcance in Alcance.objects.filter(rol=origen).select_related('usuario'):
        equivalente = Alcance.objects.filter(
            usuario_id=alcance.usuario_id,
            rol=destino,
            unidad_id=alcance.unidad_id,
            fiscal_year_id=alcance.fiscal_year_id,
        ).exists()
        if equivalente:
            alcance.delete()
        else:
            alcance.rol = destino
            alcance.save(update_fields=['rol'])


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0017_poau_roles_sin_formulate'),
    ]

    operations = [
        migrations.RunPython(pasar_a_validador, migrations.RunPython.noop),
    ]
