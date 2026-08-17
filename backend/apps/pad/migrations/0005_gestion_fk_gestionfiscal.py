# PIP-DB-004: pad — gestion (año int) → FK GestionFiscal (UUID) en 5 modelos
# con 1 fila cada uno (2027 válida) + ProgramacionAnualPAD.anio → gestion (FK).
# Secuencia: re-alinear Meta (unique/ordering/index a gestion_fk) → Add →
# RunPython → Remove → Rename → re-alinear Meta a gestion → Alter final.
# PostgreSQL no castea int→uuid en ALTER COLUMN TYPE.

import django.db.models.deletion
from django.db import migrations, models

MODELOS_CON_DATOS = (
    'PoliticaPAD',
    'LineamientoEstrategico',
    'ResultadoTerritorial',
    'ProductoTerritorial',
    'ArticulacionSIPEB',
)


def mapear_gestion_anio_a_uuid(apps, schema_editor):
    GestionFiscal = apps.get_model('gestion', 'GestionFiscal')
    por_anio = {gf.anio: gf.pk for gf in GestionFiscal.objects.all()}
    for modelo in MODELOS_CON_DATOS:
        M = apps.get_model('pad', modelo)
        for fila in M.objects.all().order_by():
            pk = por_anio.get(int(fila.gestion))
            if pk is None:
                raise ValueError(
                    f'{modelo} {fila.pk}: gestión {fila.gestion} sin '
                    f'GestionFiscal (no se inventan gestiones — PIP-DB-004).'
                )
            fila.gestion_fk_id = pk
            fila.save(update_fields=['gestion_fk'])


