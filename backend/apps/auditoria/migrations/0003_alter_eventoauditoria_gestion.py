# PIP-DB-008: convierte EventoAuditoria.gestion (año int) → FK a GestionFiscal
# (UUID). Secuencia AddField → RunPython → RemoveField → RenameField → AlterField
# porque la tabla tiene 1 fila real (gestion=2027, válida). null=True conservado.

import django.db.models.deletion
from django.db import migrations, models


def mapear_gestion_anio_a_uuid(apps, schema_editor):
    GestionFiscal = apps.get_model('gestion', 'GestionFiscal')
    por_anio = {gf.anio: gf.pk for gf in GestionFiscal.objects.all()}
    EventoAuditoria = apps.get_model('auditoria', 'EventoAuditoria')
    for fila in EventoAuditoria.objects.all().order_by():
        if fila.gestion is None:
            continue
        pk = por_anio.get(int(fila.gestion))
        if pk is None:
            raise ValueError(
                f'EventoAuditoria {fila.pk}: gestión {fila.gestion} sin '
                f'GestionFiscal (no se inventan gestiones — invariante PIP-DB-008).'
            )
        fila.gestion_fk_id = pk
        fila.save(update_fields=['gestion_fk'])


def revertir_gestion_uuid_a_anio(apps, schema_editor):
    GestionFiscal = apps.get_model('gestion', 'GestionFiscal')
    por_pk = {gf.pk: gf.anio for gf in GestionFiscal.objects.all()}
    EventoAuditoria = apps.get_model('auditoria', 'EventoAuditoria')
    for fila in EventoAuditoria.objects.all().order_by():
        if fila.gestion_fk_id is None:
            continue
        fila.gestion = por_pk.get(fila.gestion_fk_id)
        fila.save(update_fields=['gestion'])


class Migration(migrations.Migration):

    dependencies = [
        ('auditoria', '0002_eventoauditoria_audit_entidad_historial_idx_and_more'),
        ('gestion', '0002_alter_gestionfiscal_estado'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventoauditoria',
            name='gestion_fk',
            field=models.ForeignKey(blank=True, db_column='gestion_fk', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión fiscal'),
        ),
        migrations.RunPython(mapear_gestion_anio_a_uuid, revertir_gestion_uuid_a_anio),
        migrations.RemoveField(
            model_name='eventoauditoria',
            name='gestion',
        ),
        migrations.RenameField(
            model_name='eventoauditoria',
            old_name='gestion_fk',
            new_name='gestion',
        ),
        migrations.AlterField(
            model_name='eventoauditoria',
            name='gestion',
            field=models.ForeignKey(blank=True, db_column='gestion', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión fiscal'),
        ),
    ]