from django.db import migrations


TABLAS = (
    'articulacion_resultadopad',
    'articulacion_productopad',
    'articulacion_resultadopei',
    'articulacion_productopei',
    'articulacion_accionpoa',
    'articulacion_operacionpoau',
    'articulacion_actividadpoau',
    'articulacion_tareapoau',
)

FUNCION = 'articulacion_bloquear_mutacion_codigo_oficial'


def _nombre_trigger(tabla):
    return f'{tabla}_codigo_oficial_inmutable'


SQL_FORWARD = f'''
CREATE OR REPLACE FUNCTION {FUNCION}()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.estado_codigo = 'oficial' THEN
        RAISE EXCEPTION 'Los registros con código OFICIAL son inmutables.'
            USING ERRCODE = 'integrity_constraint_violation';
    END IF;

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
''' + '\n'.join(
    f'''
DROP TRIGGER IF EXISTS {_nombre_trigger(tabla)} ON {tabla};
CREATE TRIGGER {_nombre_trigger(tabla)}
BEFORE UPDATE OR DELETE ON {tabla}
FOR EACH ROW EXECUTE FUNCTION {FUNCION}();
'''
    for tabla in TABLAS
)

SQL_REVERSE = '\n'.join(
    f'DROP TRIGGER IF EXISTS {_nombre_trigger(tabla)} ON {tabla};'
    for tabla in TABLAS
) + f'\nDROP FUNCTION IF EXISTS {FUNCION}();\n'


class Migration(migrations.Migration):

    dependencies = [
        ('articulacion', '0005_accionpoa_articulacion_incompleta_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql=SQL_FORWARD,
            reverse_sql=SQL_REVERSE,
        ),
    ]
