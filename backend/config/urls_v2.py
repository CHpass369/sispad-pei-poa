"""Namespaces de la API V2 de PIP-GAMS (ADR-002).

Estructura:
    /api/v2/platform/...    núcleo transversal (IAM, workflow, me…)
    /api/v2/core/...        PIP CORE (organización: tipos de unidad, unidades)
    /api/v2/catalogos/...   PIP CATÁLOGOS (clasificador, fuentes, rubros…)
    /api/v2/geo/...         PIP GEO (distritos, unidades territoriales…)
    /api/v2/integracion/... PIP INTEGRACIÓN (cadena PAD-PEI, matrices…)
    /api/v2/auditoria/...   PIP AUDITORÍA (eventos de auditoría)
    /api/v2/sis-poa/...     SIS-POA (acciones, operaciones, presupuesto…)
    /api/v2/sis-pro/...     SIS-PRO (proyectos, cartera…)
    /api/v2/me/...          identidad/capacidades del usuario actual

Los routers de cada sistema se pueblan en los work packages correspondientes.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.accounts.views_v2 import MeViewSet
from apps.articulacion.views import (
    AcuerdoInternacionalViewSet as ArticulacionAcuerdoInternacionalViewSet,
    CompatibilidadAcuerdoInternacionalViewSet as ArticulacionCompatibilidadAcuerdoInternacionalViewSet,
    CodigoNivelViewSet as ArticulacionCodigoNivelViewSet,
    IndicadorCadenaViewSet as ArticulacionIndicadorCadenaViewSet,
    LineamientoPADViewSet as ArticulacionLineamientoPADViewSet,
    NormativaViewSet as ArticulacionNormativaViewSet,
    ProductoPADViewSet as ArticulacionProductoPADViewSet,
    ProductoPEIViewSet as ArticulacionProductoPEIViewSet,
    ResultadoPADViewSet as ArticulacionResultadoPADViewSet,
    ResultadoPEIViewSet as ArticulacionResultadoPEIViewSet,
    ArticulacionPADPEIViewSet,
)
from apps.articulacion.views_matrices import MatrizViewSet as ArticulacionMatrizViewSet
from apps.auditoria.views import EventoAuditoriaViewSet as AuditoriaEventoAuditoriaViewSet
from apps.catalogos.views import (
    ClasificadorInstitucionalViewSet as CatalogoClasificadorInstitucionalViewSet,
    EntidadTransferenciaViewSet as CatalogoEntidadTransferenciaViewSet,
    FinalidadFuncionViewSet as CatalogoFinalidadFuncionViewSet,
    FuenteFinanciamientoViewSet as CatalogoFuenteFinanciamientoViewSet,
    ObjetoGastoViewSet as CatalogoObjetoGastoViewSet,
    OrganismoFinanciadorViewSet as CatalogoOrganismoFinanciadorViewSet,
    RubroRecursoViewSet as CatalogoRubroRecursoViewSet,
    TipoFinanciamientoViewSet as CatalogoTipoFinanciamientoViewSet,
    TipoOperacionViewSet as CatalogoTipoOperacionViewSet,
    TipoProductoViewSet as CatalogoTipoProductoViewSet,
    TipoProyectoViewSet as CatalogoTipoProyectoViewSet,
    UnidadMedidaViewSet as CatalogoUnidadMedidaViewSet,
    VersionCatalogoViewSet as CatalogoVersionCatalogoViewSet,
)
from apps.organizacion.views import (
    AsignacionUsuarioUnidadViewSet as OrganizacionAsignacionUsuarioUnidadViewSet,
    DireccionAdministrativaViewSet as OrganizacionDireccionAdministrativaViewSet,
    TipoUnidadViewSet as OrganizacionTipoUnidadViewSet,
    UnidadEjecutoraViewSet as OrganizacionUnidadEjecutoraViewSet,
    UnidadOrganizacionalViewSet as OrganizacionUnidadOrganizacionalViewSet,
)
from apps.territorio.views import (
    DistritoViewSet as TerritorioDistritoViewSet,
    LocalizacionTerritorialViewSet as TerritorioLocalizacionTerritorialViewSet,
    UnidadTerritorialViewSet as TerritorioUnidadTerritorialViewSet,
)
from apps.inversion.views_v2 import (
    CondicionViewSet,
    CostoViewSet,
    DocumentoViewSet,
    ProyectoViewSet,
    VinculoViewSet as VinculoProyectoViewSet,
)
from apps.inversion.views_preinversion import (
    AlternativaProyectoViewSet,
    AprobacionViewSet,
    ComponenteProyectoViewSet,
    CondicionITCPViewSet,
    DocumentoGeneradoViewSet,
    DocumentoPreinversionViewSet,
    EDTPViewSet,
    EstudioTecnicoViewSet,
    FuenteFinanciamientoViewSet,
    GrupoBeneficiarioViewSet,
    IndicadorEvaluacionViewSet,
    ItemCostoEDTPViewSet,
    ItemCronogramaViewSet,
    ITCPViewSet,
    ObservacionViewSet,
    PlanOMViewSet,
    ProyectoPreinversionViewSet,
    RevisionViewSet,
    SeccionEDTPViewSet,
    TDRActividadViewSet,
    TDRItemPresupuestoViewSet,
    TDRPersonalViewSet,
    TDRProductoViewSet,
    TDRViewSet,
)
from apps.poau.views_v2 import (
    AccionViewSet,
    ActividadViewSet,
    OperacionViewSet,
    PoAViewSet,
    ProgramacionViewSet,
    TareaViewSet,
)
from apps.techos.views_v2 import TechoViewSetV2
from apps.workflow.views_v2 import (
    DefinicionViewSet,
    InstanciaViewSet,
    TareaViewSet as WorkflowTareaViewSet,
)

platform_router = DefaultRouter()
sis_poa_router = DefaultRouter()
sis_pro_router = DefaultRouter()
core_router = DefaultRouter()
catalogo_router = DefaultRouter()
geo_router = DefaultRouter()
integracion_router = DefaultRouter()
auditoria_router = DefaultRouter()


sis_poa_router.register('poas', PoAViewSet, basename='v2-poas')
sis_poa_router.register('acciones', AccionViewSet, basename='v2-acciones-poa')
sis_poa_router.register('operaciones', OperacionViewSet, basename='v2-operaciones')
sis_poa_router.register('actividades', ActividadViewSet, basename='v2-actividades')
sis_poa_router.register('tareas', TareaViewSet, basename='v2-tareas')
sis_poa_router.register('programaciones', ProgramacionViewSet, basename='v2-programaciones')
sis_poa_router.register('techos', TechoViewSetV2, basename='v2-techos')

sis_pro_router.register('proyectos', ProyectoViewSet, basename='v2-proyectos')
sis_pro_router.register('proyectos-preinversion', ProyectoPreinversionViewSet, basename='v2-proyectos-preinversion')
sis_pro_router.register('condiciones', CondicionViewSet, basename='v2-condiciones')
sis_pro_router.register('documentos', DocumentoViewSet, basename='v2-documentos-proyecto')
sis_pro_router.register('costos', CostoViewSet, basename='v2-costos-proyecto')
sis_pro_router.register('vinculos', VinculoProyectoViewSet, basename='v2-vinculos-proyecto')

# --- Preinversión (SISPRE / RM 115) ---------------------------------------
sis_pro_router.register('itcps', ITCPViewSet, basename='v2-itcps')
sis_pro_router.register('itcp-condiciones', CondicionITCPViewSet, basename='v2-itcp-condiciones')
sis_pro_router.register('tdrs', TDRViewSet, basename='v2-tdrs')
sis_pro_router.register('tdr-actividades', TDRActividadViewSet, basename='v2-tdr-actividades')
sis_pro_router.register('tdr-productos', TDRProductoViewSet, basename='v2-tdr-productos')
sis_pro_router.register('tdr-personal', TDRPersonalViewSet, basename='v2-tdr-personal')
sis_pro_router.register('tdr-items-presupuesto', TDRItemPresupuestoViewSet, basename='v2-tdr-items-presupuesto')
sis_pro_router.register('edtps', EDTPViewSet, basename='v2-edtps')
sis_pro_router.register('edtp-secciones', SeccionEDTPViewSet, basename='v2-edtp-secciones')
sis_pro_router.register('estudios-tecnicos', EstudioTecnicoViewSet, basename='v2-estudios-tecnicos')
sis_pro_router.register('edtp-items-costo', ItemCostoEDTPViewSet, basename='v2-edtp-items-costo')
sis_pro_router.register('edtp-financiamiento', FuenteFinanciamientoViewSet, basename='v2-edtp-financiamiento')
sis_pro_router.register('edtp-cronograma', ItemCronogramaViewSet, basename='v2-edtp-cronograma')
sis_pro_router.register('edtp-plan-om', PlanOMViewSet, basename='v2-edtp-plan-om')
sis_pro_router.register('edtp-indicadores', IndicadorEvaluacionViewSet, basename='v2-edtp-indicadores')
sis_pro_router.register('componentes', ComponenteProyectoViewSet, basename='v2-componentes-proyecto')
sis_pro_router.register('beneficiarios', GrupoBeneficiarioViewSet, basename='v2-beneficiarios-proyecto')
sis_pro_router.register('alternativas', AlternativaProyectoViewSet, basename='v2-alternativas-proyecto')
sis_pro_router.register('documentos-preinv', DocumentoPreinversionViewSet, basename='v2-documentos-preinv')
sis_pro_router.register('documentos-generados', DocumentoGeneradoViewSet, basename='v2-documentos-generados')
sis_pro_router.register('revisiones', RevisionViewSet, basename='v2-revisiones-preinv')
sis_pro_router.register('observaciones', ObservacionViewSet, basename='v2-observaciones-preinv')
sis_pro_router.register('aprobaciones', AprobacionViewSet, basename='v2-aprobaciones-preinv')

platform_router.register('workflow-definiciones', DefinicionViewSet, basename='v2-workflow-definiciones')
platform_router.register('workflow-instancias', InstanciaViewSet, basename='v2-workflow-instancias')
platform_router.register('workflow-tareas', WorkflowTareaViewSet, basename='v2-workflow-tareas')

# --- PIP CORE (organización) -------------------------------------------------
core_router.register('tipos-unidad', OrganizacionTipoUnidadViewSet, basename='v2-core-tipos-unidad')
core_router.register('unidades', OrganizacionUnidadOrganizacionalViewSet, basename='v2-core-unidades')
core_router.register('direcciones-administrativas', OrganizacionDireccionAdministrativaViewSet, basename='v2-core-direcciones-administrativas')
core_router.register('unidades-ejecutoras', OrganizacionUnidadEjecutoraViewSet, basename='v2-core-unidades-ejecutoras')
core_router.register('asignaciones-usuario-unidad', OrganizacionAsignacionUsuarioUnidadViewSet, basename='v2-core-asignaciones-usuario-unidad')

# --- PIP CATÁLOGOS ------------------------------------------------------------
catalogo_router.register('clasificadores-institucionales', CatalogoClasificadorInstitucionalViewSet, basename='v2-catalogos-clasificadores-institucionales')
catalogo_router.register('rubros', CatalogoRubroRecursoViewSet, basename='v2-catalogos-rubros')
catalogo_router.register('objetos-gasto', CatalogoObjetoGastoViewSet, basename='v2-catalogos-objetos-gasto')
catalogo_router.register('fuentes', CatalogoFuenteFinanciamientoViewSet, basename='v2-catalogos-fuentes')
catalogo_router.register('organismos', CatalogoOrganismoFinanciadorViewSet, basename='v2-catalogos-organismos')
catalogo_router.register('entidades-transferencia', CatalogoEntidadTransferenciaViewSet, basename='v2-catalogos-entidades-transferencia')
catalogo_router.register('finalidades-funciones', CatalogoFinalidadFuncionViewSet, basename='v2-catalogos-finalidades-funciones')
catalogo_router.register('unidades-medida', CatalogoUnidadMedidaViewSet, basename='v2-catalogos-unidades-medida')
catalogo_router.register('tipos-operacion', CatalogoTipoOperacionViewSet, basename='v2-catalogos-tipos-operacion')
catalogo_router.register('tipos-producto', CatalogoTipoProductoViewSet, basename='v2-catalogos-tipos-producto')
catalogo_router.register('tipos-proyecto', CatalogoTipoProyectoViewSet, basename='v2-catalogos-tipos-proyecto')
catalogo_router.register('tipos-financiamiento', CatalogoTipoFinanciamientoViewSet, basename='v2-catalogos-tipos-financiamiento')
catalogo_router.register('versiones-catalogo', CatalogoVersionCatalogoViewSet, basename='v2-catalogos-versiones-catalogo')

# --- PIP GEO ------------------------------------------------------------------
geo_router.register('distritos', TerritorioDistritoViewSet, basename='v2-geo-distritos')
geo_router.register('unidades-territoriales', TerritorioUnidadTerritorialViewSet, basename='v2-geo-unidades-territoriales')
geo_router.register('localizaciones', TerritorioLocalizacionTerritorialViewSet, basename='v2-geo-localizaciones')

# --- PIP INTEGRACIÓN (cadena PAD-PEI) -----------------------------------------
integracion_router.register('resultados-pad', ArticulacionResultadoPADViewSet, basename='v2-integracion-resultados-pad')
integracion_router.register('productos-pad', ArticulacionProductoPADViewSet, basename='v2-integracion-productos-pad')
integracion_router.register('resultados-pei', ArticulacionResultadoPEIViewSet, basename='v2-integracion-resultados-pei')
integracion_router.register('productos-pei', ArticulacionProductoPEIViewSet, basename='v2-integracion-productos-pei')
integracion_router.register('articulaciones-pad-pei', ArticulacionPADPEIViewSet, basename='v2-integracion-articulaciones-pad-pei')
integracion_router.register('indicadores', ArticulacionIndicadorCadenaViewSet, basename='v2-integracion-indicadores')
integracion_router.register('lineamientos-pad', ArticulacionLineamientoPADViewSet, basename='v2-integracion-lineamientos-pad')
integracion_router.register('acuerdos', ArticulacionAcuerdoInternacionalViewSet, basename='v2-integracion-acuerdos')
integracion_router.register('compatibilidades', ArticulacionCompatibilidadAcuerdoInternacionalViewSet, basename='v2-integracion-compatibilidades')
integracion_router.register('normativas', ArticulacionNormativaViewSet, basename='v2-integracion-normativas')
integracion_router.register('codigos-nivel', ArticulacionCodigoNivelViewSet, basename='v2-integracion-codigos-nivel')
integracion_router.register('matrices', ArticulacionMatrizViewSet, basename='v2-integracion-matrices')

# --- PIP AUDITORÍA ------------------------------------------------------------
auditoria_router.register('eventos', AuditoriaEventoAuditoriaViewSet, basename='v2-auditoria-eventos')

me_router = DefaultRouter()
me_router.register('me', MeViewSet, basename='v2-me')

urlpatterns = [
    path('platform/', include(platform_router.urls)),
    path('core/', include(core_router.urls)),
    path('catalogos/', include(catalogo_router.urls)),
    path('geo/', include(geo_router.urls)),
    path('integracion/', include(integracion_router.urls)),
    path('auditoria/', include(auditoria_router.urls)),
    path('sis-poa/', include(sis_poa_router.urls)),
    path('sis-poa/budget/', include('apps.budget.urls')),
    path('sis-pro/', include(sis_pro_router.urls)),
    path('', include(me_router.urls)),
]
