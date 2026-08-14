"""Rutas de la API V2 del ciclo presupuestario SIS-POA (apps.budget).

Namespace montado en `config/urls_v2.py` como `/api/v2/sis-poa/budget/`.
"""
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    BudgetDocumentViewSet,
    CatalogOptionsView,
    CeilingResourceViewSet,
    CompositionView,
    DirectiveCeilingViewSet,
    FiscalYearViewSet,
    MandatoryExpenseViewSet,
    ProgrammaticCategoryViewSet,
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

urlpatterns = [
    path(
        'directive-ceilings/<int:pk>/composition/',
        CompositionView.as_view(),
        name='v2-directive-ceiling-composition',
    ),
    path('catalogs/', CatalogOptionsView.as_view(), name='v2-budget-catalogs'),
    *budget_router.urls,
]
