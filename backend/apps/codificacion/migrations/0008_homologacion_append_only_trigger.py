from django.db import migrations


CREATE_APPEND_ONLY_TRIGGER = """
CREATE FUNCTION codificacion_rechazar_cambio_homologacion_codigo()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION
        'codificacion_homologacioncodigo is append-only; UPDATE and DELETE are forbidden'
        USING ERRCODE = '55000';
END;
$$;

CREATE TRIGGER codificacion_homologacioncodigo_append_only
BEFORE UPDATE OR DELETE ON codificacion_homologacioncodigo
FOR EACH ROW
EXECUTE FUNCTION codificacion_rechazar_cambio_homologacion_codigo();
"""


DROP_APPEND_ONLY_TRIGGER = """
DROP TRIGGER IF EXISTS codificacion_homologacioncodigo_append_only
ON codificacion_homologacioncodigo;
DROP FUNCTION IF EXISTS codificacion_rechazar_cambio_homologacion_codigo();
"""


class Migration(migrations.Migration):
    dependencies = [
        ('codificacion', '0007_secuencia_y_homologacion'),
    ]

    operations = [
        migrations.RunSQL(
            sql=CREATE_APPEND_ONLY_TRIGGER,
            reverse_sql=DROP_APPEND_ONLY_TRIGGER,
        ),
    ]
