"""Recupera la clave natural que `CatalogoBase` ya declaraba y nadie heredaba.

`CatalogoBase` es la clase abstracta de la que cuelgan los trece catálogos, y su
Meta declara `unique_together = [('codigo', 'gestion')]`. La intención estaba
escrita desde el principio.

El problema es que las trece subclases abrían `class Meta:` en lugar de
`class Meta(CatalogoBase.Meta):`. En Django eso no extiende la Meta del padre:
la reemplaza entera. La restricción se descartaba en silencio —sin error, sin
aviso— en los trece modelos, y en la base no existía ni una sola clave natural
de catálogo.

Ese hueco no es teórico: por ahí entraron 11 organismos financiadores
duplicados durante una carga de clasificadores, porque el `ON CONFLICT DO
NOTHING` del importador no tenía índice contra el cual chocar.

Comprobado antes de aplicar: cero pares `(codigo, gestion)` repetidos en las 13
tablas, sobre 3.757 filas. La restricción entra sin tocar un dato.

Los `AlterModelOptions` vienen en el mismo paquete porque la Meta heredada
también trae `ordering = ['codigo', 'gestion__anio']`, que hasta ahora sólo se
aplicaba en los modelos que lo declaraban por su cuenta.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('catalogos', '0010_validar_blindaje_fuente_oficial'),
        ('gestion', '0004_gestionfiscal_fiscal_year_metadata'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='clasificadorinstitucional',
            options={'ordering': ['codigo', 'gestion__anio'], 'verbose_name': 'Clasificador institucional', 'verbose_name_plural': 'Clasificadores institucionales'},
        ),
        migrations.AlterModelOptions(
            name='entidadtransferencia',
            options={'ordering': ['codigo', 'gestion__anio'], 'verbose_name': 'Entidad de transferencia', 'verbose_name_plural': 'Entidades de transferencia'},
        ),
        migrations.AlterModelOptions(
            name='finalidadfuncion',
            options={'ordering': ['codigo', 'gestion__anio'], 'verbose_name': 'Finalidad/Función', 'verbose_name_plural': 'Finalidades y funciones'},
        ),
        migrations.AlterModelOptions(
            name='fuentefinanciamiento',
            options={'ordering': ['codigo', 'gestion__anio'], 'verbose_name': 'Fuente de financiamiento', 'verbose_name_plural': 'Fuentes de financiamiento'},
        ),
        migrations.AlterModelOptions(
            name='objetogasto',
            options={'ordering': ['codigo', 'gestion__anio'], 'verbose_name': 'Objeto del gasto', 'verbose_name_plural': 'Objetos del gasto'},
        ),
        migrations.AlterModelOptions(
            name='organismofinanciador',
            options={'ordering': ['codigo', 'gestion__anio'], 'verbose_name': 'Organismo financiador', 'verbose_name_plural': 'Organismos financiadores'},
        ),
        migrations.AlterModelOptions(
            name='rubrorecurso',
            options={'ordering': ['codigo', 'gestion__anio'], 'verbose_name': 'Rubro de recurso', 'verbose_name_plural': 'Rubros de recursos'},
        ),
        migrations.AlterModelOptions(
            name='tipofinanciamiento',
            options={'ordering': ['codigo', 'gestion__anio'], 'verbose_name': 'Tipo de financiamiento', 'verbose_name_plural': 'Tipos de financiamiento'},
        ),
        migrations.AlterModelOptions(
            name='tipooperacion',
            options={'ordering': ['codigo', 'gestion__anio'], 'verbose_name': 'Tipo de operación', 'verbose_name_plural': 'Tipos de operación'},
        ),
        migrations.AlterModelOptions(
            name='tipoproducto',
            options={'ordering': ['codigo', 'gestion__anio'], 'verbose_name': 'Tipo de producto', 'verbose_name_plural': 'Tipos de producto'},
        ),
        migrations.AlterModelOptions(
            name='tipoproyecto',
            options={'ordering': ['codigo', 'gestion__anio'], 'verbose_name': 'Tipo de proyecto', 'verbose_name_plural': 'Tipos de proyecto'},
        ),
        migrations.AlterModelOptions(
            name='unidadmedida',
            options={'ordering': ['codigo', 'gestion__anio'], 'verbose_name': 'Unidad de medida', 'verbose_name_plural': 'Unidades de medida'},
        ),
        migrations.AlterUniqueTogether(
            name='clasificadorinstitucional',
            unique_together={('codigo', 'gestion')},
        ),
        migrations.AlterUniqueTogether(
            name='entidadtransferencia',
            unique_together={('codigo', 'gestion')},
        ),
        migrations.AlterUniqueTogether(
            name='finalidadfuncion',
            unique_together={('codigo', 'gestion')},
        ),
        migrations.AlterUniqueTogether(
            name='fuentefinanciamiento',
            unique_together={('codigo', 'gestion')},
        ),
        migrations.AlterUniqueTogether(
            name='objetogasto',
            unique_together={('codigo', 'gestion')},
        ),
        migrations.AlterUniqueTogether(
            name='organismofinanciador',
            unique_together={('codigo', 'gestion')},
        ),
        migrations.AlterUniqueTogether(
            name='rubrorecurso',
            unique_together={('codigo', 'gestion')},
        ),
        migrations.AlterUniqueTogether(
            name='sectoreconomicopresupuestario',
            unique_together={('codigo', 'gestion')},
        ),
        migrations.AlterUniqueTogether(
            name='tipofinanciamiento',
            unique_together={('codigo', 'gestion')},
        ),
        migrations.AlterUniqueTogether(
            name='tipooperacion',
            unique_together={('codigo', 'gestion')},
        ),
        migrations.AlterUniqueTogether(
            name='tipoproducto',
            unique_together={('codigo', 'gestion')},
        ),
        migrations.AlterUniqueTogether(
            name='tipoproyecto',
            unique_together={('codigo', 'gestion')},
        ),
        migrations.AlterUniqueTogether(
            name='unidadmedida',
            unique_together={('codigo', 'gestion')},
        ),
    ]
