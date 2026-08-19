"""Rutas de la API V2 del ciclo presupuestario SIS-POA (apps.budget).

Namespace montado en `config/urls_v2.py` como `/api/v2/sis-poa/budget/`.
"""
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AperturaViewSet,
    AuditLogView,
    BudgetControlView,
    DocumentoPresupuestarioViewSet,
    ImportacionViewSet,
    CatalogOptionsView,
    RecursoTechoViewSet,
    CompositionView,
    TechoDirectivoViewSet,
    DistributionDashboardView,
    DistribucionVersionViewSet,
    ExpenseObjectViewSet,
    GestionFiscalPresupuestoViewSet,
    GastoObligatorioViewSet,
    CategoriaProgramaticaTechoViewSet,
    ReformaViewSet,
    ReservaViewSet,
    DistribucionTerritorialViewSet,
)

budget_router = DefaultRouter()
budget_router.register('fiscal-years', GestionFiscalPresupuestoViewSet, basename='v2-fiscal-years')
budget_router.register(
    'directive-ceilings', TechoDirectivoViewSet,
    basename='v2-directive-ceilings',
)
budget_router.register('resources', RecursoTechoViewSet, basename='v2-budget-resources')
budget_router.register(
    'mandatory-expenses', GastoObligatorioViewSet,
    basename='v2-mandatory-expenses',
)
budget_router.register('documents', DocumentoPresupuestarioViewSet, basename='v2-budget-documents')
budget_router.register(
    'programmatic-categories', CategoriaProgramaticaTechoViewSet,
    basename='v2-programmatic-categories',
)
budget_router.register(
    'distributions', DistribucionVersionViewSet,
    basename='v2-budget-distributions',
)
budget_router.register('allocations', AperturaViewSet, basename='v2-budget-allocations')
budget_router.register(
    'expense-objects', ExpenseObjectViewSet, basename='v2-expense-objects',
)
budget_router.register('reserves', ReservaViewSet, basename='v2-budget-reserves')
budget_router.register('imports', ImportacionViewSet, basename='v2-budget-imports')
budget_router.register(
    'territorial-distributions', DistribucionTerritorialViewSet,
    basename='v2-territorial-distributions',
)
budget_router.register('reforms', ReformaViewSet, basename='v2-budget-reforms')

urlpatterns = [
    path(
        'directive-ceilings/<int:pk>/composition/',
        CompositionView.as_view(),
        name='v2-directive-ceiling-composition',
    ),
    path('catalogs/', CatalogOptionsView.as_view(), name='v2-budget-catalogs'),
    path(
        'distributions/dashboard/',
        DistributionDashboardView.as_view(),
        name='v2-budget-distribution-dashboard',
    ),
    path(
        'control/summary/',
        BudgetControlView.as_view(),
        name='v2-budget-control-summary',
    ),
    path(
        'control/validate/',
        BudgetControlView.as_view(),
        name='v2-budget-control-validate',
    ),
    path('audit/', AuditLogView.as_view(), name='v2-budget-audit'),
    *budget_router.urls,
]
