# Generated manually for the controlled and auditable SIM-2027 migration.
import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


APPEND_ONLY_FORWARD = """
CREATE OR REPLACE FUNCTION codificacion_rechazar_cambio_auditoria_sim()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION
        'SIM migration audit tables are append-only; UPDATE and DELETE are forbidden'
        USING ERRCODE = '55000';
END;
$$;

CREATE TRIGGER codificacion_ejecucionmigracionsim_append_only
BEFORE UPDATE OR DELETE ON codificacion_ejecucionmigracionsim
FOR EACH ROW EXECUTE FUNCTION codificacion_rechazar_cambio_auditoria_sim();

CREATE TRIGGER codificacion_mapeolineamientopadlegacy_append_only
BEFORE UPDATE OR DELETE ON codificacion_mapeolineamientopadlegacy
FOR EACH ROW EXECUTE FUNCTION codificacion_rechazar_cambio_auditoria_sim();
"""

APPEND_ONLY_REVERSE = """
DROP TRIGGER IF EXISTS codificacion_ejecucionmigracionsim_append_only
ON codificacion_ejecucionmigracionsim;
DROP TRIGGER IF EXISTS codificacion_mapeolineamientopadlegacy_append_only
ON codificacion_mapeolineamientopadlegacy;
DROP FUNCTION IF EXISTS codificacion_rechazar_cambio_auditoria_sim();
"""


class Migration(migrations.Migration):
    dependencies = [
        ('codificacion', '0009_fuente_normativa_e_idempotencia'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='EjecucionMigracionSIM',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('gestion', models.PositiveIntegerField(verbose_name='Gestión')),
                ('modo', models.CharField(choices=[('dry_run', 'Dry run'), ('commit', 'Commit')], max_length=20)),
                ('manifest_hash', models.CharField(db_index=True, max_length=64)),
                ('manifest', models.JSONField()),
                ('cambios_planificados', models.PositiveIntegerField(default=0)),
                ('cambios_aplicados', models.PositiveIntegerField(default=0)),
                ('homologaciones_creadas', models.PositiveIntegerField(default=0)),
                ('mapeos_lineamiento_creados', models.PositiveIntegerField(default=0)),
                ('warnings', models.PositiveIntegerField(default=0)),
                ('backup_path', models.CharField(blank=True, default='', max_length=500)),
                ('backup_sha256', models.CharField(blank=True, default='', max_length=64)),
                ('backup_restore_validated', models.BooleanField(default=False)),
                ('usuario', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='ejecuciones_migracion_sim', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['gestion', 'modo'], name='codificacio_gestion_382231_idx')],
            },
        ),
        migrations.CreateModel(
            name='MapeoLineamientoPADLegacy',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('origen', models.CharField(choices=[('pad.LineamientoEstrategico', 'PAD legacy'), ('articulacion.LineamientoPAD', 'Articulación legacy')], max_length=50)),
                ('legacy_id', models.CharField(help_text='PK de la fila legacy en forma de string: UUID para articulacion.LineamientoPAD, string de entero para pad.LineamientoEstrategico.', max_length=64)),
                ('codigo_legacy', models.CharField(max_length=100)),
                ('denominacion_legacy', models.TextField()),
                ('manifest_hash', models.CharField(blank=True, default='', max_length=64)),
                ('lineamiento_pad', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='mapeos_legacy', to='codificacion.lineamientopad')),
                ('usuario', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='mapeos_lineamiento_pad_legacy', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['origen', 'codigo_legacy'],
                'indexes': [models.Index(fields=['lineamiento_pad'], name='codificacio_lineami_eab765_idx')],
                'constraints': [models.UniqueConstraint(fields=('origen', 'legacy_id'), name='uniq_mapeo_lineamiento_pad_legacy')],
            },
        ),
        migrations.RunSQL(
            sql=APPEND_ONLY_FORWARD,
            reverse_sql=APPEND_ONLY_REVERSE,
        ),
    ]
