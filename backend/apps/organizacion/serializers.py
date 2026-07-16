from rest_framework import serializers
from .models import TipoUnidad, UnidadOrganizacional, DireccionAdministrativa, UnidadEjecutora, AsignacionUsuarioUnidad


class TipoUnidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoUnidad
        fields = '__all__'


class UnidadOrganizacionalSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnidadOrganizacional
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']


class UnidadOrganizacionalTreeSerializer(serializers.ModelSerializer):
    hijas = serializers.SerializerMethodField()

    class Meta:
        model = UnidadOrganizacional
        fields = ['id', 'codigo', 'nombre', 'sigla', 'tipo', 'tipo_id', 'hijas', 'gestion', 'activo']

    def get_hijas(self, obj):
        hijas = obj.hijas.filter(activo=True)
        return UnidadOrganizacionalTreeSerializer(hijas, many=True).data


class DireccionAdministrativaSerializer(serializers.ModelSerializer):
    class Meta:
        model = DireccionAdministrativa
        fields = '__all__'


class UnidadEjecutoraSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnidadEjecutora
        fields = '__all__'


class AsignacionUsuarioUnidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = AsignacionUsuarioUnidad
        fields = '__all__'
