"""Recrea las funciones trigger de presupuesto con los nombres de tabla
renombrados de la app catalogos (catalogo_*).

Las migraciones 0003/0004 crearon las funciones PL/pgSQL con los nombres
antiguos (catalogos_versionclasificador, etc.) embebidos en su cuerpo.
Tras el renombrado de tablas a catalogo_* (catalogos 0005), esos cuerpos
quedan rotos en runtime; esta migración los recrea con los nombres nuevos
sin modificar las migraciones originales.
"""

from django.db import migrations


RECREAR_FUNCIONES = r"""
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

    SELECT gestion INTO gestion_relacionada
      FROM organizacion_unidadorganizacional
     WHERE id = NEW.unidad_id;
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
"""


RESTAURAR_FUNCIONES = r"""
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
"""


class Migration(migrations.Migration):
    dependencies = [
        ('presupuesto', '0004_blindaje_categoria_programatica'),
        ('catalogos', '0005_rename_catalogos_c_version_e77357_idx_catalogo_ub_version_948f51_idx_and_more'),
    ]

    operations = [
        migrations.RunSQL(RECREAR_FUNCIONES, RESTAURAR_FUNCIONES),
    ]
