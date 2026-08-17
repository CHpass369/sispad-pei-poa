# PIP-DB-003: catalogos — gestion (año int) → FK GestionFiscal (UUID).
# CatalogoBase (abstracto) materializa en 13 subclases + VersionClasificador + VersionCatalogo.
# Secuencia Add→RunPython→Remove→Rename→Alter con re-alineación de Meta por paso.

import django.db.models.deletion
from django.db import migrations, models

MODELOS_CON_DATOS = ['VersionClasificador', 'FuenteFinanciamiento', 'OrganismoFinanciador', 'UnidadMedida', 'RubroRecurso', 'TipoProducto', 'TipoProyecto', 'TipoFinanciamiento', 'TipoOperacion', 'FinalidadFuncion']


def mapear_gestion_anio_a_uuid(apps, schema_editor):
    GestionFiscal = apps.get_model('gestion', 'GestionFiscal')
    por_anio = {gf.anio: gf.pk for gf in GestionFiscal.objects.all()}
    for modelo in MODELOS_CON_DATOS:
        M = apps.get_model('catalogos', modelo)
        for fila in M.objects.all().order_by():
            if not hasattr(fila, 'gestion') or not hasattr(fila, 'gestion_fk_id'):
                continue
            pk = por_anio.get(int(fila.gestion))
            if pk is None:
                # Las gestiones de los seeds están materializadas por
                # gestion.0003 (PIP-DB-003); en producción viven en la canónica.
                raise ValueError(f'{modelo} {fila.pk}: gestión {fila.gestion} sin GestionFiscal (PIP-DB-003).')
            fila.gestion_fk_id = pk
            fila.save(update_fields=['gestion_fk'])


