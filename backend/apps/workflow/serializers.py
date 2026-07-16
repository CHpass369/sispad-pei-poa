from rest_framework import serializers
from .models import EnvioFormulacion, Revision, Observacion, Aprobacion


class EnvioFormulacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnvioFormulacion
        fields = '__all__'
        read_only_fields = ['fecha_envio']


class RevisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Revision
        fields = '__all__'
        read_only_fields = ['fecha_asignacion']


class ObservacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Observacion
        fields = '__all__'


class AprobacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Aprobacion
        fields = '__all__'
