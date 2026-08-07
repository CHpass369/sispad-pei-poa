from django.db import migrations


CREAR_TRIGGER = r"""
CREATE OR REPLACE FUNCTION presupuesto_validar_categoria_programatica()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    gestion_version integer;
    tipo_version varchar(40);
    codigo_entidad varchar(50);
    gestion_entidad integer;
    codigo_da varchar(10);
    gestion_da integer;
    codigo_ue varchar(10);
    gestion_ue integer;
    da_de_ue uuid;
    codigo_programa varchar(20);
    gestion_programa integer;
    codigo_proyecto varchar(20);
    gestion_proyecto integer;
    programa_de_proyecto uuid;
    codigo_actividad varchar(20);
    gestion_actividad integer;
    proyecto_de_actividad uuid;
BEGIN
    SELECT gestion, tipo INTO gestion_version, tipo_version
      FROM catalogos_versionclasificador
     WHERE id = NEW.version_clasificador_id;
    SELECT codigo, gestion INTO codigo_entidad, gestion_entidad
      FROM catalogos_clasificadorinstitucional WHERE id = NEW.entidad_id;
    SELECT codigo, gestion INTO codigo_da, gestion_da
      FROM organizacion_direccionadministrativa WHERE id = NEW.da_id;
    SELECT codigo, gestion, da_id INTO codigo_ue, gestion_ue, da_de_ue
      FROM organizacion_unidadejecutora WHERE id = NEW.ue_id;
    SELECT codigo, gestion INTO codigo_programa, gestion_programa
      FROM presupuesto_programapresupuestario WHERE id = NEW.programa_id;
    SELECT codigo, gestion, programa_id
      INTO codigo_proyecto, gestion_proyecto, programa_de_proyecto
      FROM presupuesto_proyectopresupuestario WHERE id = NEW.proyecto_id;
    SELECT codigo, gestion, proyecto_id
      INTO codigo_actividad, gestion_actividad, proyecto_de_actividad
      FROM presupuesto_actividadpresupuestaria WHERE id = NEW.actividad_id;

    IF tipo_version IS DISTINCT FROM 'categoria_programatica'
       OR codigo_entidad IS DISTINCT FROM '1312'
       OR gestion_entidad IS DISTINCT FROM gestion_version
       OR gestion_da IS DISTINCT FROM gestion_version
       OR gestion_ue IS DISTINCT FROM gestion_version
       OR gestion_programa IS DISTINCT FROM gestion_version
       OR gestion_proyecto IS DISTINCT FROM gestion_version
       OR gestion_actividad IS DISTINCT FROM gestion_version
       OR da_de_ue IS DISTINCT FROM NEW.da_id
       OR programa_de_proyecto IS DISTINCT FROM NEW.programa_id
       OR proyecto_de_actividad IS DISTINCT FROM NEW.proyecto_id THEN
        RAISE EXCEPTION 'Categoría programática incoherente'
            USING ERRCODE = '23514', CONSTRAINT = 'categoria_programatica_coherente';
    END IF;

    NEW.codigo_compuesto := concat_ws(
        '.', codigo_entidad, codigo_da, codigo_ue,
        codigo_programa, codigo_proyecto, codigo_actividad
    );
    RETURN NEW;
END;
$$;

CREATE TRIGGER validar_categoria_programatica
BEFORE INSERT OR UPDATE ON presupuesto_categoriaprogramatica
FOR EACH ROW EXECUTE FUNCTION presupuesto_validar_categoria_programatica();
"""


ELIMINAR_TRIGGER = r"""
DROP TRIGGER IF EXISTS validar_categoria_programatica
    ON presupuesto_categoriaprogramatica;
DROP FUNCTION IF EXISTS presupuesto_validar_categoria_programatica();
"""


class Migration(migrations.Migration):
    dependencies = [
        ('presupuesto', '0003_coherencia_gestion_asignacion'),
    ]

    operations = [
        migrations.RunSQL(CREAR_TRIGGER, ELIMINAR_TRIGGER),
    ]
