from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.gestion.models import GestionFiscal
from apps.organizacion.models import UnidadOrganizacional

from .models import AlcanceOrganizacional, Usuario, Rol


class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = ['id', 'codigo', 'nombre', 'descripcion', 'activo']


class UsuarioSerializer(serializers.ModelSerializer):
    roles_detalle = RolSerializer(source='roles', many=True, read_only=True)

    class Meta:
        model = Usuario
        fields = [
            'id', 'email', 'first_name', 'last_name', 'cargo', 'telefono',
            'roles', 'roles_detalle', 'estado', 'activo', 'is_staff', 'is_superuser',
            'debe_cambiar_password', 'last_login', 'date_joined',
        ]
        read_only_fields = ['estado', 'is_superuser', 'last_login', 'date_joined']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        roles = validated_data.pop('roles', [])
        user = Usuario.objects.create_user(**validated_data)
        user.roles.set(roles)
        return user

    def update(self, instance, validated_data):
        roles = validated_data.pop('roles', None)
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        if roles is not None:
            instance.roles.set(roles)
        return instance


# --- F3a: registro público y aprobación administrativa ----------------------
#
# Contrato del registro (#17): el solicitante solo elige datos personales,
# cargo, UO y contraseña. NUNCA rol, capacidades, sistema ni scope: esos los
# define el administrador al aprobar (#18). Por eso estos serializers son
# separados de UsuarioSerializer (que expone roles/is_staff).


class RegistroPublicoSerializer(serializers.Serializer):
    """Alta pública de usuario: queda PENDIENTE hasta aprobación admin."""

    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    cargo = serializers.CharField(max_length=200, required=False, allow_blank=True)
    unidad_organizacional_id = serializers.UUIDField()
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    def validate_email(self, value):
        value = Usuario.objects.normalize_email(value)
        if Usuario.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                'Ya existe una cuenta registrada con este correo.'
            )
        return value

    def validate_unidad_organizacional_id(self, value):
        if not UnidadOrganizacional.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                'La unidad organizacional no existe.'
            )
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': ['Las contraseñas no coinciden.'],
            })
        try:
            candidato = Usuario(
                email=attrs['email'],
                first_name=attrs['first_name'],
                last_name=attrs['last_name'],
            )
            validate_password(attrs['password'], user=candidato)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'password': exc.messages})
        return attrs


class AprobacionSerializer(serializers.Serializer):
    """Datos que el administrador define al aprobar una solicitud (#18)."""

    unidad_organizacional_id = serializers.UUIDField()
    rol_codigo = serializers.CharField(max_length=50)
    sistema = serializers.ChoiceField(choices=['sis_pe', 'sis_poa'])
    scope_type = serializers.ChoiceField(
        choices=AlcanceOrganizacional.SCOPE_TYPE_CHOICES,
    )
    fiscal_year_id = serializers.UUIDField(required=False, allow_null=True)

    def validate_unidad_organizacional_id(self, value):
        if not UnidadOrganizacional.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                'La unidad organizacional no existe.'
            )
        return value

    def validate_fiscal_year_id(self, value):
        if value is not None and not GestionFiscal.objects.filter(id=value).exists():
            raise serializers.ValidationError('La gestión fiscal no existe.')
        return value


class SolicitudSerializer(serializers.ModelSerializer):
    """Fila del listado de solicitudes PENDIENTE (sin datos sensibles)."""

    unidad_solicitada = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = [
            'id', 'email', 'first_name', 'last_name', 'cargo',
            'date_joined', 'unidad_solicitada',
        ]

    def get_unidad_solicitada(self, obj):
        """UO pedida en el registro (alcance-trazo rol=None, activo=False)."""
        alcance = next(
            (a for a in obj.alcances_organizacionales.all() if a.rol_id is None),
            None,
        )
        if alcance is None:
            return None
        return {'id': str(alcance.unidad_id), 'nombre': alcance.unidad.nombre}
