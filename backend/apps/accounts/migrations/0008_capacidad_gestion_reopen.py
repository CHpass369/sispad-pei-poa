# Reabrir y eliminar una gestión fiscal son actos de gobernanza, no de
# formulación: revierten o borran un acto formal del ciclo presupuestario.
#
# `sis_poa.budget.manage` no alcanza para distinguirlos, porque la tiene
# cualquiera que administre el presupuesto. Esta capacidad separada los deja
# en manos de la jefatura de POA y de administración, y de nadie más.
#
# Idempotente: get_or_create + add() solo de lo faltante, para no pisar
# ajustes manuales posteriores.
from django.db import migrations

CODIGO = 'sis_poa.budget.reopen'
NOMBRE = 'Reabrir o eliminar gestion fiscal'
SISTEMA = 'sis-poa'
ORDEN = 30

# `superadmin` atraviesa igual todos los filtros por ser superusuario; se lo
# asigna explícitamente para que la capacidad figure en su catálogo.
ROLES = ['jefe_poa', 'admin_poa', 'superadmin']


def sembrar_capacidad(apps, schema_editor):
    Capacidad = apps.get_model('accounts', 'Capacidad')
    Rol = apps.get_model('accounts', 'Rol')

    capacidad, _ = Capacidad.objects.get_or_create(
        codigo=CODIGO,
        defaults={'nombre': NOMBRE, 'sistema': SISTEMA, 'orden': ORDEN},
    )
    for codigo_rol in ROLES:
        rol = Rol.objects.filter(codigo=codigo_rol).first()
        if rol and not rol.capacidades.filter(codigo=CODIGO).exists():
            rol.capacidades.add(capacidad)


def quitar_capacidad(apps, schema_editor):
    Capacidad = apps.get_model('accounts', 'Capacidad')
    Capacidad.objects.filter(codigo=CODIGO).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_roles_poa_pe'),
    ]

    operations = [
        migrations.RunPython(sembrar_capacidad, quitar_capacidad),
    ]
