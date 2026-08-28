"""Seed F1 (ADR-003): 6 roles base del sistema + capacidades mínimas viables.

Uso: python manage.py seed_roles_permisos

Idempotente: get_or_create por codigo y add() solo de las capacidades
faltantes, de modo que preserva ajustes manuales posteriores (patron de la
migracion 0007). Correrlo N veces no duplica ni revoca.

Reconciliacion con seeds previos (0002-0007):
- `sis_pe.pad.edit`, `sis_pe.pei.edit` y `sis_poa.poau.edit` ya existen con
  sistema 'sis-pe'/'sis-poa' (con guion): se reutilizan sin modificar.
- Las capacidades nuevas usan sistema 'sis_pe'/'sis_poa'/'accounts'
  (underscore) por instruccion explicita de F1. Convivencia de ambas
  convenciones registrada como deuda.
- Los roles "todas las capacidades sis_pe.* / sis_poa.*" se resuelven por
  prefijo sobre la DB: incluyen las preexistentes (p.ej.
  `sis_poa.budget.manage`, que los ViewSets actuales exigen via
  TieneCapacidad) y las nuevas de F1.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import Capacidad, Rol

# Capacidad requerida por el baseline, aunque ya la crea una migracion
# historica. Mantenerla aqui hace que el seed operativo converja en una DB
# instalada parcialmente.
CAPACIDADES_BASE = [
    ('sis_poa.formulate', 'Formular POA/POAU', 'sis-poa'),
    ('sis_poa.poau.edit', 'Editar POAU', 'sis-poa'),
]

# Capacidades NUEVAS de F1 (las que aun no existen en migraciones 0002-0007).
# (codigo, nombre, sistema)
CAPACIDADES_NUEVAS = [
    # SIS-PE
    ('sis_pe.pad.view', 'Ver PAD', 'sis_pe'),
    ('sis_pe.pei.view', 'Ver PEI', 'sis_pe'),
    ('sis_pe.articulacion.view', 'Ver articulacion', 'sis_pe'),
    ('sis_pe.articulacion.edit', 'Editar articulacion', 'sis_pe'),
    ('sis_pe.indicadores.view', 'Ver indicadores', 'sis_pe'),
    ('sis_pe.indicadores.edit', 'Editar indicadores', 'sis_pe'),
    ('sis_pe.evaluacion.view', 'Ver evaluacion', 'sis_pe'),
    ('sis_pe.evaluacion.edit', 'Editar evaluacion', 'sis_pe'),
    # SIS-POA
    ('sis_poa.poau.view', 'Ver POAU', 'sis_poa'),
    ('sis_poa.poau.create', 'Crear POAU', 'sis_poa'),
    ('sis_poa.poau.submit', 'Enviar POAU', 'sis_poa'),
    ('sis_poa.poau.review', 'Revisar POAU', 'sis_poa'),
    ('sis_poa.poau.approve', 'Aprobar POAU', 'sis_poa'),
    ('sis_poa.poa.view', 'Ver POA', 'sis_poa'),
    ('sis_poa.poa.edit', 'Editar POA', 'sis_poa'),
    ('sis_poa.techos.view', 'Ver techos presupuestarios', 'sis_poa'),
    ('sis_poa.techos.edit', 'Editar techos presupuestarios', 'sis_poa'),
    ('sis_poa.distribuciones.view', 'Ver distribuciones', 'sis_poa'),
    ('sis_poa.distribuciones.edit', 'Editar distribuciones', 'sis_poa'),
    ('sis_poa.programacion.view', 'Ver programacion', 'sis_poa'),
    ('sis_poa.programacion.edit', 'Editar programacion', 'sis_poa'),
    ('sis_poa.reportes.view', 'Ver reportes operativos', 'sis_poa'),
    ('sis_poa.seguimiento.view', 'Ver seguimiento', 'sis_poa'),
    ('sis_poa.seguimiento.edit', 'Editar seguimiento', 'sis_poa'),
    # Gestion de usuarios (accounts)
    ('accounts.usuario.view', 'Ver usuarios', 'accounts'),
    ('accounts.usuario.create', 'Crear usuarios', 'accounts'),
    ('accounts.usuario.edit', 'Editar usuarios', 'accounts'),
    ('accounts.usuario.activate', 'Activar o desactivar usuarios', 'accounts'),
    ('accounts.rol.view', 'Ver roles', 'accounts'),
    ('accounts.rol.create', 'Crear roles', 'accounts'),
    ('accounts.rol.edit', 'Editar roles', 'accounts'),
    ('accounts.capacidad.view', 'Ver capacidades', 'accounts'),
    ('accounts.capacidad.assign', 'Asignar capacidades', 'accounts'),
    ('accounts.alcance.view', 'Ver alcances organizacionales', 'accounts'),
    ('accounts.alcance.assign', 'Asignar alcances organizacionales', 'accounts'),
    ('accounts.solicitud.view', 'Ver solicitudes de acceso', 'accounts'),
    ('accounts.solicitud.approve', 'Aprobar solicitudes de acceso', 'accounts'),
]

# Las capacidades de gestion de usuarios que reciben JEFE_PE y JEFE_POA
# ("limitadas a SIS-PE/SIS-POA": el limite territorial lo aplica el scope
# resolver de F2 via AlcanceOrganizacional; F1 solo asigna la capacidad).
CAPACIDADES_USUARIO = [
    'accounts.usuario.view',
    'accounts.usuario.create',
    'accounts.usuario.edit',
    'accounts.usuario.activate',
]

CAPACIDADES_FORMULADOR = [
    'sis_poa.formulate',
    'sis_poa.poau.view',
    'sis_poa.poau.create',
    'sis_poa.poau.edit',  # ya existe (0002, sistema 'sis-poa')
    'sis_poa.poau.submit',
]

# codigo -> (nombre visible, prefijos de capacidad, capacidades explicitas)
ROLES = {
    'SUPER_ADMIN': (
        'Superadministrador',
        ('sis_pe.', 'sis_poa.', 'accounts.'),
        (),
    ),
    'SECRETARIO_MUNICIPAL': (
        'Secretario Municipal',
        ('sis_poa.',),
        (),
    ),
    'DIRECTOR': (
        'Director',
        ('sis_poa.',),
        (),
    ),
    'JEFE_POA': (
        'Jefe POA',
        ('sis_poa.',),
        tuple(CAPACIDADES_USUARIO),
    ),
    'JEFE_PE': (
        'Jefe PE',
        ('sis_pe.',),
        tuple(CAPACIDADES_USUARIO),
    ),
    'FORMULADOR_POAU': (
        'Formulador POAU',
        (),
        tuple(CAPACIDADES_FORMULADOR),
    ),
}


class Command(BaseCommand):
    help = 'Siembra los 6 roles base del sistema y las capacidades F1 (ADR-003).'

    @transaction.atomic
    def handle(self, *args, **options):
        creadas = 0
        for orden, (codigo, nombre, sistema) in enumerate(
            CAPACIDADES_BASE + CAPACIDADES_NUEVAS, start=100,
        ):
            _, created = Capacidad.objects.get_or_create(
                codigo=codigo,
                defaults={
                    'nombre': nombre,
                    'sistema': sistema,
                    'activo': True,
                    'orden': orden,
                },
            )
            creadas += int(created)

        for orden, (codigo, (nombre, prefijos, explicitas)) in enumerate(ROLES.items(), start=1):
            rol, _ = Rol.objects.get_or_create(
                codigo=codigo,
                defaults={
                    'nombre': nombre,
                    'descripcion': nombre,
                    'es_sistema': True,
                    'orden': orden,
                },
            )
            # Invariante del seed: los 6 roles base son de sistema (no
            # editables desde UI). Se refuerza aunque el rol ya existiera.
            if not rol.es_sistema:
                rol.es_sistema = True
                rol.save(update_fields=['es_sistema'])

            objetivo = set(explicitas)
            for prefijo in prefijos:
                objetivo.update(
                    Capacidad.objects.filter(
                        codigo__startswith=prefijo,
                    ).values_list('codigo', flat=True)
                )

            actuales = set(rol.capacidades.values_list('codigo', flat=True))
            faltantes = list(
                Capacidad.objects.filter(codigo__in=objetivo - actuales)
            )
            if faltantes:
                rol.capacidades.add(*faltantes)

        # La migración IAM 0002 define `superadmin` como el rol legado con
        # todas las capacidades. Se conserva para instalaciones existentes y
        # se reconcilia aquí porque las capacidades F1 se crean después de esa
        # migración y no pueden incorporarse automáticamente al M2M histórico.
        superadmin = Rol.objects.filter(codigo='superadmin').first()
        if superadmin:
            actuales = set(
                superadmin.capacidades.values_list('codigo', flat=True)
            )
            faltantes = list(
                Capacidad.objects.exclude(codigo__in=actuales)
            )
            if faltantes:
                superadmin.capacidades.add(*faltantes)

        self.stdout.write(self.style.SUCCESS(
            f'Seed F1 completado: {creadas} capacidades nuevas creadas '
            f'(de {len(CAPACIDADES_BASE) + len(CAPACIDADES_NUEVAS)} definidas); '
            f'{len(ROLES)} roles '
            f'base verificados.'
        ))
