"""Rutas de la API V2 del ciclo presupuestario SIS-POA (apps.budget)."""
from rest_framework.routers import DefaultRouter

from .views import FiscalYearViewSet

budget_router = DefaultRouter()
budget_router.register('fiscal-years', FiscalYearViewSet, basename='v2-fiscal-years')

urlpatterns = budget_router.urls
