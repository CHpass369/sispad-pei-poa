# PIP-DB-002: recrea los triggers de coherencia de gestión tras convertir
# organizacion.gestion (integer año) → FK a gestion_gestionfiscal (UUID).
# Los triggers 0003/0004 (y sus versiones 0005 con nombres catalogo_*) leían
# gestion como entero; ahora se normaliza con JOIN a gestion_gestionfiscal.
# Sin cambios de semántica.
#
# Reversa: se eliminan los triggers (el SQL original ya no puede ejecutarse
# contra la columna UUID — el estado previo era inválido con la FK).

from django.db import migrations


ASIGNACION = r"""
CREATE OR REPLACE FUNCTION presupuesto_validar_coherencia_asignacion()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    gestion_relacionada integer;
    tipo_version varchar(40);
BEGIN
    SELECT vc.gestion, vc.tipo
      INTO gestion_relacionada, tipo_version
      FROM presupuesto_categoriaprogramatica cp
      JOIN catalogo_version_clasificador vc
        ON vc.id = cp.version_clasificador_id
     WHERE cp.id = NEW.categoria_programatica_id;
    IF gestion_relacionada IS DISTINCT FROM NEW.gestion
       OR tipo_version IS DISTINCT FROM 'categoria_programatica' THEN
        RAISE EXCEPTION 'Categoría programática incompatible con la gestión'
            USING ERRCODE = '23514', CONSTRAINT = 'asignacion_coherencia_gestion';
    END IF;

    SELECT gf.anio INTO gestion_relacionada
      FROM organizacion_unidadorganizacional uo
      JOIN gestion_gestionfiscal gf ON gf.id = uo.gestion
     WHERE uo.id = NEW.unidad_id;
    IF gestion_relacionada IS DISTINCT FROM NEW.gestion THEN
        RAISE EXCEPTION 'Unidad incompatible con la gestión'
            USING ERRCODE = '23514', CONSTRAINT = 'asignacion_coherencia_gestion';
    END IF;

    SELECT vc.gestion, vc.tipo
      INTO gestion_relacionada, tipo_version
      FROM catalogo_fuente_financiamiento c
      LEFT JOIN catalogo_version_clasificador vc
        ON vc.id = c.version_clasificador_id
     WHERE c.id = NEW.fuente_id;
    IF gestion_relacionada IS DISTINCT FROM NEW.gestion
       OR tipo_version IS DISTINCT FROM 'fuente_financiamiento' THEN
        RAISE EXCEPTION 'Fuente incompatible con la gestión o tipo de versión'
            USING ERRCODE = '23514', CONSTRAINT = 'asignacion_coherencia_gestion';
    END IF;

    SELECT vc.gestion, vc.tipo
      INTO gestion_relacionada, tipo_version
      FROM catalogo_organismo_financiador c
      LEFT JOIN catalogo_version_clasificador vc
        ON vc.id = c.version_clasificador_id
     WHERE c.id = NEW.organismo_id;
    IF gestion_relacionada IS DISTINCT FROM NEW.gestion
       OR tipo_version IS DISTINCT FROM 'organismo_financiador' THEN
        RAISE EXCEPTION 'Organismo incompatible con la gestión o tipo de versión'
            USING ERRCODE = '23514', CONSTRAINT = 'asignacion_coherencia_gestion';
    END IF;

    SELECT vc.gestion, vc.tipo
      INTO gestion_relacionada, tipo_version
      FROM catalogo_objeto_gasto c
      LEFT JOIN catalogo_version_clasificador vc
        ON vc.id = c.version_clasificador_id
     WHERE c.id = NEW.objeto_gasto_id;
    IF gestion_relacionada IS DISTINCT FROM NEW.gestion
       OR tipo_version IS DISTINCT FROM 'objeto_gasto' THEN
        RAISE EXCEPTION 'Objeto incompatible con la gestión o tipo de versión'
            USING ERRCODE = '23514', CONSTRAINT = 'asignacion_coherencia_gestion';
    END IF;

    IF NEW.operacion_id IS NOT NULL THEN
        SELECT acp.gestion INTO gestion_relacionada
          FROM articulacion_operacionpoau op
          JOIN articulacion_accionpoa acp ON acp.id = op.accion_poa_id
         WHERE op.id = NEW.operacion_id;
    ELSIF NEW.actividad_id IS NOT NULL THEN
        SELECT acp.gestion INTO gestion_relacionada
          FROM articulacion_actividadpoau act
          JOIN articulacion_operacionpoau op ON op.id = act.operacion_id
          JOIN articulacion_accionpoa acp ON acp.id = op.accion_poa_id
         WHERE act.id = NEW.actividad_id;
    ELSE
        SELECT acp.gestion INTO gestion_relacionada
          FROM articulacion_tareapoau tar
          JOIN articulacion_actividadpoau act ON act.id = tar.actividad_id
          JOIN articulacion_operacionpoau op ON op.id = act.operacion_id
          JOIN articulacion_accionpoa acp ON acp.id = op.accion_poa_id
         WHERE tar.id = NEW.tarea_id;
    END IF;
    IF gestion_relacionada IS DISTINCT FROM NEW.gestion THEN
        RAISE EXCEPTION 'Nivel operativo incompatible con la gestión'
            USING ERRCODE = '23514', CONSTRAINT = 'asignacion_coherencia_gestion';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS validar_coherencia_asignacion_presupuestaria
    ON presupuesto_asignacionpresupuestariaunidad;
CREATE TRIGGER validar_coherencia_asignacion_presupuestaria
BEFORE INSERT OR UPDATE ON presupuesto_asignacionpresupuestariaunidad
FOR EACH ROW EXECUTE FUNCTION presupuesto_validar_coherencia_asignacion();
"""


