"""Rutas de la API V2 del ciclo presupuestario SIS-POA (apps.budget).

Namespace montado en `config/urls_v2.py` como `/api/v2/sis-poa/budget/`.
"""
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AllocationViewSet,
    BudgetControlView,
    BudgetDocumentViewSet,
    BudgetImportViewSet,
    CatalogOptionsView,
    CeilingResourceViewSet,
    CompositionView,
    DirectiveCeilingViewSet,
    DistributionDashboardView,
    DistributionVersionViewSet,
    ExpenseObjectViewSet,
    FiscalYearViewSet,
    MandatoryExpenseViewSet,
    ProgrammaticCategoryViewSet,
    ReformViewSet,
    ReserveViewSet,
    TerritorialDistributionViewSet,
)

budget_router = DefaultRouter()
budget_router.register('fiscal-years', FiscalYearViewSet, basename='v2-fiscal-years')
budget_router.register(
    'directive-ceilings', DirectiveCeilingViewSet,
    basename='v2-directive-ceilings',
)
budget_router.register('resources', CeilingResourceViewSet, basename='v2-budget-resources')
budget_router.register(
    'mandatory-expenses', MandatoryExpenseViewSet,
    basename='v2-mandatory-expenses',
)
budget_router.register('documents', BudgetDocumentViewSet, basename='v2-budget-documents')
budget_router.register(
    'programmatic-categories', ProgrammaticCategoryViewSet,
    basename='v2-programmatic-categories',
)
budget_router.register(
    'distributions', DistributionVersionViewSet,
    basename='v2-budget-distributions',
)
budget_router.register('allocations', AllocationViewSet, basename='v2-budget-allocations')
budget_router.register(
    'expense-objects', ExpenseObjectViewSet, basename='v2-expense-objects',
)
budget_router.register('reserves', ReserveViewSet, basename='v2-budget-reserves')
budget_router.register('imports', BudgetImportViewSet, basename='v2-budget-imports')
budget_router.register(
    'territorial-distributions', TerritorialDistributionViewSet,
    basename='v2-territorial-distributions',
)
budget_router.register('reforms', ReformViewSet, basename='v2-budget-reforms')

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
    *budget_router.urls,
]
