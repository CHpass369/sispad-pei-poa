"""Comando de auditoría de migración legacy→V2 (WP-05 / ADR-004).

Uso:
    python manage.py legacy_audit --inventario [--dry-run] [--apps a b c]
        Registra todos los registros legacy en LegacyMigrationMap con su
        checksum (dry-run: solo reporta conteos sin escribir).

    python manage.py legacy_audit --marcar-migrado <app.Modelo>:<uuid>
        --destino-tipo <Tipo> --destino-uuid <uuid> [--lote x] [--dry-run]
        Marca un registro legacy como migrado hacia su destino V2.

    python manage.py legacy_audit --reconciliar [--dry-run]
        Compara el checksum actual de cada registro 'migrado' con el
        almacenado: reconciliado o discrepancia.

    python manage.py legacy_audit --estado <estado>
        Reporta el conteo por estado.
"""
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count

from apps.core.migration_audit import checksum_registro, modelos_de_aplicacion
from apps.core.models import LegacyMigrationMap

APP_EXCLUIDAS = {'core'}


class Command(BaseCommand):
    help = 'Herramienta de auditoría de migración legacy→V2 (ADR-004, WP-05)'

    def add_arguments(self, parser):
        parser.add_argument('--inventario', action='store_true')
        parser.add_argument('--reconciliar', action='store_true')
        parser.add_argument('--estado', choices=[
            s for s, _ in LegacyMigrationMap.Estados.CHOICES
        ])
        parser.add_argument('--marcar-migrado', dest='marcar_migrado')
        parser.add_argument('--destino-tipo', dest='destino_tipo', default='')
        parser.add_argument('--destino-uuid', dest='destino_uuid', default='')
        parser.add_argument('--apps', nargs='*', default=None)
        parser.add_argument('--lote', default=None)
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        if options['estado']:
            self._reportar_estado(options['estado'])
            return
        if options['marcar_migrado']:
            self._marcar_migrado(options)
            return
        if options['reconciliar']:
            self._reconciliar(options)
            return
        if options['inventario']:
            self._inventario(options)
            return
        raise CommandError(
            'Indique una acción: --inventario, --reconciliar, '
            '--marcar-migrado o --estado.'
        )

    def _modelos(self, options):
        apps_filtro = set(options['apps'] or [])
        for model in modelos_de_aplicacion():
            if model._meta.app_label in APP_EXCLUIDAS:
                continue
            if apps_filtro and model._meta.app_label not in apps_filtro:
                continue
            yield model

    def _inventario(self, options):
        dry = options['dry_run']
        total = 0
        creados = 0
        for model in self._modelos(options):
            qs = model.objects.all()
            count = qs.count()
            total += count
            self.stdout.write(
                f'{model._meta.app_label}.{model._meta.model_name}: {count}'
            )
            if dry or not count:
                continue
            for obj in qs.iterator(chunk_size=500):
                _, was_created = LegacyMigrationMap.objects.get_or_create(
                    app_legacy=model._meta.app_label,
                    modelo_legacy=model._meta.model_name,
                    uuid_legacy=obj.pk,
                    defaults={
                        'checksum': checksum_registro(obj),
                        'lote': options['lote'] or 'inicial',
                    },
                )
                creados += int(was_created)
        self.stdout.write(
            self.style.SUCCESS(
                f'Registros inventariados: {total} '
                f'({creados} nuevos en el mapa, dry-run={dry})'
            )
        )

    def _marcar_migrado(self, options):
        dry = options['dry_run']
        referencia = options['marcar_migrado']
        try:
            app_modelo, _, uuid_str = referencia.partition(':')
            app_label, _, modelo = app_modelo.partition('.')
            if not (app_label and modelo and uuid_str):
                raise ValueError
            from django.apps import apps as django_apps
            model = django_apps.get_model(app_label, modelo)
        except (ValueError, LookupError):
            raise CommandError(
                'Formato esperado: <app.Modelo>:<uuid> (p.ej. '
                'planificacion.Plan:3f2a...).'
            )
        try:
            obj = model.objects.get(pk=uuid_str)
        except model.DoesNotExist:
            raise CommandError(f'No existe {referencia} en la base.')

        destino_uuid = options['destino_uuid'] or None
        if not options['destino_tipo']:
            raise CommandError('--destino-tipo es obligatorio al migrar.')

        if not dry:
            entry, created = LegacyMigrationMap.objects.get_or_create(
                app_legacy=app_label,
                modelo_legacy=model._meta.model_name,
                uuid_legacy=obj.pk,
                defaults={
                    'lote': options['lote'] or 'inicial',
                    'checksum': checksum_registro(obj),
                },
            )
            entry.tipo_destino = options['destino_tipo']
            entry.uuid_destino = destino_uuid
            entry.estado = LegacyMigrationMap.Estados.MIGRADO
            entry.lote = options['lote'] or 'inicial'
            entry.checksum = checksum_registro(obj)
            entry.observaciones = ''
            entry.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Marcado migrado: {referencia} → '
                    f'{options["destino_tipo"]}:{destino_uuid or "-"}'
                )
            )
        else:
            self.stdout.write(
                f'[dry-run] marcaría {referencia} → '
                f'{options["destino_tipo"]}:{destino_uuid or "-"}'
            )

    def _reconciliar(self, options):
        dry = options['dry_run']
        qs = LegacyMigrationMap.objects.filter(
            estado=LegacyMigrationMap.Estados.MIGRADO,
        )
        if options['lote']:
            qs = qs.filter(lote=options['lote'])
        total = 0
        ok = 0
        discrep = 0
        for entry in qs.iterator(chunk_size=500):
            total += 1
            try:
                from django.apps import apps as django_apps
                model = django_apps.get_model(
                    entry.app_legacy, entry.modelo_legacy,
                )
                obj = model.objects.get(pk=entry.uuid_legacy)
                actual = checksum_registro(obj)
                estado = (
                    LegacyMigrationMap.Estados.RECONCILIADO
                    if actual == entry.checksum
                    else LegacyMigrationMap.Estados.DISCREPANCIA
                )
            except model.DoesNotExist:
                estado = LegacyMigrationMap.Estados.DISCREPANCIA
            if estado == LegacyMigrationMap.Estados.RECONCILIADO:
                ok += 1
            else:
                discrep += 1
            if not dry:
                entry.estado = estado
                if estado == LegacyMigrationMap.Estados.DISCREPANCIA:
                    entry.observaciones = (
                        'Checksum no coincide: el registro legacy fue '
                        'modificado tras la migración.'
                    )
                entry.save(update_fields=['estado', 'observaciones', 'fecha'])
        self.stdout.write(
            self.style.SUCCESS(
                f'Reconciliados: {ok}/{total}, discrepancias: {discrep} '
                f'(dry-run={dry})'
            )
        )

    def _reportar_estado(self, estado):
        qs = LegacyMigrationMap.objects.values('app_legacy', 'modelo_legacy')
        if estado:
            qs = LegacyMigrationMap.objects.filter(estado=estado)
        conteos = (
            qs.values('app_legacy', 'modelo_legacy')
            .annotate(total=Count('id'))
            .order_by('app_legacy', 'modelo_legacy')
        )
        gran_total = 0
        for c in conteos:
            gran_total += c['total']
            self.stdout.write(
                f'{c["app_legacy"]}.{c["modelo_legacy"]} '
                f'(estado={estado or "todos"}): {c["total"]}'
            )
        self.stdout.write(self.style.SUCCESS(f'Total: {gran_total}'))