def revertir_gestion_uuid_a_anio(apps, schema_editor):
    GestionFiscal = apps.get_model('gestion', 'GestionFiscal')
    por_pk = {gf.pk: gf.anio for gf in GestionFiscal.objects.all()}
    for modelo in MODELOS_CON_DATOS:
        M = apps.get_model('pad', modelo)
        for fila in M.objects.all().order_by():
            if fila.gestion_fk_id is None:
                continue
            fila.gestion = por_pk.get(fila.gestion_fk_id)
            fila.save(update_fields=['gestion'])


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0002_alter_gestionfiscal_estado'),
        ('pad', '0004_migrar_programaciones'),
    ]

    operations = [
        # --- AddField primero; los Alter* con gestion_fk van después ---
        migrations.AddField(
            model_name='articulacionsipeb',
            name='gestion_fk',
            field=models.ForeignKey(db_column='gestion_fk', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión'),
        ),
        migrations.AddField(
            model_name='lineamientoestrategico',
            name='gestion_fk',
            field=models.ForeignKey(db_column='gestion_fk', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión'),
        ),
        migrations.AddField(
            model_name='politicapad',
            name='gestion_fk',
            field=models.ForeignKey(db_column='gestion_fk', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión'),
        ),
        migrations.AddField(
            model_name='productoterritorial',
            name='gestion_fk',
            field=models.ForeignKey(db_column='gestion_fk', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión'),
        ),
        migrations.AddField(
            model_name='resultadoterritorial',
            name='gestion_fk',
            field=models.ForeignKey(db_column='gestion_fk', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión'),
        ),
        # --- Re-alinear Meta a gestion_fk (campo viejo se removerá) ---
        migrations.AlterModelOptions(
            name='articulacionsipeb',
            options={'ordering': ['gestion_fk', 'resultado'], 'verbose_name': 'Articulación SIPEB', 'verbose_name_plural': 'Articulaciones SIPEB'},
        ),
        migrations.AlterModelOptions(
            name='lineamientoestrategico',
            options={'ordering': ['gestion_fk', 'codigo'], 'verbose_name': 'Lineamiento estratégico', 'verbose_name_plural': 'Lineamientos estratégicos'},
        ),
        migrations.AlterModelOptions(
            name='politicapad',
            options={'ordering': ['gestion_fk', 'codigo'], 'verbose_name': 'Política PAD', 'verbose_name_plural': 'Políticas PAD'},
        ),
        migrations.AlterModelOptions(
            name='productoterritorial',
            options={'ordering': ['gestion_fk', 'codigo'], 'verbose_name': 'Producto territorial', 'verbose_name_plural': 'Productos territoriales'},
        ),
        migrations.AlterModelOptions(
            name='resultadoterritorial',
            options={'ordering': ['gestion_fk', 'codigo'], 'verbose_name': 'Resultado territorial', 'verbose_name_plural': 'Resultados territoriales'},
        ),
        migrations.AlterUniqueTogether(
            name='lineamientoestrategico',
            unique_together={('codigo', 'politica', 'gestion_fk')},
        ),
        migrations.AlterUniqueTogether(
            name='politicapad',
            unique_together={('codigo', 'gestion_fk')},
        ),
        migrations.AlterUniqueTogether(
            name='productoterritorial',
            unique_together={('codigo', 'resultado', 'gestion_fk')},
        ),
        migrations.AlterUniqueTogether(
            name='resultadoterritorial',
            unique_together={('codigo', 'lineamiento', 'gestion_fk')},
        ),
        migrations.AlterIndexTogether(
            name='resultadoterritorial',
            index_together=set(),
        ),
        migrations.RunPython(mapear_gestion_anio_a_uuid, revertir_gestion_uuid_a_anio),
        migrations.RemoveField(model_name='articulacionsipeb', name='gestion'),
        migrations.RemoveField(model_name='lineamientoestrategico', name='gestion'),
        migrations.RemoveField(model_name='politicapad', name='gestion'),
        migrations.RemoveField(model_name='productoterritorial', name='gestion'),
        migrations.RemoveField(model_name='resultadoterritorial', name='gestion'),
        migrations.RenameField(model_name='articulacionsipeb', old_name='gestion_fk', new_name='gestion'),
        migrations.RenameField(model_name='lineamientoestrategico', old_name='gestion_fk', new_name='gestion'),
        migrations.RenameField(model_name='politicapad', old_name='gestion_fk', new_name='gestion'),
        migrations.RenameField(model_name='productoterritorial', old_name='gestion_fk', new_name='gestion'),
        migrations.RenameField(model_name='resultadoterritorial', old_name='gestion_fk', new_name='gestion'),
        # --- Re-alinear Meta a gestion (estado final del modelo) ---
        migrations.AlterModelOptions(
            name='articulacionsipeb',
            options={'ordering': ['gestion__anio', 'resultado'], 'verbose_name': 'Articulación SIPEB', 'verbose_name_plural': 'Articulaciones SIPEB'},
        ),
        migrations.AlterModelOptions(
            name='lineamientoestrategico',
            options={'ordering': ['gestion__anio', 'codigo'], 'verbose_name': 'Lineamiento estratégico', 'verbose_name_plural': 'Lineamientos estratégicos'},
        ),
        migrations.AlterModelOptions(
            name='politicapad',
            options={'ordering': ['gestion__anio', 'codigo'], 'verbose_name': 'Política PAD', 'verbose_name_plural': 'Políticas PAD'},
        ),
        migrations.AlterModelOptions(
            name='productoterritorial',
            options={'ordering': ['gestion__anio', 'codigo'], 'verbose_name': 'Producto territorial', 'verbose_name_plural': 'Productos territoriales'},
        ),
        migrations.AlterModelOptions(
            name='resultadoterritorial',
            options={'ordering': ['gestion__anio', 'codigo'], 'verbose_name': 'Resultado territorial', 'verbose_name_plural': 'Resultados territoriales'},
        ),
        migrations.AlterUniqueTogether(
            name='lineamientoestrategico',
            unique_together={('codigo', 'politica', 'gestion')},
        ),
        migrations.AlterUniqueTogether(
            name='politicapad',
            unique_together={('codigo', 'gestion')},
        ),
        migrations.AlterUniqueTogether(
            name='productoterritorial',
            unique_together={('codigo', 'resultado', 'gestion')},
        ),
        migrations.AlterUniqueTogether(
            name='resultadoterritorial',
            unique_together={('codigo', 'lineamiento', 'gestion')},
        ),
        migrations.AlterField(
            model_name='articulacionsipeb',
            name='gestion',
            field=models.ForeignKey(db_column='gestion', on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión'),
        ),
        migrations.AlterField(
            model_name='lineamientoestrategico',
            name='gestion',
            field=models.ForeignKey(db_column='gestion', on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión'),
        ),
        migrations.AlterField(
            model_name='politicapad',
            name='gestion',
            field=models.ForeignKey(db_column='gestion', on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión'),
        ),
        migrations.AlterField(
            model_name='productoterritorial',
            name='gestion',
            field=models.ForeignKey(db_column='gestion', on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión'),
        ),
        migrations.AlterField(
            model_name='resultadoterritorial',
            name='gestion',
            field=models.ForeignKey(db_column='gestion', on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión'),
        ),
        # --- ProgramacionAnualPAD (tabla vacía): anio → gestion (FK) ---
        migrations.AddField(
            model_name='programacionanualpad',
            name='gestion_fk',
            field=models.ForeignKey(db_column='gestion_fk', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión'),
        ),
        migrations.AlterUniqueTogether(
            name='programacionanualpad',
            unique_together={('resultado', 'producto', 'gestion_fk', 'tipo')},
        ),
        migrations.RemoveField(model_name='programacionanualpad', name='anio'),
        migrations.RenameField(model_name='programacionanualpad', old_name='gestion_fk', new_name='gestion'),
        migrations.AlterUniqueTogether(
            name='programacionanualpad',
            unique_together={('resultado', 'producto', 'gestion', 'tipo')},
        ),
        migrations.AlterField(
            model_name='programacionanualpad',
            name='gestion',
            field=models.ForeignKey(db_column='gestion', on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión'),
        ),
    ]