CATEGORIA = r"""
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
      FROM catalogo_version_clasificador
     WHERE id = NEW.version_clasificador_id;
    SELECT codigo, gestion INTO codigo_entidad, gestion_entidad
      FROM catalogo_clasificador_institucional WHERE id = NEW.entidad_id;
    SELECT da.codigo, gf.anio INTO codigo_da, gestion_da
      FROM organizacion_direccionadministrativa da
      JOIN gestion_gestionfiscal gf ON gf.id = da.gestion
     WHERE da.id = NEW.da_id;
    SELECT ue.codigo, gf.anio, ue.da_id INTO codigo_ue, gestion_ue, da_de_ue
      FROM organizacion_unidadejecutora ue
      JOIN gestion_gestionfiscal gf ON gf.id = ue.gestion
     WHERE ue.id = NEW.ue_id;
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

DROP TRIGGER IF EXISTS validar_categoria_programatica
    ON presupuesto_categoriaprogramatica;
CREATE TRIGGER validar_categoria_programatica
BEFORE INSERT OR UPDATE ON presupuesto_categoriaprogramatica
FOR EACH ROW EXECUTE FUNCTION presupuesto_validar_categoria_programatica();
"""


ELIMINAR = r"""
DROP TRIGGER IF EXISTS validar_coherencia_asignacion_presupuestaria
    ON presupuesto_asignacionpresupuestariaunidad;
DROP FUNCTION IF EXISTS presupuesto_validar_coherencia_asignacion();
DROP TRIGGER IF EXISTS validar_categoria_programatica
    ON presupuesto_categoriaprogramatica;
DROP FUNCTION IF EXISTS presupuesto_validar_categoria_programatica();
"""


class Migration(migrations.Migration):
    dependencies = [
        ('presupuesto', '0006_limpiar_indices_redundantes'),
    ]

    operations = [
        migrations.RunSQL(ASIGNACION, ELIMINAR),
        migrations.RunSQL(CATEGORIA, ELIMINAR),
    ]