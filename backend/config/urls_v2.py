"""Namespaces de la API V2 de PIP-GAMS (ADR-002).

Estructura:
    /api/v2/platform/...   núcleo transversal (IAM, organización, catálogos…)
    /api/v2/sis-pe/...     SIS-PE (instrumentos, versiones, nodos, vínculos…)
    /api/v2/sis-poa/...    SIS-POA (acciones, operaciones, presupuesto…)
    /api/v2/sis-pro/...    SIS-PRO (proyectos, cartera…)
    /api/v2/me/...         identidad/capacidades del usuario actual

Los routers de cada sistema se pueblan en los work packages correspondientes.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.accounts.views_v2 import MeViewSet
from apps.budget.urls import budget_router
from apps.evaluacion.views_v2 import (
    EvaluacionV2ViewSet,
    LeccionV2ViewSet,
    RecomendacionV2ViewSet,
)
from apps.inversion.views_v2 import (
    CondicionViewSet,
    CostoViewSet,
    DocumentoViewSet,
    ProyectoViewSet,
    VinculoViewSet,
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
from apps.planificacion.views_v2 import (
    InstrumentoViewSet,
    MetodologiaViewSet,
    NodoViewSet,
    TipoInstrumentoViewSet,
    VersionViewSet,
    VinculoViewSet,
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
sis_pe_router = DefaultRouter()
sis_poa_router = DefaultRouter()
sis_pro_router = DefaultRouter()

sis_pe_router.register('instrumentos', InstrumentoViewSet, basename='v2-instrumentos')
sis_pe_router.register('versiones', VersionViewSet, basename='v2-versiones')
sis_pe_router.register('nodos', NodoViewSet, basename='v2-nodos')
sis_pe_router.register('vinculos', VinculoViewSet, basename='v2-vinculos')
sis_pe_router.register('tipos-instrumento', TipoInstrumentoViewSet, basename='v2-tipos-instrumento')
sis_pe_router.register('metodologias', MetodologiaViewSet, basename='v2-metodologias')
sis_pe_router.register('evaluaciones', EvaluacionV2ViewSet, basename='v2-evaluaciones')
sis_pe_router.register('lecciones', LeccionV2ViewSet, basename='v2-lecciones')
sis_pe_router.register('recomendaciones', RecomendacionV2ViewSet, basename='v2-recomendaciones')

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
sis_pro_router.register('vinculos', VinculoViewSet, basename='v2-vinculos-proyecto')

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

me_router = DefaultRouter()
me_router.register('me', MeViewSet, basename='v2-me')

urlpatterns = [
    path('platform/', include(platform_router.urls)),
    path('sis-pe/', include(sis_pe_router.urls)),
    path('sis-poa/', include(sis_poa_router.urls)),
    path('sis-poa/budget/', include(budget_router.urls)),
    path('sis-pro/', include(sis_pro_router.urls)),
    path('', include(me_router.urls)),
]
