"""
Semilla de roles del sistema - POAU y Articulación PAD.
Idempotente: python manage.py shell < scripts/seed_roles.py
"""
from apps.accounts.models import Rol

roles = [
    ('articulador_tecnico', 'Técnico de Articulación PAD', True,
     'Puede crear y editar articulaciones del PAD'),
    ('articulador_aprobador', 'Administrador de Articulaciones', True,
     'Aprueba o rechaza articulaciones del PAD'),
    ('poau_responsable', 'Responsable POAU de Unidad', True,
     'Responsable de llenar el POAU de su unidad organizacional'),
    ('poau_revisor', 'Revisor de POAU', True,
     'Puede revisar, aprobar o rechazar POAU de las unidades'),
]

for codigo, nombre, sistema, descripcion in roles:
    Rol.objects.get_or_create(
        codigo=codigo,
        defaults={
            'nombre': nombre,
            'es_sistema': sistema,
            'descripcion': descripcion,
        }
    )

print(f'Roles POAU/Articulación creados: {len(roles)}')
