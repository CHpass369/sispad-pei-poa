"""Pasa a minúscula las claves de mes de la programación mensual.

`programacion_mensual` es un `jsonb` con los meses del año como clave, en
castellano. Nada impide escribirlos de otra forma, y ya pasó: cuatro filas
quedaron con los doce meses en MAYÚSCULA.

    articulacion_tareapoau ······ 1 fila
    articulacion_actividadpoau ·· 2 filas
    articulacion_operacionpoau ·· 1 fila

El total anual no se ve afectado —`jsonb_each` suma sin mirar la grafía, y de
hecho `total_programado` coincide en las tres filas que lo tienen cargado—. Lo
que se rompe es la agregación **por mes**, que es para lo que existe el campo:
una consulta que agrupe por `'junio'` ignora esas filas en silencio y devuelve un
número más bajo, sin error. En `operacionpoau` eso son 905 de 997 bolivianos.

Ninguna fila mezcla las dos grafías (verificado), así que bajar a minúscula no
puede pisar una clave existente ni cambiar ninguna suma.

Esto corrige los datos de hoy, no la causa. Mientras el mes sea una clave de
texto libre dentro de un `jsonb`, el mismo error puede volver a entrar. La
corrección de fondo es la que sigue en el plan: llevar la programación a una
tabla con `mes` como entero 1–12 y `UNIQUE(entidad, mes)`, donde un mes mal
escrito directamente no entra.

Sin reversa real: volver a poner las claves en mayúscula sería restaurar el
error. La reversa es un no-op declarado.
"""
from django.db import migrations

TABLAS = [
    ('articulacion_tareapoau', 'programacion_mensual'),
    ('articulacion_actividadpoau', 'programacion_mensual'),
    ('articulacion_operacionpoau', 'programacion_mensual'),
    ('articulacion_asignacionobjetogasto', 'programacion_mensual'),
    ('articulacion_seguimientopresupuesto', 'ejecucion_mensual'),
]


def normalizar(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        for tabla, columna in TABLAS:
            cursor.execute(f"""
                UPDATE "{tabla}"
                   SET "{columna}" = (
                       SELECT jsonb_object_agg(lower(k), v)
                         FROM jsonb_each("{columna}") AS e(k, v)
                   )
                 WHERE jsonb_typeof("{columna}") = 'object'
                   AND EXISTS (
                       SELECT 1 FROM jsonb_object_keys("{columna}") AS k
                        WHERE k <> lower(k)
                   );
            """)


class Migration(migrations.Migration):
    dependencies = [
        ('articulacion', '0015_limpiar_indices_duplicados_de_fk'),
    ]

    operations = [
        migrations.RunPython(normalizar, migrations.RunPython.noop),
    ]
