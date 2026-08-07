from django.db import migrations


CREAR_TRIGGER = r"""
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
      JOIN catalogos_versionclasificador vc
        ON vc.id = cp.version_clasificador_id
     WHERE cp.id = NEW.categoria_programatica_id;
    IF gestion_relacionada IS DISTINCT FROM NEW.gestion
       OR tipo_version IS DISTINCT FROM 'categoria_programatica' THEN
        RAISE EXCEPTION 'Categoría programática incompatible con la gestión'
            USING ERRCODE = '23514', CONSTRAINT = 'asignacion_coherencia_gestion';
    END IF;

    SELECT gestion INTO gestion_relacionada
      FROM organizacion_unidadorganizacional
     WHERE id = NEW.unidad_id;
    IF gestion_relacionada IS DISTINCT FROM NEW.gestion THEN
        RAISE EXCEPTION 'Unidad incompatible con la gestión'
            USING ERRCODE = '23514', CONSTRAINT = 'asignacion_coherencia_gestion';
    END IF;

    SELECT vc.gestion, vc.tipo
      INTO gestion_relacionada, tipo_version
      FROM catalogos_fuentefinanciamiento c
      LEFT JOIN catalogos_versionclasificador vc
        ON vc.id = c.version_clasificador_id
     WHERE c.id = NEW.fuente_id;
    IF gestion_relacionada IS DISTINCT FROM NEW.gestion
       OR tipo_version IS DISTINCT FROM 'fuente_financiamiento' THEN
        RAISE EXCEPTION 'Fuente incompatible con la gestión o tipo de versión'
            USING ERRCODE = '23514', CONSTRAINT = 'asignacion_coherencia_gestion';
    END IF;

    SELECT vc.gestion, vc.tipo
      INTO gestion_relacionada, tipo_version
      FROM catalogos_organismofinanciador c
      LEFT JOIN catalogos_versionclasificador vc
        ON vc.id = c.version_clasificador_id
     WHERE c.id = NEW.organismo_id;
    IF gestion_relacionada IS DISTINCT FROM NEW.gestion
       OR tipo_version IS DISTINCT FROM 'organismo_financiador' THEN
        RAISE EXCEPTION 'Organismo incompatible con la gestión o tipo de versión'
            USING ERRCODE = '23514', CONSTRAINT = 'asignacion_coherencia_gestion';
    END IF;

    SELECT vc.gestion, vc.tipo
      INTO gestion_relacionada, tipo_version
      FROM catalogos_objetogasto c
      LEFT JOIN catalogos_versionclasificador vc
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

CREATE TRIGGER validar_coherencia_asignacion_presupuestaria
BEFORE INSERT OR UPDATE ON presupuesto_asignacionpresupuestariaunidad
FOR EACH ROW EXECUTE FUNCTION presupuesto_validar_coherencia_asignacion();
"""


ELIMINAR_TRIGGER = r"""
DROP TRIGGER IF EXISTS validar_coherencia_asignacion_presupuestaria
    ON presupuesto_asignacionpresupuestariaunidad;
DROP FUNCTION IF EXISTS presupuesto_validar_coherencia_asignacion();
"""


class Migration(migrations.Migration):
    dependencies = [
        ('presupuesto', '0002_categoriaprogramatica_asignacionpresupuestariaunidad_and_more'),
    ]

    operations = [
        migrations.RunSQL(CREAR_TRIGGER, ELIMINAR_TRIGGER),
    ]
