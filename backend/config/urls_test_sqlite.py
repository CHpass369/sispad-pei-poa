"""Urlconf mínimo para settings_test_sqlite (solo auth/accounts)."""
from django.urls import path, include

api_prefix = 'api/v1/'

urlpatterns = [
    path(f'{api_prefix}auth/', include('apps.accounts.urls')),
]
