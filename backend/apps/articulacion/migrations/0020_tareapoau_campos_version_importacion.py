import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('articulacion', '0019_importacion_programacion_fisica'),
        ('gestion', '0005_candado_gestion_habilitada'),
        ('organizacion', '0003_area_y_clase_de_unidad'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='tareapoau',
            name='formula',
            field=models.TextField(blank=True, verbose_name='Fórmula'),
        ),
        migrations.AddField(
            model_name='tareapoau',
            name='indicador',
            field=models.TextField(blank=True, verbose_name='Indicador'),
        ),
        migrations.AddField(
            model_name='tareapoau',
            name='unidad_medida',
            field=models.CharField(
                blank=True,
                max_length=100,
                verbose_name='Unidad de medida',
            ),
        ),
        migrations.CreateModel(
            name='VersionImportacionPOAU',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                (
                    'created_by',
                    models.ForeignKey(
                        blank=True,
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='+',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    'updated_by',
                    models.ForeignKey(
                        blank=True,
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='+',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    'id',
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    'tipo_evento',
                    models.CharField(
                        choices=[
                            ('REEMPLAZO', 'Reemplazo'),
                            ('RESTAURACION', 'Restauración'),
                        ],
                        max_length=20,
                    ),
                ),
                ('snapshot', models.JSONField(default=dict)),
                ('resumen', models.JSONField(default=dict)),
                ('fuente_nombre', models.CharField(blank=True, default='', max_length=300)),
                ('fuente_sha256', models.CharField(blank=True, default='', max_length=64)),
                ('hoja', models.CharField(blank=True, default='', max_length=200)),
                ('motivo', models.TextField(blank=True, default='')),
                (
                    'gestion',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='versiones_importacion_poau',
                        to='gestion.gestionfiscal',
                    ),
                ),
                (
                    'unidad',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='versiones_importacion_poau',
                        to='organizacion.unidadorganizacional',
                    ),
                ),
                (
                    'usuario',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='versiones_importacion_poau',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'verbose_name': 'Versión histórica de importación POAU',
                'verbose_name_plural': 'Versiones históricas de importación POAU',
                'db_table': 'articulacion_version_importacion_poau',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(
                        fields=['gestion', 'unidad', 'created_at'],
                        name='art_poau_ver_guo_cre_idx',
                    ),
                ],
            },
        ),
    ]
