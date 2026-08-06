"""Audit or commit the controlled SIM-2027 provisional-code migration."""
import json
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from apps.codificacion.services.migracion_sim import MigracionSIMService
from apps.codificacion.services.postgres_backup import PostgresBackupService


class Command(BaseCommand):
    help = 'Audita o migra códigos SIM a correlativos numéricos PROVISIONALES.'

    def add_arguments(self, parser):
        parser.add_argument('--gestion', type=int, default=2027)
        parser.add_argument('--manifest')
        parser.add_argument('--commit', action='store_true')
        parser.add_argument('--expected-hash')
        parser.add_argument('--usuario')
        parser.add_argument('--backup-dir')

    def handle(self, *args, **options):
        gestion = options['gestion']
        manifest_path = options.get('manifest')
        if not options['commit']:
            service = MigracionSIMService(gestion=gestion)
            manifest = service.auditar()
            path = Path(manifest_path) if manifest_path else Path(
                'backups/t5/manifests'
            ) / f"sim-{gestion}-{manifest['manifest_hash']}.json"
            service.persistir_manifiesto(manifest, path)
            self.stdout.write(json.dumps({
                'mode': 'dry_run',
                'manifest': str(path.resolve()),
                'manifest_hash': manifest['manifest_hash'],
                **manifest['resumen'],
            }, ensure_ascii=False, sort_keys=True))
            return

        missing = [
            name for name in ('expected_hash', 'usuario', 'backup_dir')
            if not options.get(name)
        ]
        if missing:
            labels = ', '.join(name.replace('_', '-') for name in missing)
            raise CommandError(f'Commit requiere: {labels}.')

        user = get_user_model().objects.filter(
            email__iexact=options['usuario'], is_active=True,
        ).first()
        if user is None:
            raise CommandError('No existe un usuario activo con ese correo.')
        service = MigracionSIMService(gestion=gestion, usuario=user)
        manifest = service.construir_manifiesto()
        if manifest['manifest_hash'] != options['expected_hash']:
            raise CommandError('El expected-hash no coincide con los datos actuales.')

        try:
            backup = PostgresBackupService.create_and_validate(
                output_dir=options['backup_dir'],
                validation_queries=service.snapshot_counts(),
            )
            result = service.ejecutar(
                expected_hash=options['expected_hash'],
                backup=backup,
            )
        except (RuntimeError, ValidationError) as exc:
            raise CommandError(str(exc)) from exc

        manifest['ejecucion'] = result
        manifest['backup'] = backup
        path = Path(manifest_path) if manifest_path else Path(
            'backups/t5/manifests'
        ) / f"sim-{gestion}-{manifest['manifest_hash']}-commit.json"
        service.persistir_manifiesto(manifest, path)
        self.stdout.write(json.dumps({
            'mode': 'commit',
            'manifest': str(path.resolve()),
            'backup': backup,
            **result,
        }, ensure_ascii=False, sort_keys=True))
