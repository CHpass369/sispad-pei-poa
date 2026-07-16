"""
Script de datos semilla idempotente.
Ejecutar: python manage.py shell < scripts/seed.py
"""
from apps.accounts.models import Usuario, Rol
from apps.gestion.models import GestionFiscal

# Roles del sistema
roles = [
    ('superadmin', 'Superadministrador Técnico', True),
    ('admin_poa', 'Administrador POA', True),
    ('admin_presupuesto', 'Administrador de Presupuesto', True),
    ('responsable_unidad', 'Responsable POA de Unidad', True),
    ('revisor_planificacion', 'Revisor de Planificación', True),
    ('revisor_presupuesto', 'Revisor de Presupuesto', True),
    ('revisor_inversion', 'Revisor de Proyectos', True),
    ('revisor_juridico', 'Revisor Jurídico', True),
    ('mae', 'Máxima Autoridad Ejecutiva', True),
    ('auditor', 'Auditor', True),
    ('consulta', 'Usuario de Consulta', True),
    ('control_social', 'Participación y Control Social', True),
]

for codigo, nombre, sistema in roles:
    Rol.objects.get_or_create(
        codigo=codigo,
        defaults={'nombre': nombre, 'es_sistema': sistema, 'descripcion': nombre}
    )

# Superusuario
admin, created = Usuario.objects.get_or_create(
    email='admin@gamsacaba.gob.bo',
    defaults={
        'first_name': 'Admin',
        'last_name': 'SISPOA',
        'is_staff': True,
        'is_superuser': True,
    }
)
if created:
    admin.set_password('admin2026')
    admin.save()

# Gestión 2026
GestionFiscal.objects.get_or_create(
    anio=2026,
    defaults={
        'estado': 'preparacion',
        'anio_inicio_plurianual': 2026,
        'anio_fin_plurianual': 2028,
    }
)

print('Semilla ejecutada correctamente.')
print(f'  - {Rol.objects.count()} roles')
print(f'  - {Usuario.objects.count()} usuarios')
print(f'  - {GestionFiscal.objects.count()} gestiones fiscales')
