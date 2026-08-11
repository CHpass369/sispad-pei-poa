# Generated for SIS-POA migration: adopt tables formerly managed by apps.poau.
# db_table points to the existing poau_* tables so data is preserved.

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('organizacion', '0001_initial'),
        ('planificacion', '0005_tipoinstrumento_tiponodoestrategico_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='AccionCortoPlazo',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('codigo', models.CharField(max_length=50)),
                ('nombre', models.CharField(max_length=500)),
                ('descripcion', models.TextField(blank=True, default='')),
                ('atributos', models.JSONField(blank=True, default=dict)),
                ('estado', models.CharField(choices=[('borrador', 'Borrador'), ('en_formulacion', 'En formulación'), ('en_revision', 'En revisión'), ('observado', 'Observado'), ('aprobado', 'Aprobado')], default='borrador', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('nodo_pei', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='acciones_poa', to='planificacion.nodoestrategico')),
                ('unidad', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='acciones_poa_v2', to='organizacion.unidadorganizacional')),
            ],
            options={
                'db_table': 'poau_accioncortoplazo',
                'verbose_name': 'Acción de corto plazo',
                'verbose_name_plural': 'Acciones de corto plazo',
                'ordering': ['poa', 'codigo'],
            },
        ),
        migrations.CreateModel(
            name='Operacion',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('codigo', models.CharField(max_length=50)),
                ('nombre', models.CharField(max_length=500)),
                ('atributos', models.JSONField(blank=True, default=dict)),
                ('estado', models.CharField(choices=[('borrador', 'Borrador'), ('en_formulacion', 'En formulación'), ('en_revision', 'En revisión'), ('observado', 'Observado'), ('aprobado', 'Aprobado')], default='borrador', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('accion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='operaciones', to='sis_poa.accioncortoplazo')),
                ('unidad', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='operaciones_poa', to='organizacion.unidadorganizacional')),
            ],
            options={
                'db_table': 'poau_operacion',
                'verbose_name': 'Operación',
                'verbose_name_plural': 'Operaciones',
                'ordering': ['accion', 'codigo'],
            },
        ),
        migrations.CreateModel(
            name='Actividad',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('codigo', models.CharField(max_length=50)),
                ('nombre', models.CharField(max_length=500)),
                ('atributos', models.JSONField(blank=True, default=dict)),
                ('estado', models.CharField(choices=[('borrador', 'Borrador'), ('en_formulacion', 'En formulación'), ('en_revision', 'En revisión'), ('observado', 'Observado'), ('aprobado', 'Aprobado')], default='borrador', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('operacion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='actividades', to='sis_poa.operacion')),
            ],
            options={
                'db_table': 'poau_actividad',
                'verbose_name': 'Actividad',
                'verbose_name_plural': 'Actividades',
                'ordering': ['operacion', 'codigo'],
            },
        ),
        migrations.CreateModel(
            name='PoAInstitucional',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('gestion', models.PositiveIntegerField()),
                ('codigo', models.CharField(max_length=50, unique=True)),
                ('nombre', models.CharField(max_length=300)),
                ('estado', models.CharField(choices=[('borrador', 'Borrador'), ('en_formulacion', 'En formulación'), ('en_revision', 'En revisión'), ('observado', 'Observado'), ('aprobado', 'Aprobado')], default='borrador', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('version_pei', models.ForeignKey(blank=True, help_text='Versión PEI aprobada a la que se articula (obligatoria).', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='poas', to='planificacion.versioninstrumento')),
            ],
            options={
                'db_table': 'poau_poainstitucional',
                'verbose_name': 'POA institucional',
                'verbose_name_plural': 'POAs institucionales',
                'ordering': ['gestion', 'codigo'],
            },
        ),
        migrations.AddField(
            model_name='accioncortoplazo',
            name='poa',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='acciones', to='sis_poa.poainstitucional'),
        ),
        migrations.CreateModel(
            name='ProgramacionActividad',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('anio', models.PositiveIntegerField()),
                ('tipo', models.CharField(choices=[('fisica', 'Física'), ('financiera', 'Financiera')], max_length=20)),
                ('programado', models.DecimalField(decimal_places=4, default=0, max_digits=20)),
                ('ejecutado', models.DecimalField(decimal_places=4, default=0, max_digits=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('actividad', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='programaciones', to='sis_poa.actividad')),
            ],
            options={
                'db_table': 'poau_programacionactividad',
                'verbose_name': 'Programación de actividad',
                'verbose_name_plural': 'Programaciones de actividades',
                'ordering': ['actividad', 'anio', 'tipo'],
            },
        ),
        migrations.CreateModel(
            name='Tarea',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('codigo', models.CharField(max_length=50)),
                ('nombre', models.CharField(max_length=500)),
                ('atributos', models.JSONField(blank=True, default=dict)),
                ('estado', models.CharField(choices=[('borrador', 'Borrador'), ('en_formulacion', 'En formulación'), ('en_revision', 'En revisión'), ('observado', 'Observado'), ('aprobado', 'Aprobado')], default='borrador', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('actividad', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tareas', to='sis_poa.actividad')),
            ],
            options={
                'db_table': 'poau_tarea',
                'verbose_name': 'Tarea',
                'verbose_name_plural': 'Tareas',
                'ordering': ['actividad', 'codigo'],
            },
        ),
        migrations.AddConstraint(
            model_name='operacion',
            constraint=models.UniqueConstraint(fields=('accion', 'codigo'), name='uniq_operacion_codigo'),
        ),
        migrations.AddConstraint(
            model_name='actividad',
            constraint=models.UniqueConstraint(fields=('operacion', 'codigo'), name='uniq_actividad_codigo'),
        ),
        migrations.AddConstraint(
            model_name='accioncortoplazo',
            constraint=models.UniqueConstraint(fields=('poa', 'codigo'), name='uniq_accion_poa_codigo'),
        ),
        migrations.AddConstraint(
            model_name='programacionactividad',
            constraint=models.UniqueConstraint(fields=('actividad', 'anio', 'tipo'), name='uniq_programacion_actividad'),
        ),
        migrations.AddConstraint(
            model_name='tarea',
            constraint=models.UniqueConstraint(fields=('actividad', 'codigo'), name='uniq_tarea_codigo'),
        ),
        migrations.AddIndex(
            model_name='poainstitucional',
            index=models.Index(fields=['gestion', 'estado'], name='poau_poains_gestion_0ac185_idx'),
        ),
    ]
