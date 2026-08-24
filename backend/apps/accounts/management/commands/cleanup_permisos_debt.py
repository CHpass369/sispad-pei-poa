"""F1.5: cleanup de deudas técnicas de F1.

1. Migra capacidades con sistema con guion ('sis-pe', 'sis-poa') a
   underscore ('sis_pe', 'sis_poa').
2. Marca como deprecated los roles legacy que no son los 6 roles base
   del sistema (UPPERCASE).

Idempotente: correrlo N veces produce el mismo resultado.

Uso: python manage.py cleanup_permisos_debt
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import Capacidad, Rol

ROLES_BASE = [
    'SUPER_ADMIN',
    'SECRETARIO_MUNICIPAL',
    'DIRECTOR',
    'JEFE_POA',
    'JEFE_PE',
    'FORMULADOR_POAU',
]


class Command(BaseCommand):
    help = 'F1.5: migra sistema guion→underscore y depreca roles legacy.'

    @transaction.atomic
    def handle(self, *args, **options):
        # --- 1. Migrar sistema de capacidades: guion → underscore ---
        mapping = {'sis-pe': 'sis_pe', 'sis-poa': 'sis_poa'}
        total_caps = 0
        for viejo, nuevo in mapping.items():
            qs = Capacidad.objects.filter(sistema=viejo)
            count = qs.count()
            qs.update(sistema=nuevo)
            total_caps += count
            if count:
                self.stdout.write(f'  {viejo} → {nuevo}: {count} capacidades')
        self.stdout.write(self.style.SUCCESS(
            f'{total_caps} capacidades migradas de guion a underscore.'
        ))

        # --- 2. Marcar roles legacy como deprecated ---
        roles_legacy = Rol.objects.filter(
            es_sistema=True,
        ).exclude(
            codigo__in=ROLES_BASE,
        )
        total_roles = roles_legacy.count()
        roles_legacy.update(deprecated=True)
        self.stdout.write(self.style.SUCCESS(
            f'{total_roles} roles legacy marcados como deprecated.'
        ))

        # --- Resumen ---
        self.stdout.write(self.style.SUCCESS(
            f'Cleanup F1.5 completado: {total_caps} capacidades migradas, '
            f'{total_roles} roles deprecated.'
        ))
