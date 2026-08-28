from rest_framework import serializers
from .models import TipoUnidad, UnidadOrganizacional, DireccionAdministrativa, UnidadEjecutora, AsignacionUsuarioUnidad
from .services import FORMULATOR_ROLE_CODE


class TipoUnidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoUnidad
        fields = '__all__'


class UnidadOrganizacionalSerializer(serializers.ModelSerializer):
    gestion_anio = serializers.IntegerField(source='gestion.anio', read_only=True)

    class Meta:
        model = UnidadOrganizacional
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']


class UnidadOrganizacionalTreeSerializer(serializers.ModelSerializer):
    hijas = serializers.SerializerMethodField()
    gestion_anio = serializers.IntegerField(source='gestion.anio', read_only=True)

    class Meta:
        model = UnidadOrganizacional
        fields = ['id', 'codigo', 'nombre', 'sigla', 'tipo', 'tipo_id', 'hijas', 'gestion', 'gestion_anio', 'activo']

    def get_hijas(self, obj):
        hijas = obj.hijas.filter(activo=True)
        return UnidadOrganizacionalTreeSerializer(hijas, many=True).data


class DireccionAdministrativaSerializer(serializers.ModelSerializer):
    gestion_anio = serializers.IntegerField(source='gestion.anio', read_only=True)

    class Meta:
        model = DireccionAdministrativa
        fields = '__all__'


class UnidadEjecutoraSerializer(serializers.ModelSerializer):
    gestion_anio = serializers.IntegerField(source='gestion.anio', read_only=True)

    class Meta:
        model = UnidadEjecutora
        fields = '__all__'


class AsignacionUsuarioUnidadSerializer(serializers.ModelSerializer):
    gestion_anio = serializers.IntegerField(source='gestion.anio', read_only=True)

    class Meta:
        model = AsignacionUsuarioUnidad
        fields = '__all__'

    def validate(self, attrs):
        instance = self.instance
        usuario = attrs.get('usuario', getattr(instance, 'usuario', None))
        unidad = attrs.get('unidad', getattr(instance, 'unidad', None))
        gestion = attrs.get('gestion', getattr(instance, 'gestion', None))
        activo = attrs.get('activo', getattr(instance, 'activo', True))
        if not usuario or not gestion or not usuario.roles.filter(
            codigo=FORMULATOR_ROLE_CODE, activo=True,
        ).exists():
            return attrs
        if unidad.gestion_id != gestion.pk:
            raise serializers.ValidationError(
                'The organizational unit must belong to the fiscal year.'
            )
        duplicates = AsignacionUsuarioUnidad.objects.filter(
            usuario=usuario, gestion=gestion, activo=True,
        )
        if instance is not None:
            duplicates = duplicates.exclude(pk=instance.pk)
        if activo and duplicates.exists():
            raise serializers.ValidationError(
                'A POAU formulator can have only one organizational unit '
                'per fiscal year.'
            )
        return attrs
