"""Semilla idempotente de catálogos RM 115 para SIS-PRO preinversión.

Uso:
    python manage.py seed_sispro_preinversion
"""
from django.core.management.base import BaseCommand

from apps.inversion.models_v2 import EstadosExpedientePreinversion, TipologiaRM115


class Command(BaseCommand):
    help = 'Carga catálogos base de preinversión RM 115 (idempotente)'

    def handle(self, *args, **options):
        total = 0
        print('Tipologías RM 115:')
        for codigo, nombre in TipologiaRM115.CHOICES:
            print(f'  {codigo}: {nombre}')
            total += 1
        print('Estados del expediente de preinversión:')
        for codigo, nombre in EstadosExpedientePreinversion.CHOICES:
            print(f'  {codigo}: {nombre}')
            total += 1
        self.stdout.write(
            self.style.SUCCESS(
                f'Catálogos RM 115 listos (definidos como choices versionados '
                f'en models_v2). Total: {total}'
            )
        )
