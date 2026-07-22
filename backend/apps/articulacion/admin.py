from django.contrib import admin
from .models import (
    CodigoNivel, AcuerdoInternacional, Normativa, LineamientoPAD,
    ResultadoPAD, ProductoPAD, ResultadoPEI, ProductoPEI,
    ArticulacionPADPEI, IndicadorCadena, AccionPOA, OperacionPOAU,
    ActividadPOAU, ActividadNormativa, TareaPOAU, TareaNormativa,
    SeguimientoPresupuesto, AsignacionObjetoGasto,
)


@admin.register(CodigoNivel)
class CodigoNivelAdmin(admin.ModelAdmin):
    list_display = ['codigo_nivel', 'nivel', 'longitud', 'editable', 'vigencia']
    list_filter = ['editable', 'vigencia']
    search_fields = ['nivel', 'codigo_nivel', 'ejemplo']


@admin.register(AcuerdoInternacional)
class AcuerdoInternacionalAdmin(admin.ModelAdmin):
    list_display = ['tipo_acuerdo', 'codigo', 'denominacion', 'activo', 'es_codigo_oficial']
    list_filter = ['tipo_acuerdo', 'activo', 'es_codigo_oficial']
    search_fields = ['codigo', 'denominacion']


@admin.register(Normativa)
class NormativaAdmin(admin.ModelAdmin):
    list_display = ['codigo_norma', 'nivel', 'tipo_norma', 'estado', 'fecha_emision']
    list_filter = ['nivel', 'tipo_norma', 'estado', 'vigencia']
    search_fields = ['codigo_norma', 'denominacion', 'numero_identificador']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(LineamientoPAD)
class LineamientoPADAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'denominacion', 'gestion_desde', 'gestion_hasta', 'activo']
    list_filter = ['activo', 'gestion_desde']
    search_fields = ['codigo', 'denominacion']


@admin.register(ResultadoPAD)
class ResultadoPADAdmin(admin.ModelAdmin):
    list_display = ['codigo_resultado', 'denominacion', 'vigencia_desde', 'vigencia_hasta', 'estado']
    list_filter = ['estado', 'vigencia_desde', 'lineamiento_pad']
    search_fields = ['codigo_resultado', 'denominacion']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ProductoPAD)
class ProductoPADAdmin(admin.ModelAdmin):
    list_display = ['codigo_producto', 'denominacion', 'resultado_pad', 'responsable']
    list_filter = ['resultado_pad']
    search_fields = ['codigo_producto', 'denominacion']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ResultadoPEI)
class ResultadoPEIAdmin(admin.ModelAdmin):
    list_display = ['codigo_resultado', 'denominacion', 'entidad', 'vigencia_desde', 'vigencia_hasta']
    list_filter = ['vigencia_desde', 'cod_entidad']
    search_fields = ['codigo_resultado', 'denominacion']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ProductoPEI)
class ProductoPEIAdmin(admin.ModelAdmin):
    list_display = ['codigo_producto', 'denominacion', 'resultado_pei', 'programa_presup']
    list_filter = ['resultado_pei']
    search_fields = ['codigo_producto', 'denominacion']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ArticulacionPADPEI)
class ArticulacionPADPEIAdmin(admin.ModelAdmin):
    list_display = ['producto_pad', 'producto_pei', 'tipo_contribucion', 'ponderacion', 'estado']
    list_filter = ['estado', 'tipo_contribucion']
    search_fields = ['justificacion']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(IndicadorCadena)
class IndicadorCadenaAdmin(admin.ModelAdmin):
    list_display = ['nivel_indicador', 'indicador', 'unidad_medida', 'linea_base', 'meta_2030']
    list_filter = ['nivel_indicador']
    search_fields = ['indicador', 'unidad_medida']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AccionPOA)
class AccionPOAAdmin(admin.ModelAdmin):
    list_display = ['codigo_accion', 'denominacion', 'gestion', 'producto_pei', 'estado']
    list_filter = ['gestion', 'estado', 'tipo_operacion']
    search_fields = ['codigo_accion', 'denominacion', 'programa']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(OperacionPOAU)
class OperacionPOAUAdmin(admin.ModelAdmin):
    list_display = ['codigo_operacion', 'denominacion', 'tipo_operacion', 'accion_poa', 'estado']
    list_filter = ['tipo_operacion', 'estado']
    search_fields = ['codigo_operacion', 'denominacion']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ActividadPOAU)
class ActividadPOAUAdmin(admin.ModelAdmin):
    list_display = ['codigo_actividad', 'denominacion', 'operacion', 'estado']
    list_filter = ['estado']
    search_fields = ['codigo_actividad', 'denominacion']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ActividadNormativa)
class ActividadNormativaAdmin(admin.ModelAdmin):
    list_display = ['actividad', 'normativa', 'obligatorio', 'tipo_aplicacion']
    list_filter = ['obligatorio']
    search_fields = ['actividad__codigo_actividad', 'normativa__codigo_norma']


@admin.register(TareaPOAU)
class TareaPOAUAdmin(admin.ModelAdmin):
    list_display = ['codigo_tarea', 'denominacion', 'actividad', 'responsable', 'estado']
    list_filter = ['estado']
    search_fields = ['codigo_tarea', 'denominacion', 'responsable']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(TareaNormativa)
class TareaNormativaAdmin(admin.ModelAdmin):
    list_display = ['tarea', 'normativa', 'obligatorio', 'tipo_aplicacion']
    list_filter = ['obligatorio']
    search_fields = ['tarea__codigo_tarea', 'normativa__codigo_norma']


@admin.register(SeguimientoPresupuesto)
class SeguimientoPresupuestoAdmin(admin.ModelAdmin):
    list_display = [
        'id_cadena', 'gestion', 'accion_poa', 'presupuesto_inicial',
        'presupuesto_vigente', 'porcentaje_ejecucion_financiera', 'estado'
    ]
    list_filter = ['gestion', 'estado', 'tipo_gasto']
    search_fields = ['id_cadena', 'programa']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AsignacionObjetoGasto)
class AsignacionObjetoGastoAdmin(admin.ModelAdmin):
    list_display = [
        'codigo_asignacion', 'gestion', 'descripcion_objeto',
        'monto_programado', 'monto_vigente', 'estado'
    ]
    list_filter = ['gestion', 'estado', 'tipo_gasto', 'grupo_gasto']
    search_fields = ['codigo_asignacion', 'descripcion_objeto']
    readonly_fields = ['created_at', 'updated_at']
