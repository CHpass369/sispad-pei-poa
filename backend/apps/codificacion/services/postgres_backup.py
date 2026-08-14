"""Create a PostgreSQL custom dump and prove it by restoring a temporary DB."""
from __future__ import annotations

import hashlib
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from django.conf import settings


class PostgresBackupService:
    """Fail-closed backup service used immediately before the SIM commit."""

    SAFE_TABLES = {
        'articulacion_resultadopad',
        'articulacion_productopad',
        'articulacion_resultadopei',
        'articulacion_productopei',
        'articulacion_accionpoa',
        'articulacion_operacionpoau',
        'articulacion_actividadpoau',
        'articulacion_tareapoau',
    }

    @classmethod
    def _connection(cls, database=None):
        config = settings.DATABASES['default']
        return {
            'host': config.get('HOST') or 'localhost',
            'port': str(config.get('PORT') or '5432'),
            'user': config['USER'],
            'database': database or config['NAME'],
            'password': config.get('PASSWORD') or '',
        }

    @staticmethod
    def _environment(connection):
        env = os.environ.copy()
        env['PGPASSWORD'] = connection['password']
        return env

    @classmethod
    def _base_args(cls, connection):
        return [
            '--host', connection['host'],
            '--port', connection['port'],
            '--username', connection['user'],
        ]

    @classmethod
    def _run(cls, args, connection, **kwargs):
        return subprocess.run(
            args,
            env=cls._environment(connection),
            check=True,
            text=True,
            capture_output=True,
            **kwargs,
        )

    @classmethod
    def _validate_counts(cls, database, expected):
        connection = cls._connection(database)
        actual = {}
        for table, expected_count in expected.items():
            if table not in cls.SAFE_TABLES:
                raise RuntimeError(f'Tabla no permitida para validación: {table}')
            result = cls._run(
                [
                    'psql', *cls._base_args(connection),
                    '--dbname', database,
                    '--tuples-only', '--no-align',
                    '--command', f'SELECT count(*) FROM {table};',
                ],
                connection,
            )
            actual[table] = int(result.stdout.strip())
            if actual[table] != expected_count:
                raise RuntimeError(
                    f'Conteo restaurado inválido para {table}: '
                    f'{actual[table]} != {expected_count}',
                )
        return actual

    @classmethod
    def create_and_validate(cls, *, output_dir, validation_queries):
        output_dir = Path(output_dir).resolve()
        output_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        path = output_dir / f'sispoa_pre_t5_{timestamp}_{os.getpid()}.dump'
        source = cls._connection()
        temporary_database = f't5_restore_{timestamp.lower()}_{os.getpid()}'

        cls._run(
            [
                'pg_dump', *cls._base_args(source),
                '--dbname', source['database'],
                '--format', 'custom',
                '--compress', '9',
                '--no-owner', '--no-acl',
                '--file', str(path),
            ],
            source,
        )
        os.chmod(path, 0o600)
        cls._run(['pg_restore', '--list', str(path)], source)

        restored_counts = None
        try:
            cls._run(
                [
                    'createdb', *cls._base_args(source),
                    '--template', 'template0',
                    temporary_database,
                ],
                source,
            )
            temporary = cls._connection(temporary_database)
            cls._run(
                [
                    'pg_restore', *cls._base_args(temporary),
                    '--dbname', temporary_database,
                    '--exit-on-error', '--no-owner', '--no-acl',
                    str(path),
                ],
                temporary,
            )
            restored_counts = cls._validate_counts(
                temporary_database, validation_queries,
            )
        finally:
            cls._run(
                [
                    'dropdb', *cls._base_args(source),
                    '--if-exists', '--force', temporary_database,
                ],
                source,
            )

        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        return {
            'path': str(path),
            'sha256': digest,
            'restore_validated': True,
            'validated_counts': restored_counts,
        }
