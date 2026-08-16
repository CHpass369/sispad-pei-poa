"""Normaliza el catálogo nacional: separa nombre y objetivo concatenados.

Históricamente el importador guardaba la denominación como
``'<nombre> — <objetivo>'`` porque EjePGDESA/ComponentePDESA no tenían
campos propios. Desde la migración de campos, este comando separa los
registros existentes en ``denominacion`` (solo nombre) y
``objetivo_impacto``/``objetivo_efecto``.

Idempotente: solo procesa registros cuyo campo de objetivo esté vacío y
cuya denominación contenga el separador ' — '.

Uso:
    python manage.py normalizar_objetivos_catalogo
    python manage.py normalizar_objetivos_catalogo --dry-run
"""
from django.core.management.base import BaseCommand

from apps.codificacion.models import EjePGDESA, ComponentePDESA

SEPARADOR = ' — '


def _separar(denominacion):
    """Retorna (nombre, objetivo) si hay separador válido; si no, (denominacion, '')."""
    if SEPARADOR not in denominacion:
        return denominacion.strip(), ''
    nombre, objetivo = denominacion.split(SEPARADOR, 1)
    nombre = nombre.strip()
    objetivo = objetivo.strip()
    if not nombre or not objetivo or objetivo == nombre:
        return denominacion.strip(), ''
    return nombre, objetivo


class Command(BaseCommand):
    help = 'Separa nombre y objetivo concatenados en el catálogo nacional (idempotente).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Solo informa qué registros se actualizarían, sin persistir.',
        )

    def handle(self, *args, **options):
        dry = options['dry_run']
        total_ejes = 0
        total_componentes = 0

        for eje in EjePGDESA.objects.select_related('version_catalogo').all():
            if eje.objetivo_impacto or SEPARADOR not in eje.denominacion:
                continue
            nombre, objetivo = _separar(eje.denominacion)
            if not objetivo:
                continue
            self.stdout.write(
                f'  Eje [{eje.codigo}] v{eje.version_catalogo.gestion}: '
                f'"{nombre[:60]}..." -> objetivo ({len(objetivo)} chars)'
            )
            if not dry:
                eje.denominacion = nombre
                eje.objetivo_impacto = objetivo
                eje.save(update_fields=['denominacion', 'objetivo_impacto'])
            total_ejes += 1

        for comp in ComponentePDESA.objects.select_related(
            'version_catalogo', 'eje'
        ).all():
            if comp.objetivo_efecto or SEPARADOR not in comp.denominacion:
                continue
            nombre, objetivo = _separar(comp.denominacion)
            if not objetivo:
                continue
            self.stdout.write(
                f'  Componente [{comp.eje.codigo}.{comp.codigo}] '
                f'v{comp.version_catalogo.gestion}: '
                f'"{nombre[:60]}..." -> objetivo ({len(objetivo)} chars)'
            )
            if not dry:
                comp.denominacion = nombre
                comp.objetivo_efecto = objetivo
                comp.save(update_fields=['denominacion', 'objetivo_efecto'])
            total_componentes += 1

        modo = 'DRY-RUN (sin persistir)' if dry else 'persistido'
        self.stdout.write(
            self.style.SUCCESS(
                f'Normalización {modo}: {total_ejes} ejes, '
                f'{total_componentes} componentes.'
            )
        )
