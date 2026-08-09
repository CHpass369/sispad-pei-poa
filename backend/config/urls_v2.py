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

platform_router = DefaultRouter()
sis_pe_router = DefaultRouter()
sis_poa_router = DefaultRouter()
sis_pro_router = DefaultRouter()

me_router = DefaultRouter()
me_router.register('me', MeViewSet, basename='v2-me')

urlpatterns = [
    path('platform/', include(platform_router.urls)),
    path('sis-pe/', include(sis_pe_router.urls)),
    path('sis-poa/', include(sis_poa_router.urls)),
    path('sis-pro/', include(sis_pro_router.urls)),
    path('', include(me_router.urls)),
]