def revertir_gestion_uuid_a_anio(apps, schema_editor):
    GestionFiscal = apps.get_model('gestion', 'GestionFiscal')
    por_pk = {gf.pk: gf.anio for gf in GestionFiscal.objects.all()}
    for modelo in MODELOS_CON_DATOS:
        M = apps.get_model('catalogos', modelo)
        for fila in M.objects.all().order_by():
            if not hasattr(fila, 'gestion_fk_id') or not hasattr(fila, 'gestion'):
                continue
            if fila.gestion_fk_id is None:
                continue
            fila.gestion = por_pk.get(fila.gestion_fk_id)
            fila.save(update_fields=['gestion'])


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0003_crear_gestiones_seed'),
        ('catalogos', '0006_sectoreconomicopresupuestario_validacionplataforma'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='versionclasificador',
            options={'ordering': ['tipo', '-gestion_fk', '-fecha_norma']},
        ),
        migrations.AddField(
            model_name='versionclasificador',
            name='gestion_fk',
            field=models.ForeignKey(db_column='gestion_fk', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión'),
        ),
        migrations.RemoveConstraint(
            model_name='versionclasificador',
            name='uniq_clasificador_vigente_tipo_gestion',
        ),
        migrations.AddConstraint(
            model_name='versionclasificador',
            constraint=models.UniqueConstraint(fields=['tipo', 'gestion_fk'], condition=models.Q(('vigente', True)), name='uniq_clasificador_vigente_tipo_gestion'),
        ),
        migrations.AlterModelOptions(
            name='fuentefinanciamiento',
            options={'ordering': ['codigo', 'gestion_fk']},
        ),
        migrations.AddField(
            model_name='fuentefinanciamiento',
            name='gestion_fk',
            field=models.ForeignKey(db_column='gestion_fk', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión'),
        ),
        migrations.AlterUniqueTogether(
            name='fuentefinanciamiento',
            unique_together={('codigo', 'gestion_fk')},
        ),
        migrations.AlterModelOptions(
            name='organismofinanciador',
            options={'ordering': ['codigo', 'gestion_fk']},
        ),
        migrations.AddField(
            model_name='organismofinanciador',
            name='gestion_fk',
            field=models.ForeignKey(db_column='gestion_fk', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión'),
        ),
        migrations.AlterUniqueTogether(
            name='organismofinanciador',
            unique_together={('codigo', 'gestion_fk')},
        ),
        migrations.AlterModelOptions(
            name='unidadmedida',
            options={'ordering': ['codigo', 'gestion_fk']},
        ),
        migrations.AddField(
            model_name='unidadmedida',
            name='gestion_fk',
            field=models.ForeignKey(db_column='gestion_fk', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión'),
        ),
        migrations.AlterUniqueTogether(
            name='unidadmedida',
            unique_together={('codigo', 'gestion_fk')},
        ),
        migrations.AlterModelOptions(
            name='rubrorecurso',
            options={'ordering': ['codigo', 'gestion_fk']},
        ),
        migrations.AddField(
            model_name='rubrorecurso',
            name='gestion_fk',
            field=models.ForeignKey(db_column='gestion_fk', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión'),
        ),
        migrations.AlterUniqueTogether(
            name='rubrorecurso',
            unique_together={('codigo', 'gestion_fk')},
        ),
        migrations.AlterModelOptions(
            name='tipoproducto',
            options={'ordering': ['codigo', 'gestion_fk']},
        ),
        migrations.AddField(
            model_name='tipoproducto',
            name='gestion_fk',
            field=models.ForeignKey(db_column='gestion_fk', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión'),
        ),
        migrations.AlterUniqueTogether(
            name='tipoproducto',
            unique_together={('codigo', 'gestion_fk')},
        ),
        migrations.AlterModelOptions(
            name='tipoproyecto',
            options={'ordering': ['codigo', 'gestion_fk']},
        ),
        migrations.AddField(
            model_name='tipoproyecto',
            name='gestion_fk',
            field=models.ForeignKey(db_column='gestion_fk', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión'),
        ),
        migrations.AlterUniqueTogether(
            name='tipoproyecto',
            unique_together={('codigo', 'gestion_fk')},
        ),
        migrations.AlterModelOptions(
            name='tipofinanciamiento',
            options={'ordering': ['codigo', 'gestion_fk']},
        ),
        migrations.AddField(
            model_name='tipofinanciamiento',
            name='gestion_fk',
            field=models.ForeignKey(db_column='gestion_fk', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión'),
        ),
        migrations.AlterUniqueTogether(
            name='tipofinanciamiento',
            unique_together={('codigo', 'gestion_fk')},
        ),
        migrations.AlterModelOptions(
            name='tipooperacion',
            options={'ordering': ['codigo', 'gestion_fk']},
        ),
        migrations.AddField(
            model_name='tipooperacion',
            name='gestion_fk',
            field=models.ForeignKey(db_column='gestion_fk', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión'),
        ),
        migrations.AlterUniqueTogether(
            name='tipooperacion',
            unique_together={('codigo', 'gestion_fk')},
        ),
        migrations.AlterModelOptions(
            name='finalidadfuncion',
            options={'ordering': ['codigo', 'gestion_fk']},
        ),
        migrations.AddField(
            model_name='finalidadfuncion',
            name='gestion_fk',
            field=models.ForeignKey(db_column='gestion_fk', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión'),
        ),
        migrations.AlterUniqueTogether(
            name='finalidadfuncion',
            unique_together={('codigo', 'gestion_fk')},
        ),
        migrations.AlterModelOptions(
            name='clasificadorinstitucional',
            options={'ordering': ['codigo', 'gestion_fk']},
        ),
        migrations.AddField(
            model_name='clasificadorinstitucional',
            name='gestion_fk',
            field=models.ForeignKey(db_column='gestion_fk', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión'),
        ),
        migrations.AlterUniqueTogether(
            name='clasificadorinstitucional',
            unique_together={('codigo', 'gestion_fk')},
        ),
        migrations.AlterModelOptions(
            name='objetogasto',
            options={'ordering': ['codigo', 'gestion_fk']},
        ),
        migrations.AddField(
            model_name='objetogasto',
            name='gestion_fk',
            field=models.ForeignKey(db_column='gestion_fk', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión'),
        ),
        migrations.AlterUniqueTogether(
            name='objetogasto',
            unique_together={('codigo', 'gestion_fk')},
        ),
        migrations.AlterModelOptions(
            name='entidadtransferencia',
            options={'ordering': ['codigo', 'gestion_fk']},
        ),
        migrations.AddField(
            model_name='entidadtransferencia',
            name='gestion_fk',
            field=models.ForeignKey(db_column='gestion_fk', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión'),
        ),
        migrations.AlterUniqueTogether(
            name='entidadtransferencia',
            unique_together={('codigo', 'gestion_fk')},
        ),
        migrations.AlterModelOptions(
            name='sectoreconomicopresupuestario',
            options={'ordering': ['codigo', 'gestion_fk']},
        ),
        migrations.AddField(
            model_name='sectoreconomicopresupuestario',
            name='gestion_fk',
            field=models.ForeignKey(db_column='gestion_fk', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión'),
        ),
        migrations.AlterUniqueTogether(
            name='sectoreconomicopresupuestario',
            unique_together={('codigo', 'gestion_fk')},
        ),
        migrations.AlterModelOptions(
            name='versioncatalogo',
            options={'ordering': ['-gestion_fk', '-creado_en']},
        ),
        migrations.AddField(
            model_name='versioncatalogo',
            name='gestion_fk',
            field=models.ForeignKey(db_column='gestion_fk', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión'),
        ),
        migrations.RunPython(mapear_gestion_anio_a_uuid, revertir_gestion_uuid_a_anio),
        migrations.AlterField(
            model_name='versionclasificador',
            name='gestion',
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.RemoveField(model_name='versionclasificador', name='gestion'),
        migrations.AlterField(
            model_name='fuentefinanciamiento',
            name='gestion',
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.RemoveField(model_name='fuentefinanciamiento', name='gestion'),
        migrations.AlterField(
            model_name='organismofinanciador',
            name='gestion',
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.RemoveField(model_name='organismofinanciador', name='gestion'),
        migrations.AlterField(
            model_name='unidadmedida',
            name='gestion',
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.RemoveField(model_name='unidadmedida', name='gestion'),
        migrations.AlterField(
            model_name='rubrorecurso',
            name='gestion',
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.RemoveField(model_name='rubrorecurso', name='gestion'),
        migrations.AlterField(
            model_name='tipoproducto',
            name='gestion',
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.RemoveField(model_name='tipoproducto', name='gestion'),
        migrations.AlterField(
            model_name='tipoproyecto',
            name='gestion',
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.RemoveField(model_name='tipoproyecto', name='gestion'),
        migrations.AlterField(
            model_name='tipofinanciamiento',
            name='gestion',
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.RemoveField(model_name='tipofinanciamiento', name='gestion'),
        migrations.AlterField(
            model_name='tipooperacion',
            name='gestion',
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.RemoveField(model_name='tipooperacion', name='gestion'),
        migrations.AlterField(
            model_name='finalidadfuncion',
            name='gestion',
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.RemoveField(model_name='finalidadfuncion', name='gestion'),
        migrations.AlterField(
            model_name='clasificadorinstitucional',
            name='gestion',
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.RemoveField(model_name='clasificadorinstitucional', name='gestion'),
        migrations.AlterField(
            model_name='objetogasto',
            name='gestion',
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.RemoveField(model_name='objetogasto', name='gestion'),
        migrations.AlterField(
            model_name='entidadtransferencia',
            name='gestion',
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.RemoveField(model_name='entidadtransferencia', name='gestion'),
        migrations.AlterField(
            model_name='sectoreconomicopresupuestario',
            name='gestion',
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.RemoveField(model_name='sectoreconomicopresupuestario', name='gestion'),
        migrations.AlterField(
            model_name='versioncatalogo',
            name='gestion',
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.RemoveField(model_name='versioncatalogo', name='gestion'),
        migrations.RenameField(model_name='versionclasificador', old_name='gestion_fk', new_name='gestion'),
        migrations.RenameField(model_name='fuentefinanciamiento', old_name='gestion_fk', new_name='gestion'),
        migrations.RenameField(model_name='organismofinanciador', old_name='gestion_fk', new_name='gestion'),
        migrations.RenameField(model_name='unidadmedida', old_name='gestion_fk', new_name='gestion'),
        migrations.RenameField(model_name='rubrorecurso', old_name='gestion_fk', new_name='gestion'),
        migrations.RenameField(model_name='tipoproducto', old_name='gestion_fk', new_name='gestion'),
        migrations.RenameField(model_name='tipoproyecto', old_name='gestion_fk', new_name='gestion'),
        migrations.RenameField(model_name='tipofinanciamiento', old_name='gestion_fk', new_name='gestion'),
        migrations.RenameField(model_name='tipooperacion', old_name='gestion_fk', new_name='gestion'),
        migrations.RenameField(model_name='finalidadfuncion', old_name='gestion_fk', new_name='gestion'),
        migrations.RenameField(model_name='clasificadorinstitucional', old_name='gestion_fk', new_name='gestion'),
        migrations.RenameField(model_name='objetogasto', old_name='gestion_fk', new_name='gestion'),
        migrations.RenameField(model_name='entidadtransferencia', old_name='gestion_fk', new_name='gestion'),
        migrations.RenameField(model_name='sectoreconomicopresupuestario', old_name='gestion_fk', new_name='gestion'),
        migrations.RenameField(model_name='versioncatalogo', old_name='gestion_fk', new_name='gestion'),
        migrations.AlterModelOptions(
            name='versionclasificador',
            options={'ordering': ['tipo', '-gestion__anio', '-fecha_norma']},
        ),
        migrations.RemoveConstraint(
            model_name='versionclasificador',
            name='uniq_clasificador_vigente_tipo_gestion',
        ),
        migrations.AddConstraint(
            model_name='versionclasificador',
            constraint=models.UniqueConstraint(fields=['tipo', 'gestion'], condition=models.Q(('vigente', True)), name='uniq_clasificador_vigente_tipo_gestion'),
        ),
        migrations.AlterField(
            model_name='versionclasificador',
            name='gestion',
            field=models.ForeignKey(db_column='gestion', on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión'),
        ),
        migrations.AlterModelOptions(
            name='fuentefinanciamiento',
            options={'ordering': ['codigo', 'gestion__anio']},
        ),
        migrations.AlterUniqueTogether(
            name='fuentefinanciamiento',
            unique_together={('codigo', 'gestion')},
        ),
        migrations.AlterField(
            model_name='fuentefinanciamiento',
            name='gestion',
            field=models.ForeignKey(db_column='gestion', on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión'),
        ),
        migrations.AlterModelOptions(
            name='organismofinanciador',
            options={'ordering': ['codigo', 'gestion__anio']},
        ),
        migrations.AlterUniqueTogether(
            name='organismofinanciador',
            unique_together={('codigo', 'gestion')},
        ),
        migrations.AlterField(
            model_name='organismofinanciador',
            name='gestion',
            field=models.ForeignKey(db_column='gestion', on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión'),
        ),
        migrations.AlterModelOptions(
            name='unidadmedida',
            options={'ordering': ['codigo', 'gestion__anio']},
        ),
        migrations.AlterUniqueTogether(
            name='unidadmedida',
            unique_together={('codigo', 'gestion')},
        ),
        migrations.AlterField(
            model_name='unidadmedida',
            name='gestion',
            field=models.ForeignKey(db_column='gestion', on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión'),
        ),
        migrations.AlterModelOptions(
            name='rubrorecurso',
            options={'ordering': ['codigo', 'gestion__anio']},
        ),
        migrations.AlterUniqueTogether(
            name='rubrorecurso',
            unique_together={('codigo', 'gestion')},
        ),
        migrations.AlterField(
            model_name='rubrorecurso',
            name='gestion',
            field=models.ForeignKey(db_column='gestion', on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión'),
        ),
        migrations.AlterModelOptions(
            name='tipoproducto',
            options={'ordering': ['codigo', 'gestion__anio']},
        ),
        migrations.AlterUniqueTogether(
            name='tipoproducto',
            unique_together={('codigo', 'gestion')},
        ),
        migrations.AlterField(
            model_name='tipoproducto',
            name='gestion',
            field=models.ForeignKey(db_column='gestion', on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión'),
        ),
        migrations.AlterModelOptions(
            name='tipoproyecto',
            options={'ordering': ['codigo', 'gestion__anio']},
        ),
        migrations.AlterUniqueTogether(
            name='tipoproyecto',
            unique_together={('codigo', 'gestion')},
        ),
        migrations.AlterField(
            model_name='tipoproyecto',
            name='gestion',
            field=models.ForeignKey(db_column='gestion', on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión'),
        ),
        migrations.AlterModelOptions(
            name='tipofinanciamiento',
            options={'ordering': ['codigo', 'gestion__anio']},
        ),
        migrations.AlterUniqueTogether(
            name='tipofinanciamiento',
            unique_together={('codigo', 'gestion')},
        ),
        migrations.AlterField(
            model_name='tipofinanciamiento',
            name='gestion',
            field=models.ForeignKey(db_column='gestion', on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión'),
        ),
        migrations.AlterModelOptions(
            name='tipooperacion',
            options={'ordering': ['codigo', 'gestion__anio']},
        ),
        migrations.AlterUniqueTogether(
            name='tipooperacion',
            unique_together={('codigo', 'gestion')},
        ),
        migrations.AlterField(
            model_name='tipooperacion',
            name='gestion',
            field=models.ForeignKey(db_column='gestion', on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión'),
        ),
        migrations.AlterModelOptions(
            name='finalidadfuncion',
            options={'ordering': ['codigo', 'gestion__anio']},
        ),
        migrations.AlterUniqueTogether(
            name='finalidadfuncion',
            unique_together={('codigo', 'gestion')},
        ),
        migrations.AlterField(
            model_name='finalidadfuncion',
            name='gestion',
            field=models.ForeignKey(db_column='gestion', on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión'),
        ),
        migrations.AlterModelOptions(
            name='clasificadorinstitucional',
            options={'ordering': ['codigo', 'gestion__anio']},
        ),
        migrations.AlterUniqueTogether(
            name='clasificadorinstitucional',
            unique_together={('codigo', 'gestion')},
        ),
        migrations.AlterField(
            model_name='clasificadorinstitucional',
            name='gestion',
            field=models.ForeignKey(db_column='gestion', on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión'),
        ),
        migrations.AlterModelOptions(
            name='objetogasto',
            options={'ordering': ['codigo', 'gestion__anio']},
        ),
        migrations.AlterUniqueTogether(
            name='objetogasto',
            unique_together={('codigo', 'gestion')},
        ),
        migrations.AlterField(
            model_name='objetogasto',
            name='gestion',
            field=models.ForeignKey(db_column='gestion', on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión'),
        ),
        migrations.AlterModelOptions(
            name='entidadtransferencia',
            options={'ordering': ['codigo', 'gestion__anio']},
        ),
        migrations.AlterUniqueTogether(
            name='entidadtransferencia',
            unique_together={('codigo', 'gestion')},
        ),
        migrations.AlterField(
            model_name='entidadtransferencia',
            name='gestion',
            field=models.ForeignKey(db_column='gestion', on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión'),
        ),
        migrations.AlterModelOptions(
            name='sectoreconomicopresupuestario',
            options={'ordering': ['codigo', 'gestion__anio']},
        ),
        migrations.AlterUniqueTogether(
            name='sectoreconomicopresupuestario',
            unique_together={('codigo', 'gestion')},
        ),
        migrations.AlterField(
            model_name='sectoreconomicopresupuestario',
            name='gestion',
            field=models.ForeignKey(db_column='gestion', on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión'),
        ),
        migrations.AlterModelOptions(
            name='versioncatalogo',
            options={'ordering': ['-gestion__anio', '-creado_en']},
        ),
        migrations.AlterField(
            model_name='versioncatalogo',
            name='gestion',
            field=models.ForeignKey(db_column='gestion', on_delete=django.db.models.deletion.PROTECT, related_name='+', to='gestion.gestionfiscal', verbose_name='Gestión'),
        ),
    ]
