import django_filters
from .models import Rol, Usuario


class RolFilter(django_filters.FilterSet):
    class Meta:
        model = Rol
        fields = {
            'codigo': ['exact'],
            'nombre': ['exact', 'icontains'],
            'activo': ['exact'],
            'es_sistema': ['exact'],
        }


class UsuarioFilter(django_filters.FilterSet):
    class Meta:
        model = Usuario
        fields = {
            'email': ['exact', 'icontains'],
            'first_name': ['icontains'],
            'last_name': ['icontains'],
            'cargo': ['icontains'],
            'activo': ['exact'],
            'is_staff': ['exact'],
            'roles': ['exact'],
        }